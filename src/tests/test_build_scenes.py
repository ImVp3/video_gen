from tools.timeline.builder import build_scene
from tools.schema.dataclass import Meta


meta = Meta(width=1920, height=1080, font_type="sans")
scene = build_scene(
    meta=meta,
    scene_id="L07_Definition_Card",
    scene_type="definition_card",
    start=0.0,
    duration=6.0,
    background={"color": "#0b1629"},
    slots=[
        {
            "slot_id": "term",
            "rect": [160, 220, 800, 180],
            "style": {"color": "#e2e8f0"},
            "font": {"sans": "/path/to/Inter.ttf"},
            "payload": "Computational Thinking",
            "align": "left",
        },
        {
            "slot_id": "definition",
            "rect": [160, 420, 1240, 500],
            "style": {"color": "#cbd5e1", "interline": 8},
            "font": {"sans": "D:/ThienPV/code/demo_v2/assets/font/Inter/Inter-VariableFont_opsz,wght.ttf"},
            "payload": [
                "Phân rã bài toán",
                "Nhận diện mẫu",
                "Trừu tượng hoá",
                "Thiết kế thuật toán",
            ],
        },
    ],
    graphics=[
        {
            "role": "illustration",
            "src": "/assets/icons/brain.png",
            "layout": {"rect": [1460, 260, 300, 300], "mode": "fit", "snap_safe": True},
            "meta": {"src_size": [512, 512]},  # nếu biết kích thước gốc
        },
        {
            "role": "overlay",
            "color": "#ffffff20",
            "layout": {"rect": [140, 200, 1280, 760], "mode": "cover", "snap_safe": True},
            "meta": {"kind": "rounded_rect", "radius": 24}
        }
    ],
    presenter={
        "src": "/assets/presenter/circle_avatar.mp4",
        "rect": [1496, 760, 320, 320],
        "shape": "circle",
        "layer": 20
    }
)
def run():
    print(scene)