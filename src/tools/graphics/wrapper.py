from __future__ import annotations
from typing import List, Optional, Tuple
import logging

from moviepy import CompositeVideoClip,VideoClip, ColorClip

from tools.schema.dataclass import Meta, GraphicSpec, Layout, Rect
from tools.geometry.core import snap_to_safe
from .core import (
    probe_media, load_image_clip, compute_rect,
    position_clip, warn_if_upscale_core, make_solid_background,
    apply_policies, validate_graphic_spec
)
from utils import convert_color

def _maybe_snap(rect: Rect, spec: GraphicSpec, meta: Meta) -> Rect:
    return snap_to_safe(rect, meta) if spec.layout and spec.layout.snap_safe else rect

def build_solid_background(color: str|tuple,
                            size: Tuple[int, int],
                            duration: float) -> VideoClip:
    """
    Tạo nền màu đặc với size và duration.
    """
    try:
        return ColorClip(size, color=color).with_duration(duration)
    except Exception:
        color:tuple = convert_color(color)["rgb"]
        return ColorClip(size, color=color).with_duration(duration)
def build_background(spec: GraphicSpec, meta: Meta, scene_duration: float) -> VideoClip:
    """
    Nền màu hoặc ảnh (cover).
    """
    spec = apply_policies(spec, meta)
    errs = validate_graphic_spec(spec, meta)
    if errs:
        raise ValueError(f"Invalid background spec: {errs}")

    ly = spec.layout
    assert ly is not None
    rect = ly.rect

    if spec.color and not spec.src:
        # màu đặc
        return make_solid_background(spec.color, (meta.width, meta.height), scene_duration)

    # ảnh nền
    info = probe_media(spec.src)
    if info["kind"] != "image":
        raise ValueError(f"Background only supports images in MVP, got {info['kind']}")

    clip = load_image_clip(spec.src)
    placed = compute_rect((info["width"], info["height"]), rect, mode=ly.mode or "cover")
    warn_if_upscale_core((info["width"], info["height"]), placed, limit=1.5)
    placed = _maybe_snap(placed, spec, meta)
    return position_clip(clip, placed, opacity=ly.opacity, rotation=ly.rotation).with_duration(scene_duration)

def build_illustration(spec: GraphicSpec, meta: Meta, scene_duration: float) -> VideoClip:
    """
    Ảnh minh họa PNG/JPG (fit|cover), snap safe.
    """
    spec = apply_policies(spec, meta)
    errs = validate_graphic_spec(spec, meta)
    if errs:
        raise ValueError(f"Invalid illustration spec: {errs}")

    ly = spec.layout
    assert ly is not None
    rect = _maybe_snap(ly.rect, spec, meta)

    if spec.color and not spec.src:
        # shape đơn sắc (overlay dạng hình chữ nhật)
        shape = make_solid_background(spec.color, (rect[2], rect[3]), scene_duration)
        return position_clip(shape, (rect[0], rect[1], rect[2], rect[3]), opacity=ly.opacity, rotation=ly.rotation)

    info = probe_media(spec.src)
    if info["kind"] != "image":
        raise ValueError(f"Illustration supports images only in MVP, got {info['kind']}")

    clip = load_image_clip(spec.src)
    placed = compute_rect((info["width"], info["height"]), rect, mode=ly.mode)
    warn_if_upscale_core((info["width"], info["height"]), placed, limit=1.5)
    return position_clip(clip, placed, opacity=ly.opacity, rotation=ly.rotation).with_duration(scene_duration)

def build_overlay(spec: GraphicSpec, meta: Meta, scene_duration: float) -> VideoClip:
    """
    Logo/Watermark, ép snap_safe & z cao.
    """
    spec = apply_policies(spec, meta)
    errs = validate_graphic_spec(spec, meta)
    if errs:
        raise ValueError(f"Invalid overlay spec: {errs}")

    ly = spec.layout
    assert ly is not None
    rect = _maybe_snap(ly.rect, spec, meta)

    if spec.color and not spec.src:
        shape = make_solid_background(spec.color, (rect[2], rect[3]), scene_duration)
        return position_clip(shape, (rect[0], rect[1], rect[2], rect[3]), opacity=ly.opacity, rotation=ly.rotation)

    info = probe_media(spec.src)
    if info["kind"] != "image":
        raise ValueError(f"Overlay supports images only in MVP, got {info['kind']}")

    clip = load_image_clip(spec.src)
    placed = compute_rect((info["width"], info["height"]), rect, mode=ly.mode)
    warn_if_upscale_core((info["width"], info["height"]), placed, limit=1.5)
    return position_clip(clip, placed, opacity=ly.opacity, rotation=ly.rotation).with_duration(scene_duration)

def build_special(spec: GraphicSpec, meta: Meta, scene_duration: float) -> Optional[VideoClip]:
    """
    Placeholder: SVG/video alpha… chưa hỗ trợ ở MVP.
    """
    logging.warning("Special media not supported in MVP: %s", spec)
    return None

# =========================
# Compose
# =========================

def compose_scene(bg: VideoClip,
                illustrations: list[VideoClip],
                presenter: Optional[VideoClip],
                overlays: list[VideoClip],
                canvas_size: Tuple[int, int]) -> CompositeVideoClip:
    """
    Ghép theo thứ tự: background → illustrations → presenter → overlays.
    """
    layers: List[VideoClip] = []
    if bg: layers.append(bg)
    layers.extend(illustrations or [])
    if presenter: layers.append(presenter)
    layers.extend(overlays or [])
    return CompositeVideoClip(layers, size=canvas_size) #FIXME: compose không thuộc quản lý của graphics -> Move to Timeline