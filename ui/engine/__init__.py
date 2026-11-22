"""Pure-Python rendering and physics.

Nothing in this package imports Tk.  The Dock, RotatingText and progress ring
are computed here (Pillow frames + spring physics) and the widgets in
``ui/widgets`` simply blit the resulting frames onto a canvas.  That split is
what lets the animation code be unit-tested and previewed without a display.
"""
