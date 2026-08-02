import io
import pytest
from PIL import Image
from app.ai.visual_verifier import visual_verifier


def create_test_image_bytes(pattern: str = "rect") -> bytes:
    from PIL import ImageDraw

    img = Image.new("RGB", (100, 100), color="white")
    draw = ImageDraw.Draw(img)
    if pattern == "rect":
        draw.rectangle([10, 10, 50, 90], fill="black")
    else:
        draw.ellipse([50, 10, 90, 90], fill="black")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_perceptual_hash_computation():
    img1 = create_test_image_bytes("rect")
    img2 = create_test_image_bytes("rect")
    hash1 = visual_verifier.compute_perceptual_hash(img1)
    hash2 = visual_verifier.compute_perceptual_hash(img2)

    assert len(hash1) == 16
    assert hash1 == hash2


def test_different_images_produce_different_hashes():
    img1 = create_test_image_bytes("rect")
    img2 = create_test_image_bytes("circle")
    hash1 = visual_verifier.compute_perceptual_hash(img1)
    hash2 = visual_verifier.compute_perceptual_hash(img2)

    assert hash1 != hash2
