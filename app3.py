import streamlit as st
from PIL import Image, ImageEnhance
import io

st.set_page_config(page_title="Studio Photo Editor", layout="wide")


# =========================
# ENHANCEMENT
# =========================
def enhance_image(img):
    img = ImageEnhance.Sharpness(img).enhance(1.5)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Brightness(img).enhance(1.1)
    return img


# =========================
# BACKGROUND
# =========================
def apply_background(img, bg_mode, bg_color):
    if bg_mode == "ON":
        background = Image.new("RGBA", img.size, bg_color)
        img = Image.alpha_composite(background, img.convert("RGBA"))
    return img


# =========================
# RESIZE
# =========================
def resize_image(img, mode, width, height):
    if mode == "Custom":
        return img.resize((int(width), int(height)))

    elif mode == "Passport":
        return img.resize((600, 600))

    elif mode == "ID Card":
        return img.resize((300, 300))

    elif mode == "A4":
        return img.resize((1080, 1350))

    return img


# =========================
# FILE SIZE COMPRESSOR
# =========================
def compress_image(img, target, unit, fmt):
    buffer = io.BytesIO()

    if unit == "KB":
        target_bytes = target * 1024
    elif unit == "MB":
        target_bytes = target * 1024 * 1024
    else:
        target_bytes = target * 1024 * 1024 * 1024

    quality = 95
    save_format = "JPEG" if fmt == "JPG" else fmt

    while quality > 10:
        buffer.seek(0)
        buffer.truncate()

        img.save(buffer, format=save_format, quality=quality, optimize=True)
        size = buffer.tell()

        if size <= target_bytes:
            break

        quality -= 5

    buffer.seek(0)
    return buffer


# =========================
# UI
# =========================
st.title("📸 STUDIO PHOTO EDITOR PRO")


# ================= INPUT =================
col1, col2 = st.columns(2)

with col1:
    upload = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

with col2:
    camera = st.camera_input("Take Photo")

img_file = camera if camera else upload


# ================= MAIN =================
if img_file:

    img = Image.open(img_file)

    # ================= FIXED PREVIEW =================
    st.subheader("🖼 Preview")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(img, caption="Original Image", width=300)

    # ================= ENHANCE =================
    st.subheader("✨ Enhancement")
    if st.checkbox("Enable Enhancement"):
        img = enhance_image(img)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(img, caption="Enhanced Image", width=300)

    # ================= RESIZE =================
    st.subheader("📏 Resize")

    resize_mode = st.selectbox(
        "Resize Mode",
        ["Custom", "Passport", "ID Card", "A4"]
    )

    col1, col2 = st.columns(2)
    with col1:
        width = st.number_input("Width", value=300)
    with col2:
        height = st.number_input("Height", value=300)

    img = resize_image(img, resize_mode, width, height)

    # ================= BACKGROUND =================
    st.subheader("🎨 Background")

    bg_mode = st.selectbox("Background", ["OFF", "ON"])

    bg_color = "#ffffff"
    if bg_mode == "ON":
        bg_color = st.selectbox(
            "Color",
            ["#ffffff", "#000000", "#ff0000", "#00ff00", "#0000ff", "#f5f5f5"]
        )

    img = apply_background(img, bg_mode, bg_color)

    # ================= DPI =================
    st.subheader("🖨 DPI")

    dpi_mode = st.selectbox(
        "DPI Mode",
        ["72 (Web)", "150 (Print)", "300 (High Quality)", "Custom"]
    )

    if dpi_mode == "Custom":
        dpi = st.number_input("Enter DPI", value=300)
    else:
        dpi = int(dpi_mode.split(" ")[0])

    # ================= OUTPUT =================
    st.subheader("⚙ Output Settings")

    fmt = st.selectbox("Format", ["JPG", "PNG"])
    quality = st.slider("Quality (JPG)", 10, 100, 90)

    # ================= FILE SIZE CONTROL =================
    st.subheader("📦 File Size Control")

    compress = st.checkbox("Enable Compression")

    target_size = None
    unit = None

    if compress:
        col1, col2 = st.columns(2)

        with col1:
            target_size = st.number_input("Target Size", value=100)

        with col2:
            unit = st.selectbox("Unit", ["KB", "MB", "GB"])

    # ================= PROCESS =================
    if st.button("🚀 Generate Image"):

        buffer = io.BytesIO()

        save_format = "JPEG" if fmt == "JPG" else fmt
        img_to_save = img.convert("RGB") if save_format == "JPEG" else img

        if compress:
            buffer = compress_image(img_to_save, target_size, unit, save_format)
        else:
            img_to_save.save(buffer, format=save_format, quality=quality if save_format == "JPEG" else None)
            buffer.seek(0)

        st.success("Image Ready 🎉")

        st.download_button(
            "⬇ Download Image",
            data=buffer,
            file_name=f"studio_output.{fmt.lower()}",
            mime=f"image/{fmt.lower()}"
        )
