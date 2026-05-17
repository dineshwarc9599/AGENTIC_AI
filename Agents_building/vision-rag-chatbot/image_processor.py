"""
image_processor.py
Smart image resizing to minimise token cost while preserving diagram clarity.

Gemini Vision pricing (tokens):
  Low  detail: 65  tokens  (max 512×512)
  High detail: varies, ~170 tokens per 512×512 tile
  
We target ≤ 1024px on the longest side for diagrams/architectures while
keeping quality high enough for text OCR within the image.
"""

from PIL import Image
from typing import Tuple, Dict
import io


class ImageProcessor:
    # Max dimensions — balanced for quality vs token cost
    MAX_LONG_SIDE = 1024     # px — safe for most diagrams
    MAX_SHORT_SIDE = 768     # px
    QUALITY = 90             # JPEG quality for re-encoding

    def smart_resize(self, img: Image.Image) -> Tuple[Image.Image, Dict]:
        """
        Resize image to cap token usage while keeping diagram text legible.
        Returns (resized_pil_image, info_dict).
        """
        original_size = img.size  # (W, H)
        w, h = original_size

        # Convert to RGB if needed (RGBA, P, etc.)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        scale = 1.0
        if w > self.MAX_LONG_SIDE or h > self.MAX_LONG_SIDE:
            scale = self.MAX_LONG_SIDE / max(w, h)

        new_w = int(w * scale)
        new_h = int(h * scale)

        if scale < 1.0:
            img = img.resize((new_w, new_h), Image.LANCZOS)

        reduction = f"{(1 - scale**2)*100:.0f}% smaller" if scale < 1.0 else "no resize needed"

        info = {
            "original": f"{w}×{h}",
            "resized":  f"{new_w}×{new_h}",
            "reduction": reduction,
            "scale": scale,
        }
        return img, info

    def to_bytes(self, img: Image.Image, fmt: str = "JPEG") -> bytes:
        buf = io.BytesIO()
        img.save(buf, format=fmt, quality=self.QUALITY)
        return buf.getvalue()

    @staticmethod
    def estimate_tokens(img: Image.Image) -> int:
        """
        Rough token estimate for a PIL image sent to Gemini.
        Formula: (W * H) / (512 * 512) * 170  (high-detail tiles)
        """
        w, h = img.size
        tiles = (w / 512) * (h / 512)
        return max(65, int(tiles * 170))