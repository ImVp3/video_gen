""" Layout utilities and low-level text primitives. """

import numpy as np
from moviepy import TextClip, ColorClip, CompositeVideoClip, VideoClip
from math import ceil
from typing import Optional
from tools.schema.dataclass import Rect, Fonts, Style
from math import ceil
from typing import Any, Dict, Optional, List
from moviepy import VideoClip, CompositeVideoClip, ColorClip
# ----

def _pad_transparent(
    clip: VideoClip,
    left: int,
    top: int,
    right: int,
    bottom: int,
    bg_opacity: float = 0.01
) -> VideoClip:
    """
    Pad a clip with a nearly transparent background to expand the mask area
    without cropping alpha.

    Args:
        clip (VideoClip): The input MoviePy clip.
        left (int): Padding in pixels on the left side.
        top (int): Padding in pixels on the top side.
        right (int): Padding in pixels on the right side.
        bottom (int): Padding in pixels on the bottom side.
        bg_opacity (float, optional): Opacity of the background pad. Defaults to 0.01.

    Returns:
        VideoClip: The padded clip with the original content positioned accordingly.
    """
    width = clip.w + left + right
    height = clip.h + top + bottom

    background = (
        ColorClip(size=(width, height), color=(0, 0, 0))
        .with_opacity(bg_opacity)
        .with_duration(clip.duration or None)
    )

    return CompositeVideoClip(
        [background, clip.with_position((left, top))],
        size=(width, height)
    )

# ----

def _mk_text_clip(
    text: str,
    rect: Rect,
    font_path: Optional[str],
    px: int,
    text_align: str,
    style
) -> VideoClip:
    """
    Create a text clip safely, preventing descenders/diacritics from being cropped.

    This function automatically decides whether to render text in
    "wrap" mode (caption) or "line" mode (label) based on content length
    and line breaks, unless overridden via `style.mode_hint`.

    Args:
        text (str): The text to render.
        rect (tuple[int, int, int, int]): (x, y, width, height) rectangle for layout.
        font_path (str | None): Path to the font file (.ttf/.otf), or None for default.
        px (int): Font size in pixels.
        text_align (str): Horizontal text alignment ("left", "center", "right").
        style: Style configuration object with color, stroke, padding, etc.

    Returns:
        VideoClip: A MoviePy clip with safe padding applied.
    """
    _, _, w, _ = rect

    # Determine rendering mode
    mode_hint = getattr(style, "mode_hint", None)
    is_multiline_input = "\n" in text
    heuristic_wrap = is_multiline_input or (w and len(text) > 22)
    use_wrap = (mode_hint == "wrap") or (mode_hint is None and heuristic_wrap)

    # Render text
    if use_wrap:
        # Caption mode: wrap text to width, apply interline spacing, honor text alignment
        base = TextClip(
            text=text,
            font=font_path,
            font_size=px,
            color=style.color,
            method="caption",
            size=(w, None),
            text_align=text_align,
            interline=getattr(style, "interline", 6),
            stroke_color=style.stroke_color,
            stroke_width=style.stroke_width,
            transparent=True
        )
    else:
        # Label mode: single line, cleaner bbox for descenders
        base = TextClip(
            text=text,
            font=font_path,
            font_size=px,
            color=style.color,
            method="label",
            stroke_color=style.stroke_color,
            stroke_width=style.stroke_width,
            transparent=True
        )

    # Safe padding percentages
    top_pct = max(0.06, getattr(style, "top_pad_pct", 0.10))
    bot_pct = max(0.24, getattr(style, "baseline_pad_pct", 0.32))
    pad_top = int(max(2, ceil(px * top_pct)))
    pad_bottom = int(max(4, ceil(px * bot_pct)))

    # Apply transparent padding to avoid cropping in alpha mask
    return _pad_transparent(base, 0, pad_top, 0, pad_bottom, bg_opacity=0.01)

#---

