import os
from typing import Tuple
import numpy as np
from PIL import Image, ImageDraw
from moviepy import vfx, CompositeVideoClip, ImageClip, ColorClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import VideoClip
from moviepy.video.fx.Crop import Crop
from moviepy.video.fx.MaskColor import MaskColor
from tools.schema.dataclass import Rect

def _square_center_crop(clip: VideoClip, face_bias: float = 0.45) -> VideoClip:
    W, H = clip.w, clip.h
    if W == H: return clip
    side = min(W, H)
    x1 = (W - side) / 2
    y_center = H * face_bias
    y1 = max(0, min(H - side, y_center - side/2))
    crop = Crop(x1=x1, y1=y1, width=side, height=side)
    return crop.apply(clip)
def _circle_mask(d: int):
    """Mask tròn 0..1 (ismask=True)."""
    im = Image.new("L", (d, d), 0)
    ImageDraw.Draw(im).ellipse([0,0,d,d], fill=255)
    arr = (np.array(im).astype("float32") / 255.0)
    return ImageClip(arr, is_mask=True)

def remove_green_background(src_or_clip,
                            chroma_color=(0,255,0),
                            thr: int = 40,       # 0..255
                            stiffness: int = 3   # “gắt”/độ mềm mép
                            ) -> VideoClip:
    """
    Xóa nền xanh bằng Effect API v2.
    - src_or_clip: đường dẫn video/ảnh hoặc clip.
    - chroma_color: màu xanh cần key (R,G,B).
    """
    if hasattr(src_or_clip, "get_frame"):
        clip = src_or_clip
    else:
        ext = os.path.splitext(str(src_or_clip).lower())[1]
        if ext in (".mp4",".mov",".mkv",".webm",".avi"):
            clip = VideoFileClip(src_or_clip)
        else:
            im = Image.open(src_or_clip).convert("RGB")
            clip = ImageClip(np.array(im)).with_duration(1)

    eff = MaskColor(color=chroma_color, threshold=thr, stiffness=int(stiffness)).copy()
    keyed = clip.with_effects([eff])   # keyed có .mask; áp mask tự động
    return keyed
