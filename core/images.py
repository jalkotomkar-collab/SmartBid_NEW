"""Image helpers.

Uploaded images (product photos, the payment QR code) are resized, re-encoded as
JPEG and stored in the database as base64 text, so they persist wherever the
database does. Placeholder artwork ships in assets/placeholders/.
"""
import base64
import io

import streamlit as st
from PIL import Image, ImageOps

from . import db
from .config import PLACEHOLDER_DIR

MAX_SIDE = 1000
PRODUCT_PLACEHOLDER = "product_placeholder.jpg"


def save_upload(uploaded_file, max_side: int = MAX_SIDE, aspect: tuple | None = None) -> int:
    """Validate, resize and store an uploaded image. Returns the new image id.

    aspect=(4, 3) centre-crops to that ratio so product cards line up.
    """
    try:
        img = Image.open(uploaded_file)
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception:
        raise ValueError("That file could not be read as an image. Upload a JPG or PNG.")
    if aspect:
        target = aspect[0] / aspect[1]
        w, h = img.size
        if w / h > target:
            new_w = int(h * target)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / target)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))
    img.thumbnail((max_side, max_side))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=82, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return db.insert("INSERT INTO images (mime, data) VALUES (?, ?)", ("image/jpeg", encoded))


@st.cache_data(ttl=600, show_spinner=False)
def load_image(image_id: int) -> bytes | None:
    row = db.fetch_one("SELECT data FROM images WHERE id = ?", (image_id,))
    return base64.b64decode(row["data"]) if row else None


def product_image(image_id) -> bytes | str:
    """Bytes of the stored image, or the path of the placeholder if there is none."""
    if image_id:
        data = load_image(int(image_id))
        if data:
            return data
    return str(PLACEHOLDER_DIR / PRODUCT_PLACEHOLDER)


def delete_image(image_id) -> None:
    if image_id:
        db.execute("DELETE FROM images WHERE id = ?", (int(image_id),))
        load_image.clear()


@st.cache_data(show_spinner=False)
def data_uri(filename: str) -> str:
    """Inline a placeholder file as a data URI for use inside HTML blocks."""
    path = PLACEHOLDER_DIR / filename
    mime = "image/png" if path.suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
