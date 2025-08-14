from __future__ import annotations
from tools.schema.dataclass import Rect, Meta, GraphicSpec
from typing import Tuple, Literal, List
from functools import lru_cache
import os
import logging
from moviepy import VideoClip, ColorClip, VideoFileClip, ImageClip
from PIL import Image
import numpy as np
from tools.geometry.core import fit_into_rect, warn_if_upscale,snap_to_safe, place_in_rect
from utils import convert_color

@lru_cache(maxsize=128)
def probe_media(src: str) -> dict:
    """
    Trả về thông tin cơ bản của media:
    {kind: 'image'|'video'|'svg', width, height, has_alpha, duration}.
    """
    ext = os.path.splitext(src)[1].lower()
    if ext in (".png", ".jpg", ".jpeg", ".webp"):
        im = Image.open(src)
        width, height = im.size
        has_alpha = im.mode in ("RGBA", "LA")
        return {"kind": "image", "width": width, "height": height,
                "has_alpha": has_alpha, "duration": None}
    elif ext in (".mp4", ".mov", ".mkv", ".webm", ".avi"):
        clip = VideoFileClip(src)
        return {"kind": "video", "width": clip.w, "height": clip.h,
                "has_alpha": False, "duration": clip.duration}
    elif ext == ".svg":
        # SVG sẽ xử lý ở Phase-2
        return {"kind": "svg", "width": None, "height": None,
                "has_alpha": True, "duration": None}
    else:
        raise ValueError(f"Unsupported file type: {ext}")


@lru_cache(maxsize=64)
def load_image_clip(src: str) -> ImageClip:
    """
    Nạp PNG/JPG thành ImageClip (giữ alpha nếu có).
    """
    im = Image.open(src).convert("RGBA")
    arr = np.array(im)  # numpy sẽ dùng cho ImageClip
    return ImageClip(arr, transparent=True)


def load_video_clip(src: str) -> VideoFileClip:
    """
    Nạp video thành VideoFileClip.
    Phase-2: sẽ thêm trim/loop ở Wrapper.
    """
    return VideoFileClip(src)


def rasterize_svg(src: str, dpi: int = 192) -> ImageClip:
    """
    Phase-2: Chuyển SVG thành raster ImageClip.
    (Hiện tại chưa triển khai)
    """
    raise NotImplementedError("SVG rasterization chưa hỗ trợ ở MVP.")


# =========================
# 2. Transform & Quality
# =========================

def compute_rect(src_wh: Tuple[int, int],
                    dst_rect: Rect,
                    mode: Literal["fit", "cover"] = "fit") -> Rect:
    """
    Tính rect mới cho media theo fit/cover.
    """
    return fit_into_rect(src_wh[0], src_wh[1], dst_rect, mode=mode)


def position_clip(clip: VideoClip,
                    rect: Rect,
                    opacity: float = 1.0,
                    rotation: float = 0.0) -> VideoClip:
    """
    Resize/crop clip nếu cần, set vị trí (x,y), opacity, rotation.
    """
    x, y, w, h = rect
    clip = clip.resized((w, h))
    if rotation:
        clip = clip.rotated(rotation)
    if opacity < 1.0:
        clip = clip.with_opacity(opacity)
    return clip.with_position((x, y))


def warn_if_upscale_core(src_wh: Tuple[int, int],
                            dst_rect: Rect,
                            limit: float = 1.5) -> None:
    """
    Cảnh báo upscale > limit.
    """
    warn_if_upscale(src_wh, dst_rect, limit=limit)

def apply_policies(spec: GraphicSpec, meta: Meta) -> GraphicSpec:
    """
    Điền default & ép rule theo role:
    - background: default mode="cover", snap_safe=False
    - illustration: default mode="fit"
    - overlay: luôn snap_safe=True
    """
    if spec.layout is None:
        raise ValueError("GraphicSpec.layout is required")

    ly = spec.layout

    if spec.role == "background":
        if ly.mode not in ("fit", "cover"): ly.mode = "cover"
        ly.snap_safe = False
    elif spec.role == "overlay":
        ly.snap_safe = True
        if ly.mode not in ("fit", "cover"): ly.mode = "fit"
    else:  # illustration / special
        if ly.mode not in ("fit", "cover"): ly.mode = "fit"

    spec.layout = ly
    return spec

def validate_graphic_spec(spec: GraphicSpec, meta: Meta) -> List[str]:
    """
    Validate nhẹ ở wrapper: role/src/color/layout rect.
    Trả về danh sách lỗi dạng string (đủ cho MVP).
    """
    errors: List[str] = []
    if spec.role not in ("background", "illustration", "overlay", "special"):
        errors.append("role invalid")

    if spec.role == "background":
        if not spec.src and not spec.color:
            errors.append("background needs either src (image) or color")
    else:
        if not spec.src and not spec.color:
            errors.append("non-background needs src or color (shape overlay)")

    if spec.layout is None:
        errors.append("layout missing")
    else:
        x, y, w, h = spec.layout.rect
        if w <= 0 or h <= 0:
            errors.append("layout.rect width/height must be > 0")

    return errors
