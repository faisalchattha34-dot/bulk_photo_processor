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
# ================= RESIZE =================
st.subheader("📏 Professional Resize Presets")

resize_mode = st.selectbox(
    "Choose Purpose",
    [
        "Custom",
        "NADRA CNIC (413 × 531)",
        "Job Application (300 × 300)",
        "Admission Form (600 × 600)",
        "CV Profile Picture (400 × 400)",
        "Passport Size (600 × 600)",
        "LinkedIn Profile (400 × 400)",
        "A4 Document (1080 × 1350)"
    ]
)

if resize_mode == "Custom":

    custom_mode = st.radio(
        "Size Input Method",
        ["Manual Width & Height", "Resolution Preset"]
    )

    if custom_mode == "Manual Width & Height":

        col1, col2 = st.columns(2)

        with col1:
            width = st.number_input(
                "Width (px)",
                min_value=1,
                value=300,
                key="custom_width"
            )

        with col2:
            height = st.number_input(
                "Height (px)",
                min_value=1,
                value=300,
                key="custom_height"
            )

    else:

        resolution = st.selectbox(
            "Select Resolution",
            [
                "300 × 300",
                "400 × 400",
                "413 × 531",
                "600 × 600",
                "800 × 800",
                "1080 × 1080",
                "1920 × 1080"
            ]
        )

        resolution = resolution.replace(" ", "")
        width, height = map(int, resolution.split("×"))

elif resize_mode == "NADRA CNIC (413 × 531)":
    width, height = 413, 531

elif resize_mode == "Job Application (300 × 300)":
    width, height = 300, 300

elif resize_mode == "Admission Form (600 × 600)":
    width, height = 600, 600

elif resize_mode == "CV Profile Picture (400 × 400)":
    width, height = 400, 400

elif resize_mode == "Passport Size (600 × 600)":
    width, height = 600, 600

elif resize_mode == "LinkedIn Profile (400 × 400)":
    width, height = 400, 400

elif resize_mode == "A4 Document (1080 × 1350)":
    width, height = 1080, 1350

st.success(f"Selected Resolution: {width} × {height} px")

img = img.resize((int(width), int(height)))


# =========================
# COMPRESSOR
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
st.subheader("📤 Input Section")

col1, col2 = st.columns(2)

with col1:
    upload = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

with col2:
    st.markdown("### 📸 Camera")

    # 🔥 FIX: compact camera using CSS
    st.markdown(
        """
        <style>
        div[data-testid="stCameraInput"] {
            width: 260px !important;
            margin: auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    camera = st.camera_input("Take Photo")

img_file = camera if camera else upload


# ================= MAIN =================
if img_file:

    img = Image.open(img_file)

    # ================= PREVIEW =================
    st.subheader("🖼 Preview + Enhancement")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📷 Original")
        st.image(img, width=300)

    with col2:
        st.markdown("### ✨ Enhanced")

        enhance = st.checkbox("Enable Enhancement", value=True)

        if enhance:
            preview_img = enhance_image(img)
        else:
            preview_img = img

        st.image(preview_img, width=300)

    img = preview_img

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

    # ================= FILE SIZE =================
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
