import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
import zipfile
import io

st.set_page_config(page_title="Bulk Photo Processor V2", layout="wide")

# ---------------------------
# Compression Function
# ---------------------------
def compress_to_target(img, target_kb, fmt):
    quality = 95
    while quality >= 10:
        temp = io.BytesIO()
        save_format = "JPEG" if fmt == "JPG" else fmt
        save_kwargs = {"format": save_format}

        if save_format in ["JPEG", "WEBP"]:
            save_kwargs["quality"] = quality

        img.save(temp, **save_kwargs)

        if len(temp.getvalue()) / 1024 <= target_kb:
            temp.seek(0)
            return temp

        quality -= 5

    temp.seek(0)
    return temp


# ---------------------------
# UI
# ---------------------------
st.title("📸 Bulk Photo Processor V2")

mode = st.radio("Input Mode", ["Upload Images", "Camera"])

uploaded_files = []

if mode == "Upload Images":
    uploaded_files = st.file_uploader(
        "Upload Images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True
    ) or []
else:
    cam = st.camera_input("Take a Photo")
    if cam:
        uploaded_files = [cam]

# ---------------------------
# Presets
# ---------------------------
preset = st.selectbox(
    "Preset",
    ["Custom", "Passport (300x300)", "NADRA (400x400)",
     "University Admission (200x200)", "Job Application (300x400)"]
)

default_w, default_h = 300, 300

if preset == "NADRA (400x400)":
    default_w, default_h = 400, 400
elif preset == "University Admission (200x200)":
    default_w, default_h = 200, 200
elif preset == "Job Application (300x400)":
    default_w, default_h = 300, 400

c1, c2 = st.columns(2)
with c1:
    width = st.number_input("Width", min_value=50, value=default_w)
with c2:
    height = st.number_input("Height", min_value=50, value=default_h)

# ---------------------------
# Options
# ---------------------------
bg_color = st.selectbox(
    "Background Color",
    ["white", "blue", "red", "green", "yellow", "black"]
)

output_format = st.selectbox("Output Format", ["JPG", "PNG", "WEBP"])

if target_size == "20 KB":
    img_bytes = compress_to_target(image, 20, output_format)
elif target_size == "50 KB":
    img_bytes = compress_to_target(image, 50, output_format)
elif target_size == "100 KB":
    img_bytes = compress_to_target(image, 100, output_format)
elif target_size == "Custom" and custom_kb:
    img_bytes = compress_to_target(image, custom_kb, output_format)

enhance_image = st.checkbox("Enhance & Sharpen Image")
remove_background = st.checkbox("Remove Background (AI)", value=True)

prefix = st.text_input("Batch Rename Prefix", "photo")
st.subheader("Image Resolution (DPI)")

dpi_mode = st.radio("DPI Mode", ["Preset DPI", "Custom DPI"], horizontal=True)

if dpi_mode == "Preset DPI":
    dpi_value = st.selectbox("Select DPI", [72, 150, 300, 600])
else:
    dpi_value = st.number_input("Enter Custom DPI", min_value=10, max_value=1200, value=300)


# ---------------------------
# Preview
# ---------------------------
if uploaded_files:
    st.subheader("Original Images")
    cols = st.columns(4)

    for i, f in enumerate(uploaded_files):
        with cols[i % 4]:
            st.image(f, use_container_width=True)

    # ---------------------------
    # Process
    # ---------------------------
    if st.button("🚀 Process Images"):

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            progress = st.progress(0)

            preview_done = False

            for idx, file in enumerate(uploaded_files):
                image = Image.open(file)

                # Background remove
                if remove_background:
                    image = remove(image)
                    image = image.convert("RGBA")
                    new_bg = Image.new("RGBA", image.size, bg_color)
                    image = Image.alpha_composite(new_bg, image)
                else:
                    image = image.convert("RGB")

                # Resize
                image = image.resize((int(width), int(height)))

                # Enhance
                if enhance_image:
                    image = image.filter(ImageFilter.SHARPEN)
                    image = ImageEnhance.Sharpness(image).enhance(2.0)
                    image = ImageEnhance.Contrast(image).enhance(1.2)

                # Convert for JPG
                if output_format == "JPG":
                    image = image.convert("RGB")

                # Preview
                if not preview_done:
                    st.subheader("Processed Preview")
                    st.image(image, width=250)
                    preview_done = True

                # Save format
                save_format = "JPEG" if output_format == "JPG" else output_format

                img_bytes = io.BytesIO()

                save_kwargs = {"format": save_format}
                if save_format in ["JPEG", "WEBP"]:
                    save_kwargs["quality"] = 95

                # DPI apply
                image.save(
                    img_bytes,
                    dpi=(dpi_value, dpi_value),
                    **save_kwargs
                )

                img_bytes.seek(0)

                # Compression
                if target_size == "20 KB":
                    img_bytes = compress_to_target(image, 20, output_format)
                elif target_size == "50 KB":
                    img_bytes = compress_to_target(image, 50, output_format)
                elif target_size == "100 KB":
                    img_bytes = compress_to_target(image, 100, output_format)

                filename = f"{prefix}_{idx+1}.{output_format.lower()}"
                zipf.writestr(filename, img_bytes.getvalue())

                progress.progress((idx + 1) / len(uploaded_files))

        st.success("✅ Processing Complete")

        st.download_button(
            "📥 Download ZIP",
            zip_buffer.getvalue(),
            file_name="processed_images.zip",
            mime="application/zip"
        )
