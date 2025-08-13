import os
from moviepy import VideoClip, VideoFileClip

def get_video_resolution(path: str) -> tuple[int, int]:
    """Trả về (width, height) của video/ảnh."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    clip = VideoFileClip(path)
    w, h = clip.size
    clip.close()
    return int(w), int(h)
