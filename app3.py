import streamlit as st
from PIL import Image, ImageEnhance
import io
import zipfile
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Bulk Photo SaaS V6", layout="wide")

# =========================
# SIMPLE USER DATABASE
# =========================
if "USERS" not in st.session_state:
    st.session_state.USERS = {
        "admin": "admin"
    }

if "LOGGED_IN" not in st.session_state:
    st.session_state.LOGGED_IN = False

if "USERNAME" not in st.session_state:
    st.session_state.USERNAME = ""

# =========================
# AUTH FUNCTIONS
# =========================
def login():
    st.subheader("Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in st.session_state.USERS and st.session_state.USERS[u] == p:
            st.session_state.LOGGED_IN = True
            st.session_state.USERNAME = u
            st.success("Login successful")
        else:
            st.error("Invalid credentials")


def register():
    st.subheader("Register")
    u = st.text_input("New Username")
    p = st.text_input("New Password", type="password")

    if st.button("Create Account"):
        if u in st.session_state.USERS:
            st.error("User already exists")
        else:
            st.session_state.USERS[u] = p
            st.success("Account created")


# =========================
# IMAGE UTILITIES
# =========================
def compress_to_kb(image, target_kb, fmt="JPEG"):
    quality = 95
    min_q = 10

    while quality >= min_q:
        buffer = io.BytesIO()
        image.save(buffer, format=fmt, quality=quality, optimize=True)
        size_kb = len(buffer.getvalue()) / 1024

        if size_kb <= target_kb:
            buffer.seek(0)
            return buffer

        quality -= 5

    buffer.seek(0)
    return buffer


def resize_image(img, size_type):
    if size_type == "Passport (35x45mm approx)":
        return img.resize((413, 531))
    return img


def enhance_image(img, brightness, contrast):
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    return img


def remove_bg_safe(img):
    try:
        from rembg import remove
        output = remove(img)
        return Image.open(io.BytesIO(output))
    except:
        return img


# =========================
# MAIN APP
# =========================
def main_app():
    st.title("📸 Bulk Photo Processor SaaS V6")

    st.sidebar.header("⚙ Settings")

    target_kb = st.sidebar.number_input("Target Size (KB)", 5, 5000, 100)
    dpi = st.sidebar.number_input("DPI", 72, 600, 300)

    size_option = st.sidebar.selectbox(
        "Resize Option",
        ["Original", "Passport (35x45mm approx)"]
    )

    brightness = st.sidebar.slider("Brightness", 0.5, 2.0, 1.0)
    contrast = st.sidebar.slider("Contrast", 0.5, 2.0, 1.0)

    remove_bg = st.sidebar.checkbox("Remove Background")

    uploaded_files = st.file_uploader(
        "Upload Images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    if uploaded_files:
        zip_buffer = io.BytesIO()
        zipf = zipfile.ZipFile(zip_buffer, "w")

        for i, file in enumerate(uploaded_files):
            img = Image.open(file).convert("RGB")

            # processing
            img = resize_image(img, size_option)
            img = enhance_image(img, brightness, contrast)

            if remove_bg:
                img = remove_bg_safe(img)

            img.info["dpi"] = (dpi, dpi)

            compressed = compress_to_kb(img, target_kb)

            filename = f"processed_{i+1}.jpg"
            zipf.writestr(filename, compressed.getvalue())

        zipf.close()
        zip_buffer.seek(0)

        st.download_button(
            "⬇ Download ZIP",
            zip_buffer,
            file_name=f"photos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )


# =========================
# APP ROUTING
# =========================
st.sidebar.title("Navigation")

menu = st.sidebar.radio("Menu", ["Login", "Register", "App"])

if menu == "Login":
    login()
elif menu == "Register":
    register()
elif menu == "App":
    if st.session_state.LOGGED_IN:
        main_app()
    else:
        st.warning("Please login first")
