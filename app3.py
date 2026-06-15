from PIL import Image
import io

def process_image(
    image_file,
    width,
    height,
    bg_color,
    output_format,
    quality
):
    image = Image.open(image_file).convert("RGBA")

    background = Image.new(
        "RGBA",
        image.size,
        bg_color
    )

    merged = Image.alpha_composite(
        background,
        image
    )

    resized = merged.resize(
        (width, height)
    )

    if output_format in ["JPG", "JPEG"]:
        resized = resized.convert("RGB")

    img_bytes = io.BytesIO()

    save_format = (
        "JPEG"
        if output_format == "JPG"
        else output_format
    )

    resized.save(
        img_bytes,
        format=save_format,
        quality=quality
    )

    img_bytes.seek(0)

    return img_bytes yah code kam kar raha kuch feature add karny hai
