from __future__ import annotations
import re, colorsys
from PIL import ImageColor, Image
from typing import Union, List, Dict, Optional,Dict, Tuple
import numpy as np
from moviepy import VideoFileClip

def top_colors_first_frame(
    video: Union[str, "VideoFileClip"],
    top_k: int = 10,
    quantize: int = 0,
    resize_to: Optional[int] = None,
    return_hex: bool = True,
) -> List[Dict]:
    """
    Lấy frame đầu (t=0) và trả về top_k màu xuất hiện nhiều nhất.

    Params
    ------
    video       : đường dẫn hoặc VideoFileClip (MoviePy v2).
    top_k       : số màu cần lấy (mặc định 10).
    quantize    : bước lượng tử hoá kênh màu (0 = đếm màu chính xác).
                  Ví dụ 16 -> gom màu theo bậc 16 (giảm nhiễu).
    resize_to   : nếu set (vd 720), sẽ downscale cạnh dài của frame
                  về <= giá trị này để tăng tốc đếm (không bắt buộc).
    return_hex  : có trả kèm mã HEX hay không.

    Returns
    -------
    List[Dict] với mỗi phần tử:
      {
        "rgb": (r, g, b),
        "hex": "#RRGGBB",   # nếu return_hex=True
        "count": <số pixel>,
        "ratio": <tỷ lệ pixel trên toàn frame>
      }
    """
    opened_here = False
    clip = video
    if isinstance(video, str):
        clip = VideoFileClip(video)
        opened_here = True
    try:
        frame = clip.get_frame(0.0)  # (H,W,3|4)
    finally:
        if opened_here:
            clip.close()

    # Chuẩn hoá về RGB uint8
    if frame.ndim != 3 or frame.shape[2] < 3:
        raise ValueError("Frame không hợp lệ (cần dạng HxWx3 hoặc HxWx4).")
    frame = frame[:, :, :3]
    if frame.dtype != np.uint8:
        # MoviePy đôi khi trả float [0..1]; chuẩn hoá về uint8
        if frame.max() <= 1.0:
            frame = np.clip(np.rint(frame * 255.0), 0, 255).astype(np.uint8)
        else:
            frame = np.clip(np.rint(frame), 0, 255).astype(np.uint8)

    # Tùy chọn downscale để tăng tốc
    if resize_to:
        h, w = frame.shape[:2]
        scale = resize_to / max(h, w) if max(h, w) > resize_to else 1.0
        if scale < 1.0:
            new_size = (int(w * scale), int(h * scale))
            frame = np.array(Image.fromarray(frame).resize(new_size, Image.BILINEAR), dtype=np.uint8)

    # Tùy chọn lượng tử hoá màu (gom cụm màu gần nhau)
    if quantize and quantize > 1:
        q = int(quantize)
        frame = (frame.astype(np.int16) // q) * q + q // 2
        frame = np.clip(frame, 0, 255).astype(np.uint8)

    # Đếm nhanh bằng numpy.unique trên dtype cấu trúc
    pixels = frame.reshape(-1, 3)
    dtype = np.dtype([("r", np.uint8), ("g", np.uint8), ("b", np.uint8)])
    structured = pixels.view(dtype)
    uniques, counts = np.unique(structured, return_counts=True)

    if counts.size == 0:
        return []

    # Lấy top_k bằng argpartition (O(n))
    k = min(top_k, counts.size)
    idx = np.argpartition(-counts, kth=k - 1)[:k]
    idx = idx[np.argsort(-counts[idx])]  # sắp xếp lại theo count giảm dần

    total = pixels.shape[0]
    results: List[Dict] = []
    for i in idx:
        r, g, b = int(uniques[i]["r"]), int(uniques[i]["g"]), int(uniques[i]["b"])
        cnt = int(counts[i])
        item: Dict[str, object] = {"rgb": (r, g, b), "count": cnt, "ratio": cnt / total}
        if return_hex:
            item["hex"] = f"#{r:02X}{g:02X}{b:02X}"
        results.append(item)

    return results


Number = Union[int, float]
RGB  = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
RGB_FUNC_RE  = re.compile(r"^rgba?\((.+)\)$", re.IGNORECASE)
HSL_FUNC_RE  = re.compile(r"^hsla?\((.+)\)$", re.IGNORECASE)
HSV_FUNC_RE  = re.compile(r"^hsva?\((.+)\)$", re.IGNORECASE)

def _clamp_byte(x: Number) -> int:
    return max(0, min(255, int(round(x))))

def _parse_channel(tok: str, base: int = 255) -> int:
    tok = tok.strip()
    if tok.endswith('%'):
        val = float(tok[:-1])
        return _clamp_byte(val * base / 100.0)
    return _clamp_byte(float(tok))

def _parse_alpha(tok: str) -> int:
    tok = tok.strip()
    if tok.endswith('%'):
        return _clamp_byte(float(tok[:-1]) * 255 / 100.0)
    # allow 0..1 or 0..255
    v = float(tok)
    if v <= 1.0:
        return _clamp_byte(v * 255)
    return _clamp_byte(v)

def _expand_hex(h: str) -> str:
    if len(h) == 3:   # rgb -> rrggbb
        return ''.join(c*2 for c in h)
    if len(h) == 4:   # rgba -> rrggbbaa
        return ''.join(c*2 for c in h)
    return h

def _parse_hex(s: str) -> RGBA:
    m = HEX_RE.match(s.strip())
    if not m:
        raise ValueError("Not a hex color")
    h = _expand_hex(m.group(1))
    if len(h) == 6:
        r = int(h[0:2], 16); g = int(h[2:4], 16); b = int(h[4:6], 16); a = 255
    elif len(h) == 8:
        r = int(h[0:2], 16); g = int(h[2:4], 16); b = int(h[4:6], 16); a = int(h[6:8], 16)
    else:
        raise ValueError("Invalid hex length")
    return (r, g, b, a)

def _split_args(argstr: str) -> list[str]:
    # supports commas or spaces or slashes e.g. "255 0 0 / 0.5"
    # Normalize separators
    argstr = argstr.replace('/', ' , ')
    parts = [p for p in re.split(r"[,\s]+", argstr.strip()) if p]
    return parts

def _parse_rgb_func(s: str) -> RGBA:
    m = RGB_FUNC_RE.match(s.strip())
    if not m:
        raise ValueError("Not rgb()/rgba()")
    parts = _split_args(m.group(1))
    if len(parts) not in (3,4):
        raise ValueError("rgb/rgba needs 3 or 4 components")
    r = _parse_channel(parts[0])
    g = _parse_channel(parts[1])
    b = _parse_channel(parts[2])
    a = _parse_alpha(parts[3]) if len(parts) == 4 else 255
    return (r,g,b,a)

def _parse_hsl_func(s: str) -> RGBA:
    m = HSL_FUNC_RE.match(s.strip())
    if not m:
        raise ValueError("Not hsl()/hsla()")
    parts = _split_args(m.group(1))
    if len(parts) not in (3,4):
        raise ValueError("hsl/hsla needs 3 or 4 components")
    # h can be deg (e.g. 120 or 120deg). s,l are %.
    htok = parts[0].strip().lower().replace('deg','')
    h = float(htok) % 360.0
    s = float(parts[1].strip().rstrip('%'))/100.0
    l = float(parts[2].strip().rstrip('%'))/100.0
    a = _parse_alpha(parts[3]) if len(parts)==4 else 255
    # colorsys uses HLS (h, l, s) in 0..1
    r, g, b = colorsys.hls_to_rgb(h/360.0, l, s)
    return (_clamp_byte(r*255), _clamp_byte(g*255), _clamp_byte(b*255), a)

def _parse_hsv_func(s: str) -> RGBA:
    m = HSV_FUNC_RE.match(s.strip())
    if not m:
        raise ValueError("Not hsv()/hsva()")
    parts = _split_args(m.group(1))
    if len(parts) not in (3,4):
        raise ValueError("hsv/hsva needs 3 or 4 components")
    htok = parts[0].strip().lower().replace('deg','')
    h = float(htok) % 360.0
    s = float(parts[1].strip().rstrip('%'))/100.0
    v = float(parts[2].strip().rstrip('%'))/100.0
    a = _parse_alpha(parts[3]) if len(parts)==4 else 255
    r, g, b = colorsys.hsv_to_rgb(h/360.0, s, v)
    return (_clamp_byte(r*255), _clamp_byte(g*255), _clamp_byte(b*255), a)

def _rgba_from_any(color: Union[str, Tuple[int,int,int], Tuple[int,int,int,int], int]) -> RGBA:
    # tuple
    if isinstance(color, tuple):
        if len(color) == 3:
            r,g,b = color; a = 255
        elif len(color) == 4:
            r,g,b,a = color
        else:
            raise ValueError("Tuple must have 3 or 4 elements")
        return (_clamp_byte(r), _clamp_byte(g), _clamp_byte(b), _clamp_byte(a))
    # int 0xRRGGBB or 0xRRGGBBAA (accept both)
    if isinstance(color, int):
        if color < 0:
            raise ValueError("Negative integer color not allowed")
        if color <= 0xFFFFFF:
            r = (color >> 16) & 255; g = (color >> 8) & 255; b = color & 255; a = 255
        else:
            r = (color >> 24) & 255; g = (color >> 16) & 255; b = (color >> 8) & 255; a = color & 255
        return (r,g,b,a)
    # string
    if isinstance(color, str):
        s = color.strip()
        # 1) hex (#rgb, #rgba, #rrggbb, #rrggbbaa)
        if HEX_RE.match(s):
            return _parse_hex(s)
        # 2) rgb()/rgba()
        try:
            return _parse_rgb_func(s)
        except ValueError:
            pass
        # 3) hsl()/hsla()
        try:
            return _parse_hsl_func(s)
        except ValueError:
            pass
        # 4) hsv()/hsva()
        try:
            return _parse_hsv_func(s)
        except ValueError:
            pass
        # 5) named colors or other strings Pillow understands (also supports "rgb(…)" and "hsl(…)" without alpha)
        try:
            r,g,b = ImageColor.getrgb(s)
            return (r,g,b,255)
        except Exception:
            pass
    raise TypeError(f"Unsupported color format: {color!r}")

def _to_hex_rgb(rgb: RGB) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def _to_hex_rgba(rgba: RGBA) -> str:
    r,g,b,a = rgba
    return "#{:02x}{:02x}{:02x}{:02x}".format(r,g,b,a)

def _rgb_to_hsl(rgb: RGB) -> Tuple[float,float,float]:
    r,g,b = [c/255.0 for c in rgb]
    h,l,s = colorsys.rgb_to_hls(r,g,b)  # note: hls
    # convert to HSL convention: (H, S, L) with percents
    return ( (h*360.0)%360.0, s*100.0, l*100.0 )

def _rgb_to_hsv(rgb: RGB) -> Tuple[float,float,float]:
    r,g,b = [c/255.0 for c in rgb]
    h,s,v = colorsys.rgb_to_hsv(r,g,b)
    return ( (h*360.0)%360.0, s*100.0, v*100.0 )

def _rgb_to_cmyk(rgb: RGB) -> Tuple[float,float,float,float]:
    r,g,b = [c/255.0 for c in rgb]
    k = 1 - max(r,g,b)
    if k == 1:
        return (0.0, 0.0, 0.0, 100.0)
    c = (1-r-k)/(1-k)
    m = (1-g-k)/(1-k)
    y = (1-b-k)/(1-k)
    return (c*100.0, m*100.0, y*100.0, k*100.0)

def convert_color(color: Union[str, Tuple[int,int,int], Tuple[int,int,int,int], int]) -> Dict[str, object]:
    """
    Nhận vào: tên màu, hex (#rgb/#rgba/#rrggbb/#rrggbbaa), rgb()/rgba(), hsl()/hsla(), hsv()/hsva(),
              tuple RGB/RGBA, hoặc int (0xRRGGBB / 0xRRGGBBAA)
    Trả về: dict đầy đủ các loại mã màu.
    """
    r,g,b,a = _rgba_from_any(color)

    hex_rgb  = _to_hex_rgb((r,g,b))
    hex_rgba = _to_hex_rgba((r,g,b,a))

    # ints
    int_rgb  = (r<<16) | (g<<8) | b            # 0xRRGGBB
    int_rgba = (r<<24) | (g<<16) | (b<<8) | a  # 0xRRGGBBAA

    # normalized
    rn, gn, bn, an = (r/255.0, g/255.0, b/255.0, a/255.0)

    # HSL / HSV (degrees, percents)
    hH, sH, lH = _rgb_to_hsl((r,g,b))
    hV, sV, vV = _rgb_to_hsv((r,g,b))

    # CMYK (percents)
    cC, mC, yC, kC = _rgb_to_cmyk((r,g,b))

    return {
        # base tuples
        "rgb": (r, g, b),
        "rgba": (r, g, b, a),

        # hex forms
        "hex": hex_rgb,          # #rrggbb
        "hexa": hex_rgba,        # #rrggbbaa

        # integer forms
        "int": int_rgb,          # 0xRRGGBB
        "int_rgba": int_rgba,    # 0xRRGGBBAA

        # normalized 0..1
        "rgb_norm": (rn, gn, bn),
        "rgba_norm": (rn, gn, bn, an),

        # HSL/HSLA (H in degrees 0..360, S/L in %, alpha 0..1)
        "hsl": (hH, sH, lH),
        "hsla": (hH, sH, lH, an),

        # HSV/HSVA (H in degrees 0..360, S/V in %, alpha 0..1)
        "hsv": (hV, sV, vV),
        "hsva": (hV, sV, vV, an),

        # CMYK in %
        "cmyk": (cC, mC, yC, kC),
    }
