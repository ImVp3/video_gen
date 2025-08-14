from .core import _require, _normalize_graphics, _normalize_texts, _normalize_presenter
from tools.schema.dataclass import Meta, TextSpec, PresenterSpec, GraphicSpec, Scene, Rect
from typing import Optional, Literal, List, Tuple
from tools.geometry.core import place_in_rect
def build_scene (
    *,
    meta: Meta, 
    scene_id: str,
    scene_type: str,
    start: float,
    duration: float,
    background: dict,
    slots: list[TextSpec],
    graphics: list[GraphicSpec],
    presenter: Optional[PresenterSpec] = None,
    transition_out: dict | None = None,
) -> Scene:
    """
    Tạo một Scene với các thông tin đã cho.
    
    Args:
        meta: Thông tin canvas và safe margins.
        scene_id: ID của Scene.
        scene_type: Loại của Scene (ví dụ: "intro", "content", "outro").
        start: Thời gian bắt đầu của Scene (tính bằng giây).
        duration: Thời gian kéo dài của Scene (tính bằng giây).
        background: Thông tin về nền của Scene.
        slots: Danh sách các TextSpec cho các slot văn bản.
        graphics: Danh sách các GraphicSpec cho các đồ họa.
        presenter: Thông tin về người trình bày (nếu có).
        transition_out: Thông tin về hiệu ứng chuyển cảnh ra ngoài (nếu có).

    Returns:
        Một đối tượng Scene đã được tạo.
    """
    _require(duration >0, "Duration must be greater than 0")
    _require(start >= 0, "Start time must be non-negative")
    _require(
        any(k in background for k in ["color", "video", "image"]),
        "Background must contain at least one of 'color', 'video', or 'image'"
    )
    text_norms = _normalize_texts(slots or [], meta)
    graphic_norms = _normalize_graphics(graphics or [], meta)
    presenter_norm = _normalize_presenter(presenter, meta) if presenter else None
    for t in text_norms:
        x,y,w,h = t.rect
        _require(w > 0 and h > 0, f"TextSpec {t.slot_id} must have positive width and height")
    for g in graphic_norms:
        if g.layout:
            gx, gy, gw, gh = g.layout.rect
            _require(gw >0 and gh > 0, f"GraphicSpec {g.src} must have positive width and height")
    if presenter_norm:
        px, py, pw, ph = presenter_norm.rect
        _require(pw > 0 and ph > 0, f"PresenterSpec {presenter_norm.src} must have positive width and height")
    return Scene(
        id=scene_id,
        type=scene_type,
        start=start,
        duration=duration,
        background=background,
        slots=text_norms,
        graphics=graphic_norms,
        presenter=presenter_norm,
        transition_out=transition_out
    )
    
# Neo text -> cho renderer
def compute_text_anchor_rect(dst_rect: Rect, 
                                text_wh: Tuple[int, int], 
                                align: Literal["left", "center", "right"]
                            ) -> Rect:
    ax, cy = place_in_rect(dst_rect, align)
    tw, th = text_wh
    if align == "left":
        x = ax
    elif align == "center":
        x = ax - tw // 2
    else:  # right
        x = ax - tw
    y = cy - th // 2
    return Rect(x, y, tw, th)