def _place_in_rect(
    clip: VideoClip,
    rect: Rect,
    h_align: str,
    v_align: str
) -> VideoClip:
    """
    Position a clip within a target rectangle based on horizontal and vertical alignment.

    Args:
        clip (VideoClip): The clip to position.
        rect (Rect): A tuple (x, y, width, height) defining the target rectangle.
        h_align (str): Horizontal alignment ("left", "center", "right").
        v_align (str): Vertical alignment ("top", "center", "bottom").

    Returns:
        VideoClip: Clip positioned relative to the rectangle.
    """
    x, y, w, h = rect

    if h_align == "center":
        px = x + max(0, (w - clip.w) // 2)
    elif h_align == "right":
        px = x + max(0, (w - clip.w))
    else:  # left
        px = x

    if v_align == "center":
        py = y + max(0, (h - clip.h) // 2)
    elif v_align == "bottom":
        py = y + max(0, (h - clip.h))
    else:  # top
        py = y

    return clip.with_position((px, py))


def _fit_into_rect(clip: VideoClip, rect: Rect) -> VideoClip:
    """
    Scale down a clip proportionally to fit inside a given rectangle.

    Args:
        clip (VideoClip): The clip to resize if needed.
        rect (Rect): A tuple (x, y, width, height) for the target area.

    Returns:
        VideoClip: Resized clip if larger than target, otherwise unchanged.
    """
    _, _, w, h = rect

    if clip.w > w or clip.h > h:
        scale = max(clip.w / w, clip.h / h)
        clip = clip.resized(new_size=(int(clip.w / scale), int(clip.h / scale)))

    return clip


def _caption_bg(
    text_clip: VideoClip,
    pad: int,
    opacity: float = 0.65
) -> VideoClip:
    """
    Add a semi-transparent background behind a text clip.

    Args:
        text_clip (VideoClip): The text clip to wrap.
        pad (int): Padding in pixels around the text.
        opacity (float, optional): Opacity of the background (0–1). Defaults to 0.65.

    Returns:
        VideoClip: A composite clip with the background and text.
    """
    width = text_clip.w + pad * 2
    height = text_clip.h + pad * 2

    background = (
        ColorClip(size=(width, height), color=(0, 0, 0))
        .with_opacity(opacity)
        .with_duration(text_clip.duration or None)
    )

    return CompositeVideoClip(
        [background, text_clip.with_position((pad, pad))],
        size=(width, height)
    )

#---

def wrapped_text_clip(
    element_id: str,
    text: str,
    spec: Dict[str, Any],
    variant: str = "primary",
    fonts: Optional["Fonts"] = None,
    style: Optional["Style"] = None,
    duration: Optional[float] = None,
    max_lines: Optional[int] = None,
    overflow: str = "shrink",  # "none" | "shrink"
    min_font_size: int = 18,
    debug_rect: bool = False,
) -> VideoClip:
    """
    Create a multi-line text clip in wrap mode (automatic line breaking to fit width).

    Args:
        element_id (str): The element ID from the spec.
        text (str): Text content to render.
        spec (dict): Layout specification containing types and positions.
        variant (str, optional): Layout variant ("primary" or "alternate"). Defaults to "primary".
        fonts (Fonts, optional): Fonts configuration. Defaults to a new Fonts instance.
        style (Style, optional): Style configuration. Defaults to a new Style instance.
        duration (float, optional): Duration of the clip in seconds.
        max_lines (int, optional): Maximum number of lines allowed.
        overflow (str, optional): Overflow behavior: "none" or "shrink". Defaults to "shrink".
        min_font_size (int, optional): Minimum font size when shrinking. Defaults to 18.
        debug_rect (bool, optional): If True, overlays a debug rectangle.

    Returns:
        VideoClip: The rendered and positioned clip.
    """
    fonts = fonts or Fonts()
    style = style or Style()

    element_type = next(x for x in spec["types"] if x["id"] == element_id)
    layout = element_type["layout"]["alternate" if variant == "alternate" else "primary"]
    rect = tuple(layout["rect"])
    h_align = layout.get("align", "left")
    px = int(element_type["size"]["common"])

    base = _mk_text_clip(
        text,
        rect,
        fonts.mono if element_type["size"].get("mono") else fonts.sans,
        px,
        h_align,
        style
    )

    pad_top = int(max(2, ceil(px * style.top_pad_pct)))
    pad_bottom = int(max(4, ceil(px * style.baseline_pad_pct)))
    clip = _pad_transparent(base, 0, pad_top, 0, pad_bottom)

    allowed_h = rect[3]
    if max_lines:
        line_h = px + style.interline
        allowed_h = min(
            allowed_h,
            int(style.top_pad_pct * px + max_lines * line_h + style.baseline_pad_pct * px)
        )

    if overflow == "shrink" and clip.h > allowed_h:
        scale = allowed_h / float(clip.h)
        est_font = px * scale
        if est_font < min_font_size:
            scale = min_font_size / float(px)
        clip = clip.resized(
            new_size=(max(1, int(clip.w * scale)), max(1, int(clip.h * scale)))
        )

    if element_id in {"section_marker", "equation", "quiz_question", "quiz_feedback", "cta"}:
        v_align = "center"
    elif element_id == "captions":
        v_align = "bottom"
    else:
        v_align = "top"

    if element_id == "captions":
        clip = _caption_bg(clip, pad=max(style.pad, 14), opacity=0.65)

    if style.opacity != 1.0:
        clip = clip.with_opacity(style.opacity)
    if duration is not None:
        clip = clip.with_duration(duration)

    placed = _place_in_rect(clip, rect, h_align=h_align, v_align=v_align)

    if debug_rect:
        x, y, w, h = rect
        box = (
            ColorClip((w, h), color=(255, 255, 255))
            .with_opacity(0.15)
            .with_duration(placed.duration or duration)
            .with_position((x, y))
        )
        return CompositeVideoClip([box, placed], size=(1920, 1080))

    return placed


def structured_multiline_clip(
    element_id: str,
    lines: List[str],
    spec: Dict[str, Any],
    variant: str = "primary",
    fonts: Optional["Fonts"] = None,
    style: Optional["Style"] = None,
    duration: float = 3.0,
    stagger: float = 0.25,
    gap_px: Optional[int] = None,
    h_align_override: Optional[str] = None,
    v_align: str = "top",  # "top" | "center" | "bottom"
    debug_rect: bool = False,
) -> VideoClip:
    """
    Create a structured multi-line clip, where each line is a separate clip
    appearing in a staggered sequence.

    Args:
        element_id (str): Element ID from the spec.
        lines (list[str]): List of text lines.
        spec (dict): Layout specification.
        variant (str, optional): Layout variant. Defaults to "primary".
        fonts (Fonts, optional): Fonts configuration. Defaults to a new Fonts instance.
        style (Style, optional): Style configuration. Defaults to a new Style instance.
        duration (float, optional): Total segment duration. Defaults to 3.0 seconds.
        stagger (float, optional): Delay between line appearances. Defaults to 0.25 seconds.
        gap_px (int, optional): Pixel gap between lines. Defaults to ~25% of font size.
        h_align_override (str, optional): Override for horizontal alignment.
        v_align (str, optional): Vertical alignment of the block. Defaults to "top".
        debug_rect (bool, optional): If True, overlays a debug rectangle.

    Returns:
        VideoClip: Composite video clip with staggered lines.
    """
    fonts = fonts or Fonts()
    style = style or Style()

    element_type = next(x for x in spec["types"] if x["id"] == element_id)
    layout = element_type["layout"]["alternate" if variant == "alternate" else "primary"]
    rect = tuple(layout["rect"])
    base_align = layout.get("align", "left")
    h_align = h_align_override or base_align
    px = int(element_type["size"]["common"])

    line_clips = []
    for s in lines:
        base = _mk_text_clip(
            s,
            rect,
            fonts.mono if element_type["size"].get("mono") else fonts.sans,
            px,
            h_align,
            style
        )
        pad_top = int(max(2, ceil(px * style.top_pad_pct)))
        pad_bottom = int(max(4, ceil(px * style.baseline_pad_pct)))
        c = _pad_transparent(base, 0, pad_top, 0, pad_bottom)
        line_clips.append(c)

    gap = gap_px if gap_px is not None else max(6, int(px * 0.25))
    total_h = sum(c.h for c in line_clips) + gap * (len(line_clips) - 1)

    rect_h = rect[3]
    if total_h > rect_h:
        scale = rect_h / float(total_h)
        for i in range(len(line_clips)):
            c = line_clips[i]
            line_clips[i] = c.resized(
                new_size=(max(1, int(c.w * scale)), max(1, int(c.h * scale)))
            )
        gap = int(gap * scale)
        total_h = sum(c.h for c in line_clips) + gap * (len(line_clips) - 1)

    x, y, w, h = rect
    if v_align == "center":
        y0 = y + max(0, (h - total_h) // 2)
    elif v_align == "bottom":
        y0 = y + max(0, h - total_h)
    else:
        y0 = y

    placed = []
    y_cursor = y0
    for i, c in enumerate(line_clips):
        placed_i = _place_in_rect(c, (x, y_cursor, w, c.h), h_align=h_align, v_align="top")
        start_i = i * max(0.0, float(stagger))
        live_dur = max(0.001, duration - start_i)
        placed.append(placed_i.with_start(start_i).with_duration(live_dur))
        y_cursor += c.h + gap

    comp = CompositeVideoClip(placed, size=(1920, 1080)).with_duration(duration)

    if debug_rect:
        box = (
            ColorClip((w, h), color=(255, 255, 255))
            .with_opacity(0.12)
            .with_duration(duration)
            .with_position((x, y))
        )
        comp = CompositeVideoClip([box, comp], size=(1920, 1080)).with_duration(duration)

    return comp