
from typing import Union
import os
from moviepy import VideoClip, CompositeVideoClip

def render_clip(
    clip: Union[VideoClip, CompositeVideoClip],
    output_path: str,
    fps: int = 30,
    codec: str = "libx264",
    bitrate: str = "4000k",
    audio: bool = True,
    preset: str = "medium",
    threads: int = 4,
    verbose: bool = True
) -> None:
    """
    Render một MoviePy clip ra file video/gif.

    Args:
        clip (VideoClip | CompositeVideoClip): Clip đầu vào.
        output_path (str): Đường dẫn file xuất (mp4 hoặc gif).
        fps (int, optional): Frames per second. Mặc định 30.
        codec (str, optional): Codec video (vd: libx264, libx265, vp9).
        bitrate (str, optional): Bitrate video (vd: 4000k).
        audio (bool, optional): Có xuất audio hay không.
        preset (str, optional): Preset ffmpeg (ultrafast, superfast, fast, medium, slow).
        threads (int, optional): Số luồng render.
        verbose (bool, optional): Có in log hay không.
    """

    ext = os.path.splitext(output_path)[1].lower()
    if ext == ".gif":
        clip.write_gif(output_path, fps=fps, program="ffmpeg", logger=verbose)
    else:
        clip.write_videofile(
            output_path,
            fps=fps,
            codec=codec,
            bitrate=bitrate,
            audio=audio,
            preset=preset,
            threads=threads,
        )
    if verbose:
        print(f"✅ Render hoàn tất: {output_path}")
