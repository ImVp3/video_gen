def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def _round_i(v: float) -> int:
    return int(round(v))