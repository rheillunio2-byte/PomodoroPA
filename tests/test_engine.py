"""Pure-Python engines: no Tk, no display needed."""
from __future__ import annotations

import unittest

from tests import helpers  # noqa: F401  (puts the project root on sys.path)
from ui.engine import icons, palette
from ui.engine.colors import hex_to_rgb, luminance, mix, parse_color, readable_text
from ui.engine.dock_engine import DockEngine, DockItem
from ui.engine.dock_render import render_dock, tokens
from ui.engine.motion import Spring, cubic_bezier
from ui.engine.ring_render import render_ring
from ui.engine.text_engine import RotatingTextEngine, Track, effect_poses


def contrast(a: str, b: str) -> float:
    la, lb = luminance(hex_to_rgb(a)), luminance(hex_to_rgb(b))
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


class PaletteTests(unittest.TestCase):

    def test_text_colours_are_readable_wcag_aa(self):
        for mode, p in palette.PALETTES.items():
            for fg, bg in [("text", "bg"), ("text", "surface"), ("muted", "surface"), ("muted", "surface2"),
                           ("faint", "surface2"), ("on_tomato", "tomato"), ("tomato", "surface"),
                           ("leaf", "surface"), ("sun", "surface"), ("sky", "surface"),
                           ("plum", "surface"), ("danger", "surface")]:
                self.assertGreaterEqual(contrast(p[fg], p[bg]), 4.5, f"{mode}: {fg} on {bg}")

    def test_tinted_pills_are_readable(self):
        for mode, p in palette.PALETTES.items():
            for token in ("muted", "danger", "sun", "plum", "leaf", "sky", "tomato"):
                self.assertGreaterEqual(contrast(p[token], mix(p["surface"], p[token], 0.16)), 4.4, f"{mode}: {token}")


class ColorTests(unittest.TestCase):

    def test_parse_mix_and_readable_text(self):
        self.assertEqual(parse_color("#fff"), (255, 255, 255))
        self.assertEqual(parse_color("rgba(10, 20, 30, 0.5)"), (10, 20, 30))
        self.assertIsNone(parse_color("tomato"))
        self.assertEqual(mix("#000000", "#ffffff", 0.5), "#808080")
        self.assertEqual(readable_text("#ffffff"), "#0b0b0c")       # light block -> dark text
        self.assertEqual(readable_text("#a855f7"), "#ffffff")       # the component's default purple
        self.assertIsNone(readable_text("not a colour"))


class MotionTests(unittest.TestCase):

    def test_bezier_endpoints_monotonic_and_overshoot(self):
        ease = cubic_bezier(0.22, 1, 0.36, 1)
        self.assertEqual((ease(0), ease(1)), (0.0, 1.0))
        values = [ease(i / 50) for i in range(51)]
        self.assertEqual(values, sorted(values))
        overshoot = cubic_bezier(0.34, 1.4, 0.64, 1)                  # the flip effect's curve
        self.assertGreater(max(overshoot(i / 100) for i in range(101)), 1.0)
        self.assertAlmostEqual(cubic_bezier(0, 0, 1, 1)(0.3), 0.3, places=3)

    def test_spring_settles_and_underdamped_overshoots(self):
        spring = Spring(0, 1, stiffness=300, damping=25)
        peak = 0
        for _ in range(300):
            peak = max(peak, spring.step(1 / 60))
        self.assertTrue(spring.settled)
        self.assertEqual(spring.value, 1.0)
        bouncy = Spring(0, 1, stiffness=150, damping=4)
        self.assertGreater(max(bouncy.step(1 / 60) for _ in range(120)), 1.05)


class IconTests(unittest.TestCase):

    def test_every_icon_renders_with_ink_and_transparency(self):
        for name in icons.available():
            img = icons.render_icon(name, 32, "#ffffff")
            self.assertEqual(img.size, (32, 32))
            alpha = img.getchannel("A")
            lo, hi = alpha.getextrema()
            self.assertEqual(lo, 0, name)
            self.assertGreater(hi, 200, name)

    def test_unknown_icon_raises(self):
        with self.assertRaises(KeyError):
            icons.render_icon("nope", 16)


def make_dock(**kw):
    items = [DockItem(key=str(i), icon="home", label=f"Item {i}") for i in range(3)]
    items.insert(2, DockItem(separator=True))
    engine = DockEngine(items, base=48, magnification=70, distance=200, panel_height=64, gap=10, **kw)
    engine.center_x = 400
    return engine


