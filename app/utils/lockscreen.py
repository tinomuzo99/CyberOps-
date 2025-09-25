import os
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from .qr_utils import make_qr

# Simple generator for a phone lock-screen PNG: name + top allergy + QR

def generate_lockscreen_png(
    full_name: str,
    top_allergy: str,
    qr_url: str,
    out_path: str = "data/emergency_lockscreen.png",
    canvas=(1080, 1920),
    font_path: Optional[str] = None,
):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    W, H = canvas
    img = Image.new("RGB", (W, H), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font_title = ImageFont.truetype(font_path or "/System/Library/Fonts/SFNS.ttf", 80)
        font_text = ImageFont.truetype(font_path or "/System/Library/Fonts/SFNS.ttf", 50)
    except Exception:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # Header
    draw.text((60, 80), "EMERGENCY INFO", font=font_title, fill=(200, 0, 0))
    draw.text((60, 200), full_name, font=font_text, fill=(0, 0, 0))
    draw.text((60, 280), f"Allergy: {top_allergy}", font=font_text, fill=(0, 0, 0))

    # QR
    qr_png = make_qr(qr_url)
    import io
    qr_img = Image.open(io.BytesIO(qr_png)).convert("RGB")
    qr_size = 700
    qr_img = qr_img.resize((qr_size, qr_size))
    img.paste(qr_img, (int((W - qr_size) / 2), 500))

    draw.text((60, 1300), "Scan for emergency profile", font=font_text, fill=(0, 0, 0))

    img.save(out_path, format="PNG")
    return out_path
