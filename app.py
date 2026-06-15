import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
import zipfile
import io
from datetime import datetime

st.set_page_config(page_title="Bulk Photo SaaS V4", layout="wide")

# =========================
# SESSION STATE (SAAS LOGS)
# =========================
if "history" not in st.session_state:
    st.session_state.history = []

# =========================
# SAFE COMPRESSION ENGINE
# =========================
def compress_to_target(img, target_kb, fmt):
    quality = 95
    save_format = "JPEG" if fmt == "JPG" else fmt

    while quality >= 10:
        buffer = io.BytesIO()

        save_kwargs = {"format": save_format}
        if save_format in ["JPEG", "WEBP"]:
            save_kwargs["quality"] = quality

        img.save(buffer, **save_kwargs)

        size_kb = len(buffer.getvalue()) / 1024

        if size_kb <= target_kb:
            buffer.seek(0)
            return buffer

        quality -= 5

    buffer.seek(0)
    return buffer


# =========================
# UI HEADER
# =========================
st.title("📸 Bulk Photo Processor SaaS V4")
st.caption("Startup Ready | Admin Controls | AI Background | Compression Engine")

# =========================
# INPUT MODE
# =========================
mode = st.radio("Input Mode", ["Upload Images", "Camera"], horizontal=True)

files = []

if mode == "Upload Images":
    files = st.file_uploader(
        "Upload Images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True
    ) or []
else:
    cam = st.camera_input("Take a Photo")
    if cam:
        files = [cam]


# =========================
# PRESET SYSTEM
# =========================
preset = st.selectbox(
    "Image Preset",
    ["Custom", "Passport (300x300)", "NADRA (400x400)",
     "University (200x200)", "Job (300x400)"]
)

preset_map = {
    "Passport (300x300)": (300, 300),
    "NADRA (400x400)": (400, 400),
    "University (200x200)": (200, 200),
    "Job (300x400)": (300, 400),
    "Custom": (300, 300)
}

width, height = preset_map[preset]

c1, c2 = st.columns(2)
with c1:
    width = st.number_input("Width", min_value=50, value=width)
with c2:
    height = st.number_input("Height", min_value=50, value=height)


# =========================
# STYLE SETTINGS
# =========================
bg_color = st.selectbox("Background Color", ["white", "blue", "red", "green", "black"])
output_format = st.selectbox("Output Format", ["JPG", "PNG", "WEBP"])

enhance = st.checkbox("Enhance Image", value=True)

# ✅ NEW ADMIN FEATURE (REQUESTED)
remove_bg_option = st.selectbox(
    "Background Removal (Admin Control)",
    ["Auto (AI Remove)", "No Background Removal"],
    index=0
)

remove_bg = True if remove_bg_option == "Auto (AI Remove)" else False

prefix = st.text_input("File Prefix", "photo")


# =========================
# DPI SYSTEM
# =========================
st.subheader("Resolution Control (DPI)")

dpi_mode = st.radio("DPI Mode", ["Preset", "Custom"], horizontal=True)

if dpi_mode == "Preset":
    dpi_value = st.selectbox("Select DPI", [72, 150, 300, 600])
else:
    dpi_value = st.number_input("Custom DPI", min_value=10, max_value=1200, value=300)


# =========================
# SIZE CONTROL SYSTEM
# =========================
st.subheader("File Size Control")

size_mode = st.radio("Size Mode", ["Preset", "Custom"], horizontal=True)

if size_mode == "Preset":
    size_choice = st.selectbox("Target Size", ["No Limit", "20 KB", "50 KB", "100 KB"])
    custom_size = None
else:
    size_choice = "Custom"
    custom_size = st.number_input("Enter Size (KB)", min_value=1, value=100)


# =========================
# PREVIEW
# =========================
if files:
    st.subheader("Original Preview")
    cols = st.columns(4)

    for i, f in enumerate(files):
        with cols[i % 4]:
            st.image(f, use_container_width=True)


# =========================
# PROCESS ENGINE
# =========================
if files and st.button("🚀 Process (V4 SaaS)"):

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:

        preview_done = False

        for i, file in enumerate(files):

            image = Image.open(file)

            # -------------------
            # BACKGROUND CONTROL
            # -------------------
            if remove_bg:
                image = remove(image)
                image = image.convert("RGBA")

                bg = Image.new("RGBA", image.size, bg_color)
                image = Image.alpha_composite(bg, image)
            else:
                image = image.convert("RGB")

            # -------------------
            # RESIZE
            # -------------------
            image = image.resize((width, height))

            # -------------------
            # ENHANCE
            # -------------------
            if enhance:
                image = image.filter(ImageFilter.SHARPEN)
                image = ImageEnhance.Sharpness(image).enhance(2.0)
                image = ImageEnhance.Contrast(image).enhance(1.2)

            # JPG FIX
            if output_format == "JPG":
                image = image.convert("RGB")

            # -------------------
            # PREVIEW FIRST IMAGE
            # -------------------
            if not preview_done:
                st.subheader("Processed Preview")
                st.image(image, width=250)
                preview_done = True

            # -------------------
            # SAVE IMAGE
            # -------------------
            save_format = "JPEG" if output_format == "JPG" else output_format
            buffer = io.BytesIO()

            save_kwargs = {"format": save_format}
            if save_format in ["JPEG", "WEBP"]:
                save_kwargs["quality"] = 95

            image.save(buffer, dpi=(dpi_value, dpi_value), **save_kwargs)
            buffer.seek(0)

            # -------------------
            # COMPRESSION
            # -------------------
            if size_choice == "20 KB":
                buffer = compress_to_target(image, 20, output_format)
            elif size_choice == "50 KB":
                buffer = compress_to_target(image, 50, output_format)
            elif size_choice == "100 KB":
                buffer = compress_to_target(image, 100, output_format)
            elif size_choice == "Custom" and custom_size:
                buffer = compress_to_target(image, custom_size, output_format)

            filename = f"{prefix}_{i+1}.{output_format.lower()}"
            zipf.writestr(filename, buffer.getvalue())

            progress.progress((i + 1) / len(files))

    # =========================
    # SAAS HISTORY LOG
    # =========================
    st.session_state.history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files": len(files),
        "format": output_format,
        "bg_remove": remove_bg,
        "size": size_choice
    })

    st.success("✅ Processing Completed Successfully")

    st.download_button(
        "📥 Download ZIP",
        zip_buffer.getvalue(),
        file_name="bulk_photos_v4.zip",
        mime="application/zip"
    )


# =========================
# HISTORY PANEL (SAAS FEATURE)
# =========================
st.divider()
st.subheader("📊 SaaS Processing History")

if st.session_state.history:
    for h in reversed(st.session_state.history):
        st.write(
            f"🕒 {h['time']} | 📁 {h['files']} files | 🎨 {h['format']} | 🧠 BG Remove: {h['bg_remove']} | 📦 {h['size']}"
        )
else:
    st.info("No history yet")
