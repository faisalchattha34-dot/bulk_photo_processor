import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io

st.set_page_config(page_title="Photo SaaS Camera Mode", layout="wide")

# =========================
# FILTER FUNCTION
# =========================
def apply_filter(img, filter_type):
    if filter_type == "Bright":
        img = ImageEnhance.Brightness(img).enhance(1.4)

    elif filter_type == "Soft Glow":
        img = img.filter(ImageFilter.GaussianBlur(2))
        img = ImageEnhance.Brightness(img).enhance(1.2)

    elif filter_type == "Black & White":
        img = img.convert("L").convert("RGB")

    elif filter_type == "Sharpen":
        img = ImageEnhance.Sharpness(img).enhance(2.0)

    elif filter_type == "Blur":
        img = img.filter(ImageFilter.GaussianBlur(5))

    return img


# =========================
# UI
# =========================
st.title("📸 Snap Camera Photo SaaS")

# 📷 CAMERA INPUT
camera_image = st.camera_input("Take a live photo")

# 🎨 FILTERS
filter_type = st.selectbox(
    "Choose Filter (Snapchat Style)",
    ["None", "Bright", "Soft Glow", "Black & White", "Sharpen", "Blur"]
)

# =========================
# PROCESS
# =========================
if camera_image is not None:

    img = Image.open(camera_image)

    st.subheader("Original Image")
    st.image(img, use_container_width=True)

    # Apply filter
    filtered_img = apply_filter(img, filter_type)

    st.subheader("Filtered Preview")
    st.image(filtered_img, use_container_width=True)

    # =========================
    # DOWNLOAD
    # =========================
    buf = io.BytesIO()
    filtered_img.save(buf, format="JPEG", quality=95)
    buf.seek(0)

    st.download_button(
        "⬇️ Download Photo",
        data=buf,
        file_name="snap_photo.jpg",
        mime="image/jpeg"
    )
