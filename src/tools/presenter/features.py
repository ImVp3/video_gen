from typing import Tuple
from moviepy import VideoClip, VideoFileClip, ColorClip, CompositeVideoClip
from tools.schema.dataclass import Rect
from .core import _square_center_crop, _circle_mask, remove_green_background
from utils import top_colors_first_frame

def build_avatar(src: str, 
                rect: Rect, 
                canvas_size=(1920,1080),
                with_bg: bool = True, 
                face_bias: float = 0.45,
                bg_opacity: float = 0.5,
                chroma_color : Tuple[int,int,int]|None|str = "auto",
) -> VideoClip:
    """
    Video -> avatar tròn đặt vào rect trên canvas_size.
    - rect = (x,y,w,h), thực tế D = min(w,h).
    - with_bg: thêm vòng tròn đen mờ phía sau (mask tròn + opacity).
    """
    x, y, w, h = rect
    D = int(min(w, h))

    base = VideoFileClip(src)
    dur  = base.duration

    if chroma_color: 
        if chroma_color == "auto":
            chroma_color = top_colors_first_frame(base)[0]["rgb"]    
        base = remove_green_background(base, chroma_color=chroma_color)
    # 1) crop vuông + resize về D×D
    sq   = _square_center_crop(base, face_bias=face_bias).resized((D, D))
    avatar = sq.with_position((x, y))

    layers = []

    # 2) nền tròn mờ (ColorClip đen + mask tròn + opacity)
    if with_bg:
        black = ColorClip((D, D), color=(0,0,0)).with_duration(dur).with_opacity(bg_opacity)
        black = black.with_position((x, y))
        layers.append(black)

    layers.append(avatar)

    # 4) trả về composite kích thước canvas (quan trọng để preview không “đen”)
    return CompositeVideoClip(layers, size=canvas_size)

def build_circle_avatar(src: str, rect: Rect, canvas_size=(1920,1080),
                        with_bg: bool = True, face_bias: float = 0.45,
                        bg_opacity: float = 0.5) -> VideoClip:
    """
    Video -> avatar tròn đặt vào rect trên canvas_size.
    - rect = (x,y,w,h), thực tế D = min(w,h).
    - with_bg: thêm vòng tròn đen mờ phía sau (mask tròn + opacity).
    """
    x, y, w, h = rect
    D = int(min(w, h))

    base = VideoFileClip(src)
    dur  = base.duration

    # 1) crop vuông + resize về D×D
    sq   = _square_center_crop(base, face_bias=face_bias).resized((D, D))

    # 2) mask tròn cho avatar
    mask = _circle_mask(D).with_duration(dur)
    avatar = sq.with_mask(mask).with_position((x, y))

    layers = []

    # 3) nền tròn mờ (ColorClip đen + mask tròn + opacity)
    if with_bg:
        black = ColorClip((D, D), color=(0,0,0)).with_duration(dur).with_opacity(bg_opacity)
        black = black.with_mask(mask)                # giới hạn trong hình tròn
        black = black.with_position((x, y))
        layers.append(black)

    layers.append(avatar)

    # 4) trả về composite kích thước canvas (quan trọng để preview không “đen”)
    return CompositeVideoClip(layers, size=canvas_size)