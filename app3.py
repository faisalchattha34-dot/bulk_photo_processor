import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
import zipfile
import io
from datetime import datetime

st.set_page_config(page_title="Bulk Photo SaaS V5", layout="wide")

# =========================
# FAKE DATABASE (SaaS DEMO)
# =========================
USERS = {
    "admin": {"password": "admin123", "credits": 999},
    "user": {"password": "user123", "credits": 20}
}

# =========================
# SESSION STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "credits" not in st.session_state:
    st.session_state.credits = 0

if "history" not in st.session_state:
    st.session_state.history = []

# =========================
# LOGIN SYSTEM
# =========================
def login():
    st.title("🔐 SaaS Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.user = username
            st.session_state.credits = USERS[username]["credits"]
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Credentials")

# =========================
# LOGOUT
# =========================
def logout():
    st.session_state.user = None
    st.session_state.credits = 0
    st.rerun()

# =========================
# COMPRESSION ENGINE
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

        if len(buffer.getvalue()) / 1024 <= target_kb:
            buffer.seek(0)
            return buffer

        quality -= 5

    buffer.seek(0)
    return buffer

# =========================
# LOGIN CHECK
# =========================
if not st.session_state.user:
    login()
    st.stop()

# =========================
# HEADER DASHBOARD
# =========================
st.title("📸 Bulk Photo SaaS V5 (Startup Edition)")
st.success(f"Welcome {st.session_state.user} | Credits: {st.session_state.credits}")

if st.button("Logout"):
    logout()

# =========================
# CREDIT SYSTEM CHECK
# =========================
def use_credit(count):
    if st.session_state.credits >= count:
        st.session_state.credits -= count
        USERS[st.session_state.user]["credits"] -= count
        return True
    return False

# =========================
# INPUT
# =========================
files = st.file_uploader(
    "Upload Images",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
) or []

# =========================
# SETTINGS
# =========================
preset = st.selectbox("Preset", ["Custom", "Passport", "NADRA", "Job"])
size_map = {
    "Passport": (300, 300),
    "NADRA": (400, 400),
    "Job": (300, 400),
    "Custom": (300, 300)
}

width, height = size_map[preset]

c1, c2 = st.columns(2)
with c1:
    width = st.number_input("Width", value=width)
with c2:
    height = st.number_input("Height", value=height)

bg_color = st.selectbox("Background", ["white", "blue", "red", "green", "black"])
output_format = st.selectbox("Format", ["JPG", "PNG", "WEBP"])

remove_bg_option = st.selectbox(
    "Background Removal",
    ["ON (AI)", "OFF"]
)

remove_bg = remove_bg_option == "ON (AI)"

enhance = st.checkbox("Enhance Image", True)

prefix = st.text_input("File Prefix", "photo")

# =========================
# DPI
# =========================
dpi = st.selectbox("DPI", [72, 150, 300, 600])

# =========================
# SIZE CONTROL
# =========================
size_choice = st.selectbox("File Size", ["No Limit", "20 KB", "50 KB", "100 KB"])

# =========================
# PROCESS BUTTON
# =========================
if files and st.button("🚀 PROCESS (V5 SAAS)"):

    # CREDIT CHECK
    if not use_credit(len(files)):
        st.error("❌ Not enough credits. Please buy more.")
        st.stop()

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:

        preview = False

        for i, file in enumerate(files):

            image = Image.open(file)

            # BG REMOVE
            if remove_bg:
                image = remove(image)
                image = image.convert("RGBA")
                bg = Image.new("RGBA", image.size, bg_color)
                image = Image.alpha_composite(bg, image)
            else:
                image = image.convert("RGB")

            # RESIZE
            image = image.resize((width, height))

            # ENHANCE
            if enhance:
                image = image.filter(ImageFilter.SHARPEN)
                image = ImageEnhance.Sharpness(image).enhance(2.0)
                image = ImageEnhance.Contrast(image).enhance(1.2)

            if output_format == "JPG":
                image = image.convert("RGB")

            # PREVIEW
            if not preview:
                st.subheader("Preview")
                st.image(image, width=250)
                preview = True

            save_format = "JPEG" if output_format == "JPG" else output_format
            buffer = io.BytesIO()

            image.save(buffer, format=save_format, dpi=(dpi, dpi))
            buffer.seek(0)

            # COMPRESSION
            if size_choice == "20 KB":
                buffer = compress_to_target(image, 20, output_format)
            elif size_choice == "50 KB":
                buffer = compress_to_target(image, 50, output_format)
            elif size_choice == "100 KB":
                buffer = compress_to_target(image, 100, output_format)

            filename = f"{prefix}_{i+1}.{output_format.lower()}"
            zipf.writestr(filename, buffer.getvalue())

            progress.progress((i + 1) / len(files))

    # HISTORY
    st.session_state.history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files": len(files),
        "user": st.session_state.user,
        "credits_left": st.session_state.credits
    })

    st.success("✅ Processing Complete")

    st.download_button(
        "📥 Download ZIP",
        zip_buffer.getvalue(),
        file_name="bulk_v5_saas.zip",
        mime="application/zip"
    )

# =========================
# HISTORY
# =========================
st.divider()
st.subheader("📊 User History")

for h in reversed(st.session_state.history):
    st.write(f"🕒 {h['time']} | 👤 {h['user']} | 📁 {h['files']} files | 💳 Credits: {h['credits_left']}")
