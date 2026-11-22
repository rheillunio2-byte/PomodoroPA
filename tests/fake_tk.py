"""A minimal in-memory stand-in for tkinter / customtkinter / PIL.ImageTk.

It lets the test-suite construct every page, fire events and run the
animation loops on a machine with no display (CI, containers).  It is NOT a
rendering engine: it only records what the UI asked for.  Unknown methods
raise ``AttributeError`` on purpose, so typos in UI code are caught.
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace

CLOCK = {"now": 1000.0}
_pending: list = []          # [due, id, fn, args]
_next_id = [1]


def pump(seconds: float, step: float = 0.016) -> None:
    """Advance fake time, running every ``after`` callback that comes due."""
    end = CLOCK["now"] + seconds
    while CLOCK["now"] < end:
        CLOCK["now"] += step
        due = [p for p in _pending if p[0] <= CLOCK["now"]]
        for p in due:
            if p in _pending:
                _pending.remove(p)
                p[2](*p[3])


class TclError(Exception):
    pass


class Misc:
    def __init__(self, master=None, **kw):
        if hasattr(self, "_check"):
            self._check(kw)
        self.master = master
        self._cfg = dict(kw)
        self.children: list = []
        self._bindings: dict = {}
        self._destroyed = False
        if master is not None and hasattr(master, "children"):
            master.children.append(self)

    # configuration
    def configure(self, **kw):
        if hasattr(self, "_check"):
            self._check(kw)
        self._cfg.update(kw)

    config = configure

    def cget(self, key):
        return self._cfg.get(key, "")

    # geometry managers (no-ops, recorded)
    def _geo(self, kind, **kw):
        self._geo_info = (kind, kw)

    def pack(self, **kw): self._geo("pack", **kw)
    def grid(self, **kw): self._geo("grid", **kw)
    def place(self, **kw): self._geo("place", **kw)
    def pack_forget(self): self._geo_info = None
    def grid_forget(self): self._geo_info = None
    def place_forget(self): self._geo_info = None
    def place_configure(self, **kw): self._geo("place", **kw)
    def pack_configure(self, **kw): self._geo("pack", **kw)
    def pack_propagate(self, flag=True): pass
    def grid_propagate(self, flag=True): pass
    def grid_columnconfigure(self, *a, **k): pass
    def grid_rowconfigure(self, *a, **k): pass
    def lift(self, *a): pass
    def lower(self, *a): pass

    # info
    def winfo_children(self): return list(self.children)
    def winfo_width(self): return self._cfg.get("width") if isinstance(self._cfg.get("width"), int) and self._cfg.get("width") > 1 else 900
    def winfo_height(self): return self._cfg.get("height") if isinstance(self._cfg.get("height"), int) and self._cfg.get("height") > 1 else 300
    def winfo_reqwidth(self): return 200
    def winfo_reqheight(self): return 40
    def winfo_fpixels(self, s): return 96.0
    def winfo_ismapped(self): return True
    def winfo_exists(self): return not self._destroyed
    def winfo_rootx(self): return 0
    def winfo_rooty(self): return 0
    def winfo_pointerxy(self): return POINTER["xy"]
    def winfo_containing(self, x, y): return POINTER["widget"]
    def winfo_toplevel(self): return self
    def winfo_id(self): return 1234

    # scheduling
    def after(self, ms, fn=None, *args):
        i = _next_id[0]; _next_id[0] += 1
        if fn is not None:
            _pending.append([CLOCK["now"] + ms / 1000.0, i, fn, args])
        return i

    def after_cancel(self, i):
        for p in list(_pending):
            if p[1] == i:
                _pending.remove(p)

    # events
    def bind(self, seq, fn=None, add=None):
        self._bindings.setdefault(seq, []).append(fn)
        return f"{seq}#{len(self._bindings[seq])}"

    def unbind(self, seq, funcid=None): self._bindings.pop(seq, None)
    bind_all = bind
    def focus_set(self): pass
    def focus_force(self): pass
    def focus_get(self): return FOCUS["widget"]
    def update_idletasks(self): pass
    def update(self): pass
    def tk_popup(self, *a): pass
    def grab_release(self): pass
    def grab_set(self): pass

    def fire(self, seq, **event):
        ev = SimpleNamespace(widget=self, x=0, y=0, x_root=0, y_root=0, width=900, height=300, keysym="", detail=0, **event)
        for fn in self._bindings.get(seq, []):
            fn(ev)

    def destroy(self):
        for child in list(self.children):
            child.destroy()
        self._destroyed = True
        if self.master is not None and self in getattr(self.master, "children", []):
            self.master.children.remove(self)
        self.fire("<Destroy>")


POINTER = {"xy": (0, 0), "widget": None}
FOCUS = {"widget": None}


class Tk(Misc):
    def title(self, text=None):
        if text is not None:
            self._title = text
        return getattr(self, "_title", "")
    def geometry(self, spec=None): self._geom = spec
    def minsize(self, *a): pass
    def resizable(self, *a): pass
    def protocol(self, *a): pass
    def iconphoto(self, *a): pass
    def attributes(self, *a): pass
    def overrideredirect(self, flag): pass
    def transient(self, other=None): pass
    def withdraw(self): pass
    def deiconify(self): pass
    def mainloop(self): pass
    def mainloop_stub(self): pass


class Toplevel(Tk):
    pass


class Canvas(Misc):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.items: dict[int, dict] = {}
        self._n = 0

    def _new(self, kind, coords, kw):
        self._n += 1
        self.items[self._n] = {"kind": kind, "coords": list(coords), **kw}
        return self._n

    def create_line(self, *c, **kw): return self._new("line", c, kw)
    def create_oval(self, *c, **kw): return self._new("oval", c, kw)
    def create_rectangle(self, *c, **kw): return self._new("rect", c, kw)
    def create_polygon(self, *c, **kw): return self._new("poly", c[0] if len(c) == 1 and isinstance(c[0], (list, tuple)) else c, kw)
    def create_arc(self, *c, **kw): return self._new("arc", c, kw)
    def create_text(self, x, y, **kw): return self._new("text", (x, y), kw)
    def create_image(self, x, y, **kw): return self._new("image", (x, y), kw)
    def coords(self, item, *c): self.items[item]["coords"] = list(c)
    def itemconfigure(self, item, **kw): self.items[item].update(kw)
    itemconfig = itemconfigure
    def delete(self, item):
        if item == "all": self.items.clear()
        else: self.items.pop(item, None)
    def tag_raise(self, *a): pass
    def tag_lower(self, *a): pass
    def bbox(self, item): return (0, 0, 60, 14)
    def find_all(self): return list(self.items)


class Entry(Misc):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._text = ""
    def get(self): return self._text
    def insert(self, i, text): self._text += text
    def delete(self, a, b=None): self._text = ""


class Text(Entry):
    pass


class Menu(Misc):
    def add_command(self, **kw): pass
    def add_separator(self): pass


class PhotoImage:
    def __init__(self, image=None, **kw):
        self.image = image
    def width(self): return self.image.width
    def height(self): return self.image.height
    def paste(self, im): self.image = im


# --------------------------------------------------------------- customtkinter

# Keyword arguments accepted by the real CustomTkinter 5.2 constructors.  Real CTk
# widgets raise ValueError for anything else, so the fake does too.
_COMMON = {"width", "height", "bg_color", "fg_color", "corner_radius"}
ALLOWED = {
    "CTkFrame": _COMMON | {"border_width", "border_color", "background_corner_colors"},
    "CTkLabel": _COMMON | {"text_color", "text_color_disabled", "text", "font", "image", "compound", "anchor", "wraplength"},
    "CTkButton": _COMMON | {"border_width", "border_spacing", "hover_color", "border_color", "text_color",
                            "text_color_disabled", "text", "font", "textvariable", "image", "state", "hover",
                            "command", "compound", "anchor"},
    "CTkEntry": _COMMON | {"border_width", "border_color", "text_color", "placeholder_text_color", "textvariable",
                           "placeholder_text", "font", "state"},
    "CTkSegmentedButton": _COMMON | {"border_width", "selected_color", "selected_hover_color", "unselected_color",
                                     "unselected_hover_color", "text_color", "text_color_disabled", "font", "values",
                                     "variable", "dynamic_resizing", "command", "state"},
    "CTkOptionMenu": _COMMON | {"button_color", "button_hover_color", "text_color", "text_color_disabled",
                                "dropdown_fg_color", "dropdown_hover_color", "dropdown_text_color", "font",
                                "dropdown_font", "values", "variable", "state", "hover", "command",
                                "dynamic_resizing", "anchor"},
    "CTkSwitch": _COMMON | {"switch_width", "switch_height", "border_width", "button_length", "border_color",
                            "progress_color", "button_color", "button_hover_color", "text_color",
                            "text_color_disabled", "text", "font", "textvariable", "onvalue", "offvalue",
                            "variable", "hover", "command", "state"},
    "CTkProgressBar": _COMMON | {"border_width", "border_color", "progress_color", "variable", "orientation",
                                 "mode", "determinate_speed", "indeterminate_speed"},
    "CTkScrollableFrame": _COMMON | {"border_width", "border_color", "scrollbar_fg_color", "scrollbar_button_color",
                                     "scrollbar_button_hover_color", "label_fg_color", "label_text_color",
                                     "label_text", "label_font", "label_anchor", "orientation"},
    "CTkToplevel": {"fg_color"},
    "CTk": {"fg_color"},
}


class Strict:
    """Mixin: reject keyword arguments the real widget would reject."""

    def _check(self, kw):
        allowed = ALLOWED.get(type(self).__name__)
        if allowed is not None:
            unknown = set(kw) - allowed
            if unknown:
                raise ValueError(f"{type(self).__name__}: unknown keyword arguments {sorted(unknown)}")

class CTkFrame(Strict, Misc): pass
class CTkScrollableFrame(Strict, Misc): pass
class CTkToplevel(Strict, Tk): pass


class CTk(Strict, Tk):
    pass


class CTkLabel(Strict, Misc): pass


class CTkButton(Strict, Misc):
    def __init__(self, master=None, command=None, **kw):
        super().__init__(master, **kw)
        self.command = command
    def configure(self, **kw):
        if "command" in kw: self.command = kw.pop("command")
        super().configure(**kw)
    def invoke(self):
        if self.command: self.command()


class CTkEntry(Strict, Entry):
    pass


class CTkTextbox(Entry):
    pass


class CTkSegmentedButton(Strict, Misc):
    def __init__(self, master=None, command=None, values=(), **kw):
        super().__init__(master, values=values, **kw)
        self.command, self.value = command, (values[0] if values else "")
    def get(self): return self.value
    def set(self, v): self.value = v


class CTkOptionMenu(CTkSegmentedButton):
    def __init__(self, master=None, command=None, values=(), **kw):
        super().__init__(master, command, values, **kw)


class CTkSwitch(Strict, Misc):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.on = 0
    def select(self): self.on = 1
    def deselect(self): self.on = 0
    def get(self): return self.on
    def toggle_to(self, v):
        self.on = v
        self._cfg["command"]()


class CTkProgressBar(Strict, Misc):
    def set(self, v): self.value = v


class CTkImage:
    def __init__(self, light_image=None, dark_image=None, size=(20, 20)):
        self.light_image, self.dark_image, self.size = light_image, dark_image, size


class CTkFont:
    def __init__(self, family=None, size=12, weight="normal", **kw):
        self.family, self.size, self.weight, self.kw = family, size, weight, kw


_MODE = {"mode": "Dark"}


def install() -> types.ModuleType:
    """Register the fakes in ``sys.modules`` (idempotent).  Returns the fake tkinter."""
    tk = types.ModuleType("tkinter")
    for cls in (Tk, Toplevel, Canvas, Entry, Text, Menu, PhotoImage, Misc, TclError):
        setattr(tk, cls.__name__, cls)
    tk._default_root = None
    tk.Frame = Misc
    font = types.ModuleType("tkinter.font")
    font.families = lambda root=None: ["Segoe UI", "Bahnschrift"]
    messagebox = types.ModuleType("tkinter.messagebox")
    messagebox.askyesno = lambda *a, **k: True
    messagebox.showerror = messagebox.showinfo = lambda *a, **k: None
    filedialog = types.ModuleType("tkinter.filedialog")
    filedialog.asksaveasfilename = lambda **k: FILE["path"]
    tk.font, tk.messagebox, tk.filedialog = font, messagebox, filedialog

    ctk = types.ModuleType("customtkinter")
    for cls in (CTk, CTkFrame, CTkScrollableFrame, CTkToplevel, CTkLabel, CTkButton, CTkEntry, CTkTextbox,
                CTkSegmentedButton, CTkOptionMenu, CTkSwitch, CTkProgressBar, CTkImage, CTkFont):
        setattr(ctk, cls.__name__, cls)
    ctk.set_appearance_mode = lambda m: _MODE.update(mode=m if m != "System" else "Dark")
    ctk.get_appearance_mode = lambda: _MODE["mode"]

    imagetk = types.ModuleType("PIL.ImageTk")
    imagetk.PhotoImage = PhotoImage

    sys.modules.update({"tkinter": tk, "tkinter.font": font, "tkinter.messagebox": messagebox,
                        "tkinter.filedialog": filedialog, "customtkinter": ctk, "PIL.ImageTk": imagetk})
    import PIL
    PIL.ImageTk = imagetk                      # type: ignore[attr-defined]
    return tk


FILE = {"path": ""}
