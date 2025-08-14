from typing import Literal, Tuple
import logging
from utils import _clamp, _round_i
from tools.schema.dataclass import Fonts, Style,Meta, Rect

# ---------- 1) snap_to_safe ----------
def snap_to_safe(rect: Rect, meta: Meta) -> Rect:
    """
    Kẹp rect vào *title-safe box* theo meta.title_area.
    Lưu ý: chỉ tịnh tiến (không co giãn). Nếu rect lớn hơn vùng title-safe,
    nó sẽ bám mép trái/trên của title-safe và có thể tràn ra ngoài title-safe,
    nhưng vẫn luôn nằm *trong canvas*.

    Mẹo: nếu muốn kẹp theo action-safe, có thể truyền Meta với title_area = action_area
    (vd: Meta(w,h,title_area=meta.action_area, action_area=meta.action_area)).

    Args:
        rect: (x, y, w, h) theo px.
        meta: thông số canvas/safe.

    Returns:
        Rect đã kẹp.
    """
    x, y, w, h = rect
    cw, ch = meta.width, meta.height

    # Tính title-safe box (theo tỷ lệ biên mỗi cạnh)
    m = meta.title_area
    safe_left   = _round_i(cw * m)
    safe_right  = cw - safe_left
    safe_top    = _round_i(ch * m)
    safe_bottom = ch - safe_top

    # Nếu rect lớn hơn vùng title-safe, ta vẫn giữ w/h
    # và chỉ đảm bảo không vượt canvas
    safe_w = max(0, safe_right - safe_left)
    safe_h = max(0, safe_bottom - safe_top)

    if w > safe_w:
        # Không thể hoàn toàn nằm trong title-safe; bám mép trái title-safe
        x_new = safe_left
        # Nhưng vẫn phải đảm bảo không vượt canvas
        x_new = _round_i(_clamp(x_new, 0, cw - w))
    else:
        x_new = _round_i(_clamp(x, safe_left, safe_right - w))

    if h > safe_h:
        y_new = safe_top
        y_new = _round_i(_clamp(y_new, 0, ch - h))
    else:
        y_new = _round_i(_clamp(y, safe_top, safe_bottom - h))

    return (x_new, y_new, _round_i(w), _round_i(h))


# ---------- 2) fit_into_rect ----------
def fit_into_rect(src_w: int, src_h: int, dst_rect: Rect, mode: str = "fit") -> Rect:
    """
    Tính kích thước & vị trí *giữa* dst_rect để đặt nội dung theo tỉ lệ,
    không méo hình.

    - mode="fit": toàn bộ nội dung nhìn thấy, có thể có viền trống (contain).
    - mode="cover": lấp đầy dst_rect, có thể crop phần thừa.

    Trả về rect mới (x, y, w, h) đã căn giữa trong dst_rect.

    Lưu ý: Hàm này *không* cắt clip; việc mask/crop nên do renderer xử lý
    dựa trên dst_rect nếu mode="cover".
    """
    dx, dy, dw, dh = dst_rect
    if src_w <= 0 or src_h <= 0 or dw <= 0 or dh <= 0:
        return (dx, dy, 0, 0)

    ar_src = src_w / float(src_h)
    ar_dst = dw / float(dh)

    if mode not in ("fit", "cover"):
        mode = "fit"

    if mode == "fit":
        scale = min(dw / src_w, dh / src_h)
    else:  # cover
        scale = max(dw / src_w, dh / src_h)

    w = src_w * scale
    h = src_h * scale
    # căn giữa trong dst_rect
    x = dx + (dw - w) / 2.0
    y = dy + (dh - h) / 2.0

    # làm tròn & đảm bảo không vượt hoàn toàn khỏi canvas con
    w_i = max(1, _round_i(w))
    h_i = max(1, _round_i(h))
    x_i = _round_i(x)
    y_i = _round_i(y)

    return (x_i, y_i, w_i, h_i)

# ---------- 3) place_in_rect ----------
def place_in_rect(dst_rect: Rect, align: Literal["left", "center", "right"]) -> Tuple[int, int]:
    """
    Trả về *điểm neo* (anchor_x, center_y) bên trong dst_rect theo căn lề ngang:
    - 'left'   -> anchor_x = left
    - 'center' -> anchor_x = center_x
    - 'right'  -> anchor_x = right

    Y luôn là tâm dọc của dst_rect (center_y).
    Khi đặt một phần tử có bề rộng w', bạn có thể tính x-left như sau:
    - align=='left'   : x_left = anchor_x
    - align=='center' : x_left = anchor_x - w'/2
    - align=='right'  : x_left = anchor_x - w'
    """
    x, y, w, h = dst_rect
    cy = _round_i(y + h / 2.0)
    if align == "center":
        ax = _round_i(x + w / 2.0)
    elif align == "right":
        ax = _round_i(x + w)
    else:
        ax = _round_i(x)
    return ax, cy

# ---------- 4) warn_if_upscale ----------
def warn_if_upscale(src_wh: Tuple[int, int], dst_rect: Rect, limit: float = 1.5) -> None:
    """
    Cảnh báo (logging.warning) nếu tỉ lệ phóng đại vượt ngưỡng.
    Dùng quy ước scale ~ max(dst_w/src_w, dst_h/src_h) (an toàn cho cả fit/cover).

    Args:
        src_wh: (src_w, src_h) kích thước nội dung gốc (px).
        dst_rect: (x, y, w, h) kích thước mục tiêu (px).
        limit: ngưỡng cảnh báo (mặc định 1.5 = 150%).
    """
    sw, sh = src_wh
    _, _, dw, dh = dst_rect
    if sw <= 0 or sh <= 0 or dw <= 0 or dh <= 0:
        return
    scale = max(dw / float(sw), dh / float(sh))
    if scale > limit:
        logging.warning(
            "Upscale factor %.2fx > %.2fx (src=%sx%s → dst=%sx%s). Nguy cơ mờ.",
            scale, limit, sw, sh, dw, dh
        )