import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
import zipfile
import io
from datetime import datetime

st.set_page_config(page_title="Bulk Photo Tool FREE", layout="wide")

# =========================
# DATABASE (SESSION DEMO)
# =========================
if "USERS" not in st.session_state:
    st.session_state.USERS = {
        "admin": {"password": "admin123", "email": "admin@demo.com"},
        "user": {"password": "user123", "email": "user@demo.com"}
    }

if "user" not in st.session_state:
    st.session_state.user = None

if "history" not in st.session_state:
    st.session_state.history = []

if "page" not in st.session_state:
    st.session_state.page = "login"

USERS = st.session_state.USERS


# =========================
# REGISTER
# =========================
def register():
    st.title("📝 Register (FREE)")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if username == "" or email == "":
            st.error("All fields required")
        elif username in USERS:
            st.error("User already exists")
        else:
            USERS[username] = {
                "password": password,
                "email": email
            }
            st.success("Account created successfully")
            st.session_state.page = "login"
            st.rerun()


# =========================
# LOGIN
# =========================
def login():
    st.title("🔐 Login (FREE)")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.user = username
                st.success("Login Success")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with col2:
        if st.button("Register"):
            st.session_state.page = "register"
            st.rerun()


# =========================
# LOGOUT
# =========================
def logout():
    st.session_state.user = None
    st.session_state.page = "login"
    st.rerun()


# =========================
# AUTH ROUTING
# =========================
if not st.session_state.user:
    if st.session_state.page == "register":
        register()
    else:
        login()
    st.stop()


# =========================
# DASHBOARD
# =========================
st.title("📸 Bulk Photo Tool FREE VERSION")
st.success(f"Welcome {st.session_state.user}")

if st.button("Logout"):
    logout()


# =========================
# UPLOAD
# =========================
files = st.file_uploader(
    "Upload Images",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
) or []


# =========================
# SIZE PRESETS
# =========================
st.subheader("Size Presets")

preset = st.selectbox(
    "Preset",
    ["Custom", "Passport (300x300)", "NADRA (400x400)", "Job (300x400)", "HD (800x1000)"]
)

preset_map = {
    "Passport (300x300)": (300, 300),
    "NADRA (400x400)": (400, 400),
    "Job (300x400)": (300, 400),
    "HD (800x1000)": (800, 1000),
    "Custom": (300, 300)
}

width, height = preset_map[preset]

col1, col2 = st.columns(2)
with col1:
    width = st.number_input("Width", min_value=50, value=width)
with col2:
    height = st.number_input("Height", min_value=50, value=height)


# =========================
# SETTINGS
# =========================
bg_color = st.selectbox("Background", ["white", "blue", "red", "green", "black"])
output_format = st.selectbox("Format", ["JPG", "JPEG", "PNG", "WEBP"])

remove_bg = st.checkbox("Remove Background (AI)", True)
enhance = st.checkbox("Enhance Image", True)

prefix = st.text_input("File Prefix", "photo")


# =========================
# DPI
# =========================
st.subheader("DPI Settings")

dpi_mode = st.radio("DPI Mode", ["Preset", "Custom"], horizontal=True)

if dpi_mode == "Preset":
    dpi = st.selectbox("DPI", [72, 150, 300, 600])
else:
    dpi = st.number_input("Custom DPI", min_value=10, max_value=5000, value=300)


# =========================
# COMPRESSION
# =========================
st.subheader("Compression")

min_kb = st.number_input("Min KB (0 = off)", value=0)
max_kb = st.number_input("Max KB (0 = off)", value=0)


def smart_compress(img, min_kb, max_kb, fmt):
    quality = 95
    save_format = "JPEG" if fmt in ["JPG", "JPEG"] else fmt

    while quality >= 10:
        buffer = io.BytesIO()

        save_kwargs = {"format": save_format}
        if save_format in ["JPEG", "WEBP"]:
            save_kwargs["quality"] = quality

        img.save(buffer, **save_kwargs)
        size_kb = len(buffer.getvalue()) / 1024

        if min_kb and max_kb and min_kb <= size_kb <= max_kb:
            buffer.seek(0)
            return buffer

        quality -= 5

    buffer.seek(0)
    return buffer


# =========================
# PROCESS
# =========================
if files and st.button("🚀 PROCESS"):

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:

        preview_done = False

        for i, file in enumerate(files):

            img = Image.open(file)

            if remove_bg:
                img = remove(img)
                img = img.convert("RGBA")
                bg = Image.new("RGBA", img.size, bg_color)
                img = Image.alpha_composite(bg, img)
            else:
                img = img.convert("RGB")

            img = img.resize((width, height))

            if enhance:
                img = img.filter(ImageFilter.SHARPEN)
                img = ImageEnhance.Sharpness(img).enhance(2)
                img = ImageEnhance.Contrast(img).enhance(1.2)

            if output_format in ["JPG", "JPEG"]:
                img = img.convert("RGB")

            if not preview_done:
                st.subheader("Preview")
                st.image(img, width=250)
                preview_done = True

            buffer = io.BytesIO()

            img.save(buffer, format="JPEG" if output_format in ["JPG","JPEG"] else output_format, dpi=(dpi, dpi))
            buffer.seek(0)

            if min_kb and max_kb:
                buffer = smart_compress(img, min_kb, max_kb, output_format)

            filename = f"{prefix}_{i+1}.{output_format.lower()}"
            zipf.writestr(filename, buffer.getvalue())

            progress.progress((i+1)/len(files))

    st.session_state.history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": st.session_state.user,
        "files": len(files)
    })

    st.success("Done")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="output_free.zip"
    )


# =========================
# HISTORY
# =========================
st.divider()
st.subheader("History")

for h in reversed(st.session_state.history):
    st.write(f"{h['time']} | {h['user']} | files: {h['files']}")