class DockEngineTests(unittest.TestCase):

    def settle(self, engine, seconds=2.0):
        for _ in range(int(seconds * 60)):
            engine.step(1 / 60)

    def test_magnification_peaks_under_pointer_and_falls_off(self):
        e = make_dock()
        centre = e.rest_centres()[0] + 400
        e.pointer_x = centre
        self.settle(e)
        sizes = e.sizes()
        self.assertAlmostEqual(sizes[0], 70, delta=0.5)
        self.assertLess(sizes[1], sizes[0])
        self.assertLess(sizes[3], sizes[1])                    # growth falls off with distance
        self.assertGreater(sizes[3], 48)                       # but is still inside `distance`
        far = make_dock(); far.pointer_x = 400 + far.rest_centres()[0] - 500; far.step(1 / 60)
        for _ in range(200):
            far.step(1 / 60)
        self.assertAlmostEqual(far.sizes()[3], 48, delta=0.01)  # pointer far away -> base size
        e.pointer_x = None
        self.settle(e)
        self.assertAlmostEqual(e.sizes()[0], 48, delta=0.05)

    def test_panel_width_grows_and_stays_centred(self):
        e = make_dock()
        self.settle(e, 0.1)
        rest = e.panel_width()
        e.pointer_x = 400
        self.settle(e)
        self.assertGreater(e.panel_width(), rest + 10)
        boxes = e.boxes(100)
        left, right = boxes[0].left - e.pad, boxes[-1].right + e.pad
        self.assertAlmostEqual((left + right) / 2, 400, delta=0.5)

    def test_hop_bounces_and_lands(self):
        e = make_dock()
        self.settle(e, 0.1)
        e.hop(0)
        lifts = []
        for _ in range(90):
            e.step(1 / 60)
            lifts.append(e._motion[0].lift)
        self.assertGreater(max(lifts), 48 * 0.3)
        self.assertEqual(lifts[-1], 0.0)
        self.assertFalse(e._motion[0].hopping)

    def test_animation_off_snaps_and_never_hops(self):
        e = make_dock(animate=False)
        e.pointer_x = 400
        e.step(1 / 60)
        self.assertEqual(e.sizes()[0], 48)
        e.hop(0)
        self.assertFalse(e._motion[0].hopping)

    def test_fits_a_narrow_window_and_hit_testing_skips_separators(self):
        e = make_dock()
        e.set_available_width(200)
        self.assertLess(e.fit, 1.0)
        self.assertGreaterEqual(e.fit, 0.4)
        e.set_available_width(2000)
        self.assertEqual(e.fit, 1.0)
        self.settle(e, 0.1)
        boxes = e.boxes(100)
        self.assertEqual(e.hit_test(boxes[0].center_x, 100), 0)
        self.assertIsNone(e.hit_test(-50, 100))
        self.assertEqual(e.nearest_focusable(1, 1), 3)         # skips the separator at index 2

    def test_render_produces_an_image_in_both_themes_and_labels_change_pixels(self):
        for mode in ("dark", "light"):
            e = make_dock()
            e.items[0].badge, e.items[1].badge, e.items[1].active = 7, True, True
            e.pointer_x = 400
            self.settle(e)
            tk = tokens(palette.PALETTES[mode])
            plain = render_dock(e, tk, (800, 140), 120)
            labelled = render_dock(e, tk, (800, 140), 120, hover=0, label_alpha=1.0)
            self.assertEqual(plain.size, (800, 140))
            self.assertNotEqual(plain.tobytes(), labelled.tobytes())
            self.assertEqual(plain.getpixel((2, 2)), hex_to_rgb(palette.PALETTES[mode]["bg"]))


