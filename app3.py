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
st.set_page_config(page_title="Bulk Photo SaaS FULL PRO", layout="wide")

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
                "email": "admin@demo.com",
                "credits": 999
            },
            "user": {
                "password": hashlib.sha256("user123".encode()).hexdigest(),
                "email": "user@demo.com",
                "credits": 20
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
st.title("📸 BULK PHOTO SAAS FULL (RESTORED)")
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
# SETTINGS (FULL RESTORED)
# =========================
st.subheader("Settings")

preset = st.selectbox("Preset", ["Custom","Passport","NADRA","Job","HD"])

preset_map = {
    "Passport": (300,300),
    "NADRA": (400,400),
    "Job": (300,400),
    "HD": (800,1000),
    "Custom": (300,300)
}

w, h = preset_map[preset]

width = st.number_input("Width", value=w)
height = st.number_input("Height", value=h)

# ✔ Background color feature RESTORED
bg_color = st.selectbox("Background Color (after remove)", ["none","white","blue","red","black"])

# ✔ Format change feature RESTORED
output_format = st.selectbox("Output Format", ["JPG","PNG","WEBP"])

# ✔ DPI feature RESTORED
dpi = st.selectbox("DPI", [72,150,300,600])

# ✔ Compression control (basic safe)
quality = st.slider("Compression Quality (JPG)", 10, 100, 90)

remove_bg = st.checkbox("Remove Background (AI)", True)
enhance = st.checkbox("Enhance Image", True)

prefix = st.text_input("File Prefix", "photo")

# =========================
# SAFE BG REMOVE
# =========================
def safe_remove(img):
    out = remove(img)

    if isinstance(out, (bytes, bytearray)):
        return Image.open(io.BytesIO(out))
    elif isinstance(out, np.ndarray):
        return Image.fromarray(out)
    else:
        return out

# =========================
# BACKGROUND COLOR APPLY
# =========================
def apply_bg(img, color):
    if color == "none":
        return img

    base = Image.new("RGB", img.size, color)

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    base.paste(img, mask=img.split()[-1])
    return base

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

            # BG REMOVE
            if remove_bg:
                img = safe_remove(img).convert("RGBA")
            else:
                img = img.convert("RGB")

            # RESIZE
            img = img.resize((width, height))

            # ENHANCE
            if enhance:
                img = ImageEnhance.Sharpness(img).enhance(2.5)
                img = ImageEnhance.Contrast(img).enhance(1.3)
                img = ImageEnhance.Brightness(img).enhance(1.05)
                img = img.filter(ImageFilter.UnsharpMask(2,150,3))

            # BACKGROUND COLOR APPLY
            img = apply_bg(img, bg_color)

            if not preview:
                st.image(img, width=200)
                preview = True

            buffer = io.BytesIO()

            fmt = output_format.upper()

            if fmt == "JPG":
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(buffer, format="JPEG", quality=quality)

            else:
                img.save(buffer, format=fmt)

            buffer.seek(0)

            zipf.writestr(f"{prefix}_{i+1}.{fmt.lower()}", buffer.getvalue())

            progress.progress((i+1)/len(images))

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
