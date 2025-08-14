""" Core API and orchestration for text rendering. """

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy import ImageClip
from fontTools.ttLib import TTFont
from moviepy import TextClip
from math import ceil
from typing import Any, Dict, Optional
from moviepy import VideoClip, CompositeVideoClip, ColorClip
from tools.schema.dataclass import Rect, Payload, Fonts, Style
from .layout import (
    _mk_text_clip, 
    _pad_transparent,
    _fit_into_rect, 
    _place_in_rect, 
    _caption_bg
)
# ----

def suggest_baseline_pad_pct(font_path: str, fudge: float = 0.06) -> float:
    """
    Estimate the baseline padding percentage for a given font.

    This function reads the font's metrics and calculates the recommended
    bottom padding as a fraction of the font's units-per-em (UPM), then adds
    a small adjustment factor (`fudge`).

    Args:
        font_path (str): Path to the font file (e.g., .ttf or .otf).
        fudge (float, optional): Additional padding to add to the calculated
            baseline fraction. Default is 0.06.

    Returns:
        float: Baseline padding percentage (0–1) recommended for this font.

    Example:
        >>> suggest_baseline_pad_pct("Inter-Regular.ttf")
        0.30
    """
    tt_font = TTFont(font_path)
    upm = tt_font["head"].unitsPerEm
    descent = abs(tt_font["hhea"].descent)
    return (descent / upm) + fudge

# ----


def oversized_text_clip(
    text: str,
    font_path: str,
    font_size: int,
    color: str = "white",
    bottom_extra_pct: float = 0.4,
    width: int | None = None,
    align: str = "left"
) -> ImageClip:
    """
    Create an oversized text clip with extra bottom padding.

    This function renders text onto a transparent RGBA canvas, adding extra
    space at the bottom to prevent clipping of characters with descenders.

    Args:
        text (str): The text string to render.
        font_path (str): Path to the font file (.ttf or .otf).
        font_size (int): Font size in points.
        color (str, optional): Text color. Defaults to "white".
        bottom_extra_pct (float, optional): Extra space at the bottom as a
            fraction of font size. Defaults to 0.4.
        width (int | None, optional): Canvas width. If None, matches text width.
        align (str, optional): Text alignment (currently unused in positioning).
            Defaults to "left".

    Returns:
        ImageClip: A MoviePy ImageClip object containing the rendered text.
    """
    font = ImageFont.truetype(font_path, font_size)
    _, descent = font.getmetrics()
    text_width, text_height = font.getmask(text).size

    extra_bottom = int(font_size * bottom_extra_pct)
    canvas_height = text_height + extra_bottom
    if width is None:
        width = text_width

    img = Image.new("RGBA", (width, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, font=font, fill=color)

    return ImageClip(np.array(img))

# ----

def make_text(
    text: str,
    font_path: str,
    px: int,
    safe: bool = True
) -> TextClip:
    """
    Create a text clip, optionally with extra bottom padding for safety.

    When `safe` is True, the function uses `oversized_text_clip` to add extra
    bottom space, preventing descenders from being cut off. Otherwise, it
    creates a standard `TextClip` using MoviePy.

    Args:
        text (str): The text string to render.
        font_path (str): Path to the font file (.ttf or .otf).
        px (int): Font size in pixels.
        safe (bool, optional): If True, adds extra padding to avoid clipping.
            Defaults to True.

    Returns:
        TextClip: A MoviePy `TextClip` or `ImageClip` containing the rendered text.
    """
    if safe:
        return oversized_text_clip(text, font_path, px, bottom_extra_pct=0.40)
    return TextClip(
        text=text,
        font=font_path,
        font_size=px,
        method="label",
        color="white",
        transparent=True
    )

#---

def render_text_element(
    element_id: str,
    payload: "Payload",
    spec: Dict[str, Any],
    variant: str = "primary",
    fonts: Optional["Fonts"] = None,
    style: Optional["Style"] = None,
    duration: Optional[float] = None,
    debug_rect: bool = False
) -> VideoClip:
    """
    Render a text-based element into a positioned MoviePy VideoClip.

    Args:
        element_id (str): ID of the element type to render.
        payload (Payload): Either a text string or an existing VideoClip.
        spec (dict): Specification containing element types and layout data.
        variant (str, optional): Layout variant to use ("primary" or "alternate").
            Defaults to "primary".
        fonts (Fonts, optional): Fonts configuration. Defaults to a new Fonts instance.
        style (Style, optional): Style configuration. Defaults to a new Style instance.
        duration (float, optional): Duration of the resulting clip in seconds.
        debug_rect (bool, optional): If True, overlays a semi-transparent
            debug rectangle showing the element's bounding box.

    Returns:
        VideoClip: The rendered and positioned MoviePy VideoClip.
    """
    fonts = fonts or Fonts()
    style = style or Style()

    # Find element type definition
    element_type = next(x for x in spec["types"] if x["id"] == element_id)
    layout_variant = "alternate" if variant == "alternate" else "primary"
    layout = element_type["layout"][layout_variant]

    rect: Rect = tuple(layout["rect"])
    h_align: str = layout.get("align", "left")
    px = int(element_type["size"]["common"])

    # Create or fit the base clip
    if isinstance(payload, str):
        is_mono = bool(element_type["size"].get("mono"))
        font_path = fonts.mono if is_mono else fonts.sans
        base: VideoClip = _mk_text_clip(payload, rect, font_path, px, h_align, style)

        pad_top = int(max(2, ceil(px * style.top_pad_pct)))
        pad_bottom = int(max(4, ceil(px * style.baseline_pad_pct)))
        clip: VideoClip = _pad_transparent(base, 0, pad_top, 0, pad_bottom)
    else:
        clip = _fit_into_rect(payload, rect)

    # Determine vertical alignment
    if element_id in {"section_marker", "equation", "quiz_question", "quiz_feedback", "cta"}:
        v_align = "center"
    elif element_id == "captions":
        v_align = "bottom"
    else:
        v_align = "top"

    # Add caption background if needed
    if element_id == "captions" and isinstance(payload, str):
        clip = _caption_bg(clip, pad=max(style.pad, 14), opacity=0.65)

    # Apply opacity and duration
    if style.opacity != 1.0:
        clip = clip.with_opacity(style.opacity)
    if duration is not None:
        clip = clip.with_duration(duration)

    # Place in final position
    clip = _place_in_rect(clip, rect, h_align=h_align, v_align=v_align)

    # Optional debug rectangle overlay
    if debug_rect:
        x, y, w, h = rect
        box = (
            ColorClip((w, h), color=(255, 255, 255))
            .with_opacity(0.15)
            .with_duration(clip.duration or duration)
            .with_position((x, y))
        )
        return CompositeVideoClip([box, clip], size=(1920, 1080))

    return clip