class RotatingTextEngineTests(unittest.TestCase):

    def run_for(self, engine, seconds):
        for _ in range(int(seconds * 60)):
            engine.update(1 / 60)

    def test_wait_mode_exits_then_enters_and_notifies(self):
        seen = []
        e = RotatingTextEngine(["One", "Three"], auto=False, stagger_duration=0.02, on_next=seen.append,
                               font_px=24, bg="#000000")
        self.assertEqual([l.text for l in e.layers], ["One"])
        e.next()
        e.update(1 / 60)
        self.assertEqual([l.phase for l in e.layers], ["exit"])          # old text leaves first
        self.run_for(e, 1.5)
        self.assertEqual([(l.text, l.phase) for l in e.layers], [("Three", "rest")])
        self.assertEqual(seen, [1])
        self.assertTrue(e.idle_ok())

    def test_sync_mode_overlaps_old_and_new(self):
        e = RotatingTextEngine(["One", "Three"], auto=False, animate_presence_mode="sync", font_px=24)
        e.next()
        self.assertEqual(sorted(l.phase for l in e.layers), ["enter", "exit"])

    def test_auto_rotation_interval_loop_and_pause(self):
        e = RotatingTextEngine(["a", "b", "c"], rotation_interval=500, font_px=20)
        self.run_for(e, 0.6)
        self.assertEqual(e.index, 1)
        e.paused = True
        self.run_for(e, 2.0)
        self.assertEqual(e.index, 1)                                     # hover pauses
        e.paused = False
        self.run_for(e, 1.2)
        self.assertEqual(e.index, 0)                                     # wrapped (loop=True)
        e2 = RotatingTextEngine(["a", "b"], rotation_interval=300, loop=False, font_px=20)
        self.run_for(e2, 2.0)
        self.assertEqual(e2.index, 1)                                    # stops at the end

    def test_previous_jump_reset(self):
        e = RotatingTextEngine(["a", "b", "c"], auto=False, font_px=20)
        e.previous()
        self.assertEqual(e.index, 2)
        e.jump_to(1)
        self.assertEqual(e.index, 1)
        e.reset()
        self.assertEqual(e.index, 0)

    def test_stagger_origins(self):
        def delays(origin):
            e = RotatingTextEngine(["abcde"], stagger_duration=0.1, stagger_from=origin, auto=False,
                                   animate_presence_initial=True, font_px=20)
            return [round(el.track.delay, 2) for el in e.layers[0].elements]
        self.assertEqual(delays("first"), [0, 0.1, 0.2, 0.3, 0.4])
        self.assertEqual(delays("last"), [0.4, 0.3, 0.2, 0.1, 0])
        self.assertEqual(delays("center"), [0.2, 0.1, 0, 0.1, 0.2])
        self.assertEqual(delays(1), [0.1, 0, 0.1, 0.2, 0.3])
        self.assertEqual(sorted(delays("random")), [0, 0.1, 0.2, 0.3, 0.4])

    def test_split_by_words_lines_and_custom(self):
        def parts(split, text):
            e = RotatingTextEngine([text], split_by=split, auto=False, font_px=20)
            return [el.text for el in e.layers[0].elements]
        self.assertEqual(parts("words", "hello big world"), ["hello", "big", "world"])
        self.assertEqual(parts("lines", "a\nb"), ["a", "b"])
        self.assertEqual(parts("|", "x|y|z"), ["x", "y", "z"])
        self.assertEqual(parts("characters", "hi yo"), ["h", "i", "y", "o"])

    def test_effect_poses_match_the_component(self):
        self.assertEqual(effect_poses("slide", True)["initial"]["y"], 1.0)
        self.assertEqual(effect_poses("slide", False)["initial"]["y"], -1.0)
        self.assertEqual(effect_poses("flip", True)["initial"]["rotateX"], -90)
        self.assertEqual(effect_poses("scale", True)["initial"]["scale"], 0.35)
        self.assertEqual(effect_poses("drop", False)["initial"]["y"], -1.1)      # drop always falls from above
        self.assertEqual(effect_poses("blur", True)["transition"]["duration"], 0.55)

    def test_highlight_resizes_and_picks_contrast_colour(self):
        e = RotatingTextEngine(["Hi", "Considerably longer"], auto=False, highlight=True,
                               highlight_color="#FFFFFF", font_px=24)
        self.assertEqual(e.fg, "#0b0b0c")
        before = e.size()[0]
        e.next()
        self.run_for(e, 2.0)
        self.assertGreater(e.size()[0], before + 60)

    def test_every_effect_renders_frames_without_error(self):
        for effect in ("slide", "flip", "blur", "scale", "drop"):
            for direction in ("up", "down"):
                e = RotatingTextEngine(["Focus", "Flow"], effect=effect, direction=direction, auto=False,
                                       stagger_duration=0.02, font_px=26, text_color="#ffffff", bg="#101010",
                                       highlight=(effect == "slide"))
                e.next()
                seen = set()
                for _ in range(70):
                    e.update(1 / 60)
                    frame = e.render()
                    seen.add(frame.tobytes())
                self.assertGreater(len(seen), 5, effect)                 # it actually animates

    def test_animations_off_swaps_instantly(self):
        e = RotatingTextEngine(["a", "b"], auto=False, animate=False, font_px=20)
        e.next()
        self.assertEqual([(l.text, l.phase) for l in e.layers], [("b", "rest")])

    def test_track_tween_respects_delay_and_duration(self):
        track = Track({"type": "tween", "duration": 0.5, "ease": None}, delay=0.2)
        track.update(0.1)
        self.assertEqual(track.value, 0.0)
        for _ in range(60):
            track.update(1 / 60)
        self.assertTrue(track.done)
        self.assertAlmostEqual(track.value, 1.0)


class RingTests(unittest.TestCase):

    def test_ring_renders_progress_and_glow(self):
        kw = dict(thickness=14, c1="#FF8A4C", c2="#FF4B3E", track="#22302A", bg="#0C1310")
        empty = render_ring(160, 0.0, **kw)
        half = render_ring(160, 0.5, **kw)
        full = render_ring(160, 1.0, **kw)
        glowing = render_ring(160, 0.5, glow=1.0, **kw)
        self.assertEqual(empty.size, (160, 160))
        self.assertEqual(len({empty.tobytes(), half.tobytes(), full.tobytes(), glowing.tobytes()}), 4)
        # at 25% the arc covers the 3 o'clock position but not 9 o'clock
        quarter = render_ring(160, 0.25, **kw)
        right, left = quarter.getpixel((160 - 14, 80)), quarter.getpixel((14, 80))
        self.assertNotEqual(right, left)


if __name__ == "__main__":
    unittest.main()
