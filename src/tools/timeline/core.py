from __future__ import annotations
from tools.schema.dataclass import (
    Scene, TextSpec, GraphicSpec, PresenterSpec, Meta, MotionSpec, Rect, Style, Fonts, Layout
)
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Union, Tuple
from tools.geometry.core import snap_to_safe, fit_into_rect, place_in_rect, warn_if_upscale


def _require(cond: bool, msg: str):
    if not cond:
        raise ValueError(msg)

# z gợi ý theo vai trò (role)
_ROLE_DEFAULT_Z = {
    "background": 0,
    "illustration": 5,
    "overlay": 30,
    "special": 40,
}

def _normalize_fonts(d: Optional[dict]) -> Fonts:
    """
    Chuyển đổi dict thành Fonts, đảm bảo các trường bắt buộc.
    """
    if d is None:
        return Fonts()
    return Fonts(
        sans=d.get("sans"),
        mono=d.get("mono")
    )

def _normalize_style(d: Optional[dict]) -> Style:
    """
    Chuyển đổi dict thành Style, đảm bảo các trường bắt buộc.
    """
    if d is None:
        return Style()
    return Style(
        color=d.get("color", "#ffffff"),
        stroke_color= d.get("stroke_color", "#000000"),
        stroke_width=d.get("stroke_width", 0),
        opacity=d.get("opacity", 1.0),
        pad= d.get("pad", 0),
        interline= d.get("underline", 4),
        baseline_pad_pct= d.get("baseline_pad_pct", 0.32),
        top_pad_pct= d.get("top_pad_pct", 0.1),
    )
def _normalize_layout(d: Optional[dict]) -> Meta:
    """
    Chuyển đổi dict thành Layout, đảm bảo các trường bắt buộc.
    """
    rect = d.get("rect")
    _require(rect is not None and len(rect) == 4, "Layout rect must be a 4-tuple (x, y, w, h)")
    return Layout(
        rect=Rect(*rect),
        mode=d.get("mode", "fit"),
        align=d.get("align", "center"),
        rotation=d.get("rotation", 0.0),
        opacity=d.get("opacity", 1.0),
        snap_safe=d.get("snap_safe", True)
    )
def _apply_graphic_layout(
    layout: Layout,
    src_wh: Optional[Tuple[int, int]] = None,
    meta: Optional[Meta] = None
) -> Layout:
    rect = snap_to_safe(layout.rect, meta) if layout.snap_safe else layout.rect
    if src_wh:
        sw, sh = src_wh
        dst_rect = fit_into_rect(rect, (sw, sh), mode=layout.mode)
        warn_if_upscale(src_wh, dst_rect, limit=1.5)
        rect = dst_rect
    return Layout(
        rect=rect,
        mode=layout.mode,
        align=layout.align,
        rotation=layout.rotation,
        opacity=layout.opacity,
        snap_safe=layout.snap_safe
    )
def _normalize_graphics (items: List[Dict[str, Any]], meta: Optional[Meta] = None) -> List[GraphicSpec]:
    if not items:
        return []
    out: List[GraphicSpec] = []
    for item in items:
        role = item.get("role", "illustration")
        _require(role in _ROLE_DEFAULT_Z, f"Invalid role: {role}. Must be one of {_ROLE_DEFAULT_Z.keys()}")
        layout = _normalize_layout(item.get("layout"))
        
        src_wh: Optional[Tuple[int, int]] = None
        meta_dict = item.get("meta") or {}
        if isinstance(meta_dict.get("size"), (list, tuple)) and len(meta_dict["size"]) == 2:
            sw,sh = tuple(meta_dict["size"])
            try:
                sw_i = int(sw)
                sh_i = int(sh)
                if sw_i > 0 and sh_i > 0:
                    src_wh = (sw_i, sh_i)
            except Exception:
                src_wh = None
        if layout:
            layout = _apply_graphic_layout(layout, src_wh, meta)
        z = item.get("z_hint", _ROLE_DEFAULT_Z[role])
        out.append(
            GraphicSpec(
                role=role,
                src=item.get("src"),
                color=item.get("color"),
                layout=layout,
                z_hint=z,
                loop=item.get("loop", False),
                trim=item.get("trim") if item.get("trim") else None,
                meta=meta_dict
            )
        )
    return out
def _normalize_texts(items: List[Dict[str, Any]], meta: Optional[Meta] = None) -> List[TextSpec]:
    if not items:
        return []
    out: List[TextSpec] = []
    for item in items:
        slot_id = item.get("slot_id")
        _require(slot_id, "TextSpec must have a slot_id")
        style = _normalize_style(item.get("style"))
        rect = item.get("rect")
        _require(rect is not None and len(rect) == 4, "TextSpec rect must be a 4-tuple (x, y, w, h)")
        font = _normalize_fonts(item.get("font"))
        payload = item.get("payload", "")
        motion = item.get("motion")
        layer = item.get("layer", 10)
        align = item.get("align", "left")
        
        out.append(
            TextSpec(
                slot_id=slot_id,
                style=style,
                rect=Rect(*rect),
                font=font,
                payload=payload,
                motion=motion,
                layer=layer,
                align=align
            )
        )
    return out

def _normalize_presenter(item: Optional[Dict[str, Any]], meta: Meta) -> Optional[PresenterSpec]:
    if not item:
        return None
    _require("src" in item, "PresenterSpec must have a 'src' field")
    _require("rect" in item, "PresenterSpec must have a 'rect' field")
    rect = snap_to_safe(tuple(item["rect"]), meta)
    return PresenterSpec(
        src=item["src"],
        rect=Rect(*rect),
        shape=item.get("shape", "circle"),
        layer=item.get("layer", 20)
    )