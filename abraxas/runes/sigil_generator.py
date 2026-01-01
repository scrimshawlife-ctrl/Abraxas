"""Deterministic SVG sigil generator for ABX-Runes.

Pure Python implementation using SHA-256 based PRNG.
No external dependencies beyond stdlib.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any


class SigilPRNG:
    """Deterministic PRNG based on SHA-256 hash chaining."""

    def __init__(self, seed_material: str):
        """Initialize PRNG with seed material."""
        self.state = hashlib.sha256(seed_material.encode("utf-8")).digest()
        self.position = 0

    def next_bytes(self, n: int) -> bytes:
        """Generate next N bytes deterministically."""
        result = b""
        while len(result) < n:
            # Hash current state to get next bytes
            chunk = hashlib.sha256(self.state + self.position.to_bytes(8, "big")).digest()
            result += chunk
            self.position += 1
        return result[:n]

    def next_float(self) -> float:
        """Generate next float in [0, 1)."""
        # Use 8 bytes for high precision float
        bytes_val = self.next_bytes(8)
        int_val = int.from_bytes(bytes_val, "big")
        return int_val / (2**64)

    def next_int(self, min_val: int, max_val: int) -> int:
        """Generate next int in [min_val, max_val]."""
        return min_val + int(self.next_float() * (max_val - min_val + 1))

    def next_angle(self) -> float:
        """Generate next angle in [0, 2π)."""
        return self.next_float() * 2 * math.pi


class SVGBuilder:
    """Build SVG elements with deterministic formatting."""

    def __init__(self, width: int = 512, height: int = 512):
        self.width = width
        self.height = height
        self.elements: list[str] = []

    def _fmt(self, value: float) -> str:
        """Format float with fixed precision."""
        return f"{value:.3f}"

    def circle(self, cx: float, cy: float, r: float, stroke: str = "#000", fill: str = "none", stroke_width: float = 2.0) -> None:
        """Add circle element."""
        attrs = [
            f'cx="{self._fmt(cx)}"',
            f'cy="{self._fmt(cy)}"',
            f'fill="{fill}"',
            f'r="{self._fmt(r)}"',
            f'stroke="{stroke}"',
            f'stroke-width="{self._fmt(stroke_width)}"',
        ]
        self.elements.append(f'<circle {" ".join(attrs)}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str = "#000", stroke_width: float = 2.0) -> None:
        """Add line element."""
        attrs = [
            f'stroke="{stroke}"',
            f'stroke-width="{self._fmt(stroke_width)}"',
            f'x1="{self._fmt(x1)}"',
            f'x2="{self._fmt(x2)}"',
            f'y1="{self._fmt(y1)}"',
            f'y2="{self._fmt(y2)}"',
        ]
        self.elements.append(f'<line {" ".join(attrs)}/>')

    def path(self, d: str, stroke: str = "#000", fill: str = "none", stroke_width: float = 2.0) -> None:
        """Add path element."""
        attrs = [
            f'd="{d}"',
            f'fill="{fill}"',
            f'stroke="{stroke}"',
            f'stroke-width="{self._fmt(stroke_width)}"',
        ]
        self.elements.append(f'<path {" ".join(attrs)}/>')

    def arc(self, cx: float, cy: float, r: float, start_angle: float, end_angle: float, stroke: str = "#000", stroke_width: float = 2.0) -> None:
        """Add arc path."""
        # Normalize angles
        start = start_angle % (2 * math.pi)
        end = end_angle % (2 * math.pi)

        # Calculate start and end points
        x1 = cx + r * math.cos(start)
        y1 = cy + r * math.sin(start)
        x2 = cx + r * math.cos(end)
        y2 = cy + r * math.sin(end)

        # Determine large arc flag
        angle_diff = (end - start) % (2 * math.pi)
        large_arc = 1 if angle_diff > math.pi else 0

        d = f"M {self._fmt(x1)} {self._fmt(y1)} A {self._fmt(r)} {self._fmt(r)} 0 {large_arc} 1 {self._fmt(x2)} {self._fmt(y2)}"
        self.path(d, stroke=stroke, stroke_width=stroke_width)

    def build(self) -> str:
        """Build complete SVG string."""
        header = f'<svg height="{self.height}" viewBox="0 0 {self.width} {self.height}" width="{self.width}" xmlns="http://www.w3.org/2000/svg">\n'
        group_start = '<g id="sigil">\n'
        group_end = '</g>\n'
        footer = '</svg>\n'

        return header + group_start + "\n".join(self.elements) + "\n" + group_end + footer


class SigilGenerator:
    """Generate deterministic sigils for ABX-Runes."""

    def __init__(self, seed_material: str, width: int = 512, height: int = 512):
        self.prng = SigilPRNG(seed_material)
        self.width = width
        self.height = height
        self.cx = width / 2
        self.cy = height / 2

    def generate_rfa(self) -> str:
        """Generate sigil for ϟ₁ RFA (Resonant Field Anchor)."""
        svg = SVGBuilder(self.width, self.height)

        # Central anchor circle
        anchor_radius = 20 + self.prng.next_float() * 10
        svg.circle(self.cx, self.cy, anchor_radius, stroke_width=3.0)

        # Resonant field rings
        num_rings = self.prng.next_int(3, 5)
        for i in range(num_rings):
            ring_radius = 60 + i * 40 + self.prng.next_float() * 20
            svg.circle(self.cx, self.cy, ring_radius, stroke_width=1.5)

        # Radial stabilizers
        num_rays = self.prng.next_int(6, 8)
        for i in range(num_rays):
            angle = (2 * math.pi * i) / num_rays + self.prng.next_float() * 0.2
            r1 = anchor_radius + 10
            r2 = 220 + self.prng.next_float() * 20
            x1 = self.cx + r1 * math.cos(angle)
            y1 = self.cy + r1 * math.sin(angle)
            x2 = self.cx + r2 * math.cos(angle)
            y2 = self.cy + r2 * math.sin(angle)
            svg.line(x1, y1, x2, y2, stroke_width=2.0)

        return svg.build()

    def generate_tam(self) -> str:
        """Generate sigil for ϟ₂ TAM (Traversal-as-Meaning)."""
        svg = SVGBuilder(self.width, self.height)

        # Center node
        svg.circle(self.cx, self.cy, 15, stroke_width=3.0)

        # Traversal paths (spiral outward)
        num_paths = self.prng.next_int(4, 6)
        for i in range(num_paths):
            start_angle = self.prng.next_angle()
            num_segments = self.prng.next_int(8, 12)

            for j in range(num_segments - 1):
                t1 = j / num_segments
                t2 = (j + 1) / num_segments
                r1 = 30 + t1 * 180
                r2 = 30 + t2 * 180
                a1 = start_angle + t1 * math.pi * 2
                a2 = start_angle + t2 * math.pi * 2

                x1 = self.cx + r1 * math.cos(a1)
                y1 = self.cy + r1 * math.sin(a1)
                x2 = self.cx + r2 * math.cos(a2)
                y2 = self.cy + r2 * math.sin(a2)

                svg.line(x1, y1, x2, y2, stroke_width=1.5)

        # Path markers (dots at key points)
        num_markers = self.prng.next_int(5, 8)
        for i in range(num_markers):
            angle = self.prng.next_angle()
            radius = 50 + self.prng.next_float() * 160
            mx = self.cx + radius * math.cos(angle)
            my = self.cy + radius * math.sin(angle)
            svg.circle(mx, my, 4, stroke_width=2.0, fill="#000")

        return svg.build()

    def generate_wsss(self) -> str:
        """Generate sigil for ϟ₃ WSSS (Weak Signal · Strong Structure)."""
        svg = SVGBuilder(self.width, self.height)

        # Strong structure: geometric grid
        grid_size = self.prng.next_int(4, 6)
        cell_size = 200 / grid_size

        for i in range(grid_size + 1):
            offset = i * cell_size
            # Vertical lines
            x = self.cx - 100 + offset
            svg.line(x, self.cy - 100, x, self.cy + 100, stroke_width=2.0)
            # Horizontal lines
            y = self.cy - 100 + offset
            svg.line(self.cx - 100, y, self.cx + 100, y, stroke_width=2.0)

        # Weak signal: faint, scattered marks
        num_signals = self.prng.next_int(15, 25)
        for i in range(num_signals):
            sx = self.cx - 120 + self.prng.next_float() * 240
            sy = self.cy - 120 + self.prng.next_float() * 240
            sr = 2 + self.prng.next_float() * 3
            svg.circle(sx, sy, sr, stroke_width=0.5)

        # Central anchor
        svg.circle(self.cx, self.cy, 10, stroke_width=3.0)

        return svg.build()

    def generate_sds(self) -> str:
        """Generate sigil for ϟ₄ SDS (State-Dependent Susceptibility)."""
        svg = SVGBuilder(self.width, self.height)

        # Central state indicator (filled when open, empty when closed)
        state_radius = 25 + self.prng.next_float() * 10
        svg.circle(self.cx, self.cy, state_radius, stroke_width=3.0)

        # Phase gates (open/closed symbols)
        num_gates = self.prng.next_int(6, 8)
        gate_radius = 100 + self.prng.next_float() * 30

        for i in range(num_gates):
            angle = (2 * math.pi * i) / num_gates
            gx = self.cx + gate_radius * math.cos(angle)
            gy = self.cy + gate_radius * math.sin(angle)

            # Gate symbol: rectangle with opening
            gate_width = 15
            gate_height = 25
            is_open = self.prng.next_float() > 0.5

            # Draw gate frame
            x1 = gx - gate_width / 2
            x2 = gx + gate_width / 2
            y1 = gy - gate_height / 2
            y2 = gy + gate_height / 2

            if is_open:
                # Open gate: gap at top
                svg.line(x1, y1 + 8, x1, y2, stroke_width=2.0)
                svg.line(x2, y1 + 8, x2, y2, stroke_width=2.0)
                svg.line(x1, y2, x2, y2, stroke_width=2.0)
            else:
                # Closed gate: complete rectangle
                svg.line(x1, y1, x1, y2, stroke_width=2.0)
                svg.line(x2, y1, x2, y2, stroke_width=2.0)
                svg.line(x1, y1, x2, y1, stroke_width=2.0)
                svg.line(x1, y2, x2, y2, stroke_width=2.0)

        # Susceptibility field lines
        num_field_lines = self.prng.next_int(8, 12)
        for i in range(num_field_lines):
            angle = self.prng.next_angle()
            r1 = state_radius + 15
            r2 = 200 + self.prng.next_float() * 40
            x1 = self.cx + r1 * math.cos(angle)
            y1 = self.cy + r1 * math.sin(angle)
            x2 = self.cx + r2 * math.cos(angle)
            y2 = self.cy + r2 * math.sin(angle)
            svg.line(x1, y1, x2, y2, stroke_width=1.0)

        return svg.build()

    def generate_ipl(self) -> str:
        """Generate sigil for ϟ₅ IPL (Intermittent Phase-Lock)."""
        svg = SVGBuilder(self.width, self.height)

        # Central oscillator
        svg.circle(self.cx, self.cy, 20, stroke_width=3.0)

        # Phase-lock windows (bounded arcs with gaps)
        num_windows = self.prng.next_int(5, 7)
        window_radius = 80 + self.prng.next_float() * 20

        for i in range(num_windows):
            # Each window is an arc segment
            base_angle = (2 * math.pi * i) / num_windows
            arc_span = (math.pi / 3) + self.prng.next_float() * (math.pi / 6)  # 60-90 degrees
            start_angle = base_angle
            end_angle = base_angle + arc_span

            svg.arc(self.cx, self.cy, window_radius, start_angle, end_angle, stroke_width=3.0)

            # Mark window boundaries
            x_start = self.cx + window_radius * math.cos(start_angle)
            y_start = self.cy + window_radius * math.sin(start_angle)
            x_end = self.cx + window_radius * math.cos(end_angle)
            y_end = self.cy + window_radius * math.sin(end_angle)

            svg.circle(x_start, y_start, 5, stroke_width=2.0, fill="#000")
            svg.circle(x_end, y_end, 5, stroke_width=2.0, fill="#000")

        # Refractory periods (gaps between windows shown as faint arcs)
        refractory_radius = window_radius + 30
        for i in range(num_windows):
            base_angle = (2 * math.pi * i) / num_windows
            arc_span = (math.pi / 3)
            gap_start = base_angle + arc_span
            gap_end = base_angle + (2 * math.pi / num_windows)

            if gap_end > gap_start:
                svg.arc(self.cx, self.cy, refractory_radius, gap_start, gap_end, stroke_width=1.0)

        # Intermittent pulses (radial markers)
        num_pulses = self.prng.next_int(10, 15)
        for i in range(num_pulses):
            angle = self.prng.next_angle()
            r1 = 30
            r2 = 60
            x1 = self.cx + r1 * math.cos(angle)
            y1 = self.cy + r1 * math.sin(angle)
            x2 = self.cx + r2 * math.cos(angle)
            y2 = self.cy + r2 * math.sin(angle)
            svg.line(x1, y1, x2, y2, stroke_width=1.5)

        return svg.build()

    def generate_add(self) -> str:
        """Generate sigil for ϟ₆ ADD (Anchor Drift Detector)."""
        svg = SVGBuilder(self.width, self.height)

        # Original anchor position (reference)
        original_x = self.cx - 30
        original_y = self.cy - 30
        svg.circle(original_x, original_y, 15, stroke_width=2.0, stroke="#888")

        # Drifted anchor position (current)
        drifted_x = self.cx + 30
        drifted_y = self.cy + 30
        svg.circle(drifted_x, drifted_y, 15, stroke_width=3.0, stroke="#000")

        # Drift vector (arrow from original to drifted)
        svg.line(original_x, original_y, drifted_x, drifted_y, stroke_width=2.5, stroke="#000")

        # Arrow head
        arrow_angle = math.atan2(drifted_y - original_y, drifted_x - original_x)
        arrow_size = 12
        arrow_angle1 = arrow_angle + math.pi * 0.85
        arrow_angle2 = arrow_angle - math.pi * 0.85

        ax1 = drifted_x + arrow_size * math.cos(arrow_angle1)
        ay1 = drifted_y + arrow_size * math.sin(arrow_angle1)
        ax2 = drifted_x + arrow_size * math.cos(arrow_angle2)
        ay2 = drifted_y + arrow_size * math.sin(arrow_angle2)

        svg.line(drifted_x, drifted_y, ax1, ay1, stroke_width=2.5)
        svg.line(drifted_x, drifted_y, ax2, ay2, stroke_width=2.5)

        # Drift measurement circles (expanding from original)
        num_measurements = self.prng.next_int(4, 6)
        for i in range(num_measurements):
            measure_radius = 30 + i * 30
            svg.circle(original_x, original_y, measure_radius, stroke_width=0.8, stroke="#888")

        # Correction indicators (recenter markers)
        num_correctors = self.prng.next_int(6, 8)
        corrector_radius = 150 + self.prng.next_float() * 30

        for i in range(num_correctors):
            angle = (2 * math.pi * i) / num_correctors
            cx_mark = self.cx + corrector_radius * math.cos(angle)
            cy_mark = self.cy + corrector_radius * math.sin(angle)

            # Small cross marker
            cross_size = 8
            svg.line(cx_mark - cross_size, cy_mark, cx_mark + cross_size, cy_mark, stroke_width=1.5)
            svg.line(cx_mark, cy_mark - cross_size, cx_mark, cy_mark + cross_size, stroke_width=1.5)

        # Entropy decay indicator (spiral from drifted position)
        num_spiral_points = 20
        for i in range(num_spiral_points - 1):
            t1 = i / num_spiral_points
            t2 = (i + 1) / num_spiral_points
            r1 = 20 + t1 * 50
            r2 = 20 + t2 * 50
            a1 = t1 * math.pi * 3
            a2 = t2 * math.pi * 3

            x1 = drifted_x + r1 * math.cos(a1)
            y1 = drifted_y + r1 * math.sin(a1)
            x2 = drifted_x + r2 * math.cos(a2)
            y2 = drifted_y + r2 * math.sin(a2)

            svg.line(x1, y1, x2, y2, stroke_width=1.0)

        return svg.build()


def generate_sigil(rune_id: str, seed_material: str) -> str:
    """Generate sigil for a specific rune ID.

    Args:
        rune_id: Rune identifier (e.g., 'ϟ₁', 'ϟ₂', etc.)
        seed_material: Deterministic seed material for generation

    Returns:
        SVG string
    """
    generator = SigilGenerator(seed_material)

    generators_map = {
        "ϟ₁": generator.generate_rfa,
        "ϟ₂": generator.generate_tam,
        "ϟ₃": generator.generate_wsss,
        "ϟ₄": generator.generate_sds,
        "ϟ₅": generator.generate_ipl,
        "ϟ₆": generator.generate_add,
    }

    generator_func = generators_map.get(rune_id)
    if generator_func is None:
        raise ValueError(f"No sigil generator for rune ID: {rune_id}")

    return generator_func()
