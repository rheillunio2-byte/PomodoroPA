"""Easing curves and spring physics."""
from __future__ import annotations

import math
from typing import Callable, Sequence

Easing = Callable[[float], float]


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


# --------------------------------------------------------------------- easings

def linear(t: float) -> float:
    return t


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_expo(t: float) -> float:
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def ease_out_back(t: float, overshoot: float = 1.70158) -> float:
    c3 = overshoot + 1
    return 1 + c3 * (t - 1) ** 3 + overshoot * (t - 1) ** 2


def cubic_bezier(x1: float, y1: float, x2: float, y2: float) -> Easing:
    """CSS-style ``cubic-bezier()`` easing (what Motion/Framer use for ``ease``)."""

    def bx(s: float) -> float:
        return 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s ** 2 * x2 + s ** 3

    def by(s: float) -> float:
        return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s ** 2 * y2 + s ** 3

    def dbx(s: float) -> float:
        return 3 * (1 - s) ** 2 * x1 + 6 * (1 - s) * s * (x2 - x1) + 3 * s ** 2 * (1 - x2)

    def solve(t: float) -> float:
        s = t
        for _ in range(6):                      # Newton–Raphson
            err = bx(s) - t
            slope = dbx(s)
            if abs(err) < 1e-6 or abs(slope) < 1e-6:
                break
            s -= err / slope
        if not 0.0 <= s <= 1.0 or abs(bx(s) - t) > 1e-4:   # bisection fallback
            low, high, s = 0.0, 1.0, t
            for _ in range(40):
                s = (low + high) / 2
                if bx(s) < t:
                    low = s
                else:
                    high = s
        return s

    def ease(t: float) -> float:
        if t <= 0:
            return 0.0
        if t >= 1:
            return 1.0
        return by(solve(t))

    return ease


def resolve_easing(ease) -> Easing:
    """Accept a callable, a 4-number bezier sequence, or ``None`` (→ ease-out)."""
    if callable(ease):
        return ease
    if isinstance(ease, Sequence) and len(ease) == 4:
        return cubic_bezier(*ease)
    return ease_out_cubic


# ---------------------------------------------------------------------- spring

class Spring:
    """A damped spring on one number.

    Uses the same semi-implicit integrator as the React Bits Dock so that
    ``mass / stiffness / damping`` values copied from the component behave
    identically:  ``v = (v + h·k·(target − x)) / (1 + h·c + h²·k)``.
    """

    def __init__(self, value: float = 0.0, target: float | None = None, *,
                 stiffness: float = 150.0, damping: float = 12.0, mass: float = 1.0,
                 rest_delta: float = 0.01, rest_speed: float = 0.05):
        self.value = float(value)
        self.target = float(value if target is None else target)
        self.velocity = 0.0
        self.stiffness = max(1.0, stiffness)
        self.damping = max(0.0, damping)
        self.mass = max(0.01, mass)
        self.rest_delta = rest_delta
        self.rest_speed = rest_speed

    @property
    def settled(self) -> bool:
        return abs(self.velocity) < self.rest_speed and abs(self.target - self.value) < self.rest_delta

    def snap(self, value: float | None = None) -> None:
        self.value = self.target if value is None else float(value)
        if value is not None:
            self.target = float(value)
        self.velocity = 0.0

    def step(self, dt: float) -> float:
        """Advance by *dt* seconds (sub-stepped for stability) and return the value."""
        if self.settled:
            self.snap()
            return self.value
        steps = max(1, math.ceil(min(dt, 0.1) * 240))
        h = min(dt, 0.1) / steps
        k = self.stiffness / self.mass
        c = self.damping / self.mass
        for _ in range(steps):
            self.velocity = (self.velocity + h * k * (self.target - self.value)) / (1 + h * c + h * h * k)
            self.value += self.velocity * h
        if self.settled:
            self.snap()
        return self.value
