from dataclasses import dataclass, field
from typing import Optional, Tuple, Union
from moviepy import VideoClip
from dataclasses import dataclass
from typing import Literal, Optional, Tuple,List, Union


# Type aliases
Rect = Tuple[int, int, int, int]  # (x, y, width, height)
Payload = Union[str, VideoClip]   # Either raw text or a video clip

@dataclass
class Fonts:
    """
    Font file paths for rendering text.
    """
    sans: Optional[str] = None  # Path to a sans-serif font (.ttf/.otf). None uses Pillow's default.
    mono: Optional[str] = None  # Path to a monospace font (.ttf/.otf). None uses Pillow's default.

@dataclass
class Style:
    """
    Text style configuration for rendering.
    """
    color: str = "white"                     # Text color
    stroke_color: Optional[str] = None       # Stroke (outline) color
    stroke_width: int = 0                    # Stroke width in pixels
    opacity: float = 1.0                     # Opacity (0–1)
    pad: int = 0                             # Padding for background (e.g., captions)
    interline: int = 4                       # Line spacing between wrapped lines
    baseline_pad_pct: float = 0.32           # Extra bottom padding ratio to avoid descender clipping
    top_pad_pct: float = 0.10                # Extra top padding ratio for symmetry


@dataclass(frozen=True)
class Meta:
    """Thông tin chung."""
    version:str = "1.0.0"
    width: int
    height: int
    title_area: float = 0.05   # 5% mỗi cạnh
    action_area: float = 0.025 # 2.5% mỗi cạnh
    font_type: Literal["sans", "mono"] = "sans" 
    
@dataclass
class MotionSpec:
    enter_type: Literal["fade","slide-up","none"] = "fade"
    enter_dur: float = 0.25
    exit_type: Literal["fade","none"] = "fade"
    exit_dur: float = 0.20
    delay: float = 0.0

# @dataclass
# class Slot:
#     slot_id: str
#     rect: Rect
#     align: Literal["left","center","right"] = "left"
#     text: Optional[str] = None
#     items: Optional[list[str]] = None
#     font: str = "Inter"
#     size: int = 32
#     weight: int = 700
#     color: str = "#ffffff"
#     motion: Optional[MotionSpec] = None
#     layer: int = 10
@dataclass
class TextSpec: # OPTIMIZE: Thêm điều khiển Font Weights
    slot_id: str
    style: Style
    rect: Rect
    font: Fonts
    payload: str| List[str]
    motion: Optional[MotionSpec] = None
    layer: int = 10
    align: Literal["left", "center", "right"] = "left"  
@dataclass
class GraphicSpec:
    src: str
    rect: Rect
    mode: Literal["fit","cover"] = "fit"
    caption: Optional[str] = None
    layer: int = 5
    motion: Optional[MotionSpec] = None

@dataclass
class PresenterSpec:
    src: str
    rect: Rect
    shape: Literal["circle","rect"] = "circle"
    layer: int = 20

@dataclass
class Scene:
    id: str; type: str; start: float; duration: float
    background: dict  # {"color": "..."} | {"video": "..."} | {"image": "..."}
    slots: list[TextSpec]
    graphics: list[GraphicSpec]
    presenter: Optional[PresenterSpec] = None
    transition_out: dict | None = None

@dataclass
class Timeline:
    meta: Meta
    scenes: list[Scene]

@dataclass
class Layout:
    rect: Rect
    mode: Literal["fit", "cover"] = "fit"
    align: Literal["left", "center", "right"] = "center"   # hiện chưa dùng ở core
    rotation: float = 0.0
    opacity: float = 1.0
    snap_safe: bool = True

@dataclass
class GraphicSpec:
    role: Literal["background", "illustration", "overlay", "special"]
    src: Optional[str] = None
    color: Optional[str] = None                 # dùng khi background/shape màu
    layout: Optional[Layout] = None
    z_hint: Optional[int] = None
    loop: bool = False                          # video (phase-2)
    trim: Optional[Tuple[float, float]] = None  # (start,dur) (phase-2)
    meta: Optional[dict] = None                 # chỗ mở rộng thêm