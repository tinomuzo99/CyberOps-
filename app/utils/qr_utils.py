import io
import qrcode


def make_qr(data: str) -> bytes:
    qr = qrcode.QRCode(version=2, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
