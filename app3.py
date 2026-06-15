import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
import zipfile
import io
import json
import hashlib
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
import numpy as np

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Bulk Photo SaaS FIXED", layout="wide")

# =========================
# COOKIE SYSTEM
# =========================
cookies = EncryptedCookieManager(
    prefix="photo_saas",
    password="super_secure_key"
)

if not cookies.ready():
    st.stop()

# =========================
# DATABASE
# =========================
DB_FILE = "users.json"

def load_users():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "admin": {
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "email": "admin@demo.com"
            },
            "user": {
                "password": hashlib.sha256("user123".encode()).hexdigest(),
                "email": "user@demo.com"
            }
        }

def save_users():
    with open(DB_FILE, "w") as f:
        json.dump(st.session_state.USERS, f)

# =========================
# SESSION INIT
# =========================
if "USERS" not in st.session_state:
    st.session_state.USERS = load_users()

if "user" not in st.session_state:
    st.session_state.user = None

if "history" not in st.session_state:
    st.session_state.history = []

USERS = st.session_state.USERS

# =========================
# AUTO LOGIN
# =========================
def restore_login():
    saved = cookies.get("user")
    if saved:
        saved = str(saved).strip()
    if saved and saved in USERS:
        st.session_state.user = saved

if st.session_state.user is None:
    restore_login()

# =========================
# AUTH
# =========================
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login():
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == hash_pass(p):
            st.session_state.user = u
            cookies["user"] = u
            cookies.save()
            st.rerun()
        else:
            st.error("Invalid credentials")

def logout():
    cookies["user"] = ""
    cookies.save()
    st.session_state.user = None
    st.rerun()

# =========================
# ROUTING
# =========================
if not st.session_state.user:
    login()
    st.stop()

# =========================
# DASHBOARD
# =========================
st.title("📸 Bulk Photo SaaS FIXED VERSION")
st.success(f"Welcome {st.session_state.user}")

if st.button("Logout"):
    logout()

# =========================
# UPLOAD + CAMERA
# =========================
st.subheader("Upload / Camera")

col1, col2 = st.columns(2)

with col1:
    files = st.file_uploader(
        "Upload Images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True
    )

with col2:
    camera = st.camera_input("Take Photo")

images = []
if files:
    images.extend(files)
if camera:
    images.append(camera)

# =========================
# SETTINGS
# =========================
preset = st.selectbox("Preset", ["Custom", "Passport", "NADRA", "HD"])

sizes = {
    "Passport": (300, 300),
    "NADRA": (400, 400),
    "HD": (800, 1000),
    "Custom": (300, 300)
}

w, h = sizes[preset]

width = st.number_input("Width", value=w)
height = st.number_input("Height", value=h)

remove_bg = st.checkbox("Remove Background", True)
enhance = st.checkbox("Enhance Image", True)

prefix = st.text_input("File Prefix", "photo")

# =========================
# 🔥 SAFE REMBG FIX (IMPORTANT)
# =========================
def safe_remove_bg(img):
    out = remove(img)

    # CASE 1: bytes output
    if isinstance(out, (bytes, bytearray)):
        try:
            return Image.open(io.BytesIO(out)).convert("RGBA")
        except:
            return img.convert("RGBA")

    # CASE 2: numpy array
    elif isinstance(out, np.ndarray):
        return Image.fromarray(out).convert("RGBA")

    # CASE 3: PIL or other
    else:
        try:
            return out.convert("RGBA")
        except:
            return img.convert("RGBA")

# =========================
# PROCESS
# =========================
if images and st.button("PROCESS"):

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w") as zipf:

        preview = False

        for i, file in enumerate(images):

            img = Image.open(file)

            if remove_bg:
                img = safe_remove_bg(img)
            else:
                img = img.convert("RGB")

            img = img.resize((width, height))

            if enhance:
                img = ImageEnhance.Sharpness(img).enhance(2.5)
                img = ImageEnhance.Contrast(img).enhance(1.3)
                img = ImageEnhance.Brightness(img).enhance(1.05)
                img = img.filter(ImageFilter.UnsharpMask(2, 150, 3))

            if not preview:
                st.image(img, width=200)
                preview = True

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            buffer.seek(0)

            zipf.writestr(f"{prefix}_{i+1}.jpg", buffer.getvalue())

            progress.progress((i + 1) / len(images))

    st.session_state.history.append({
        "user": st.session_state.user,
        "files": len(images),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    st.success("Processing Complete")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="output.zip"
    )

# =========================
# HISTORY
# =========================
st.divider()
st.subheader("History")

for h in reversed(st.session_state.history):
    st.write(h)
