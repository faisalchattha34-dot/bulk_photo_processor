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
st.set_page_config(page_title="Bulk Photo SaaS PRO ULTIMATE", layout="wide")

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

def register():
    st.title("📝 Register")

    u = st.text_input("Username")
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")

    if st.button("Create"):
        if u in USERS:
            st.error("User exists")
        else:
            USERS[u] = {
                "password": hash_pass(p),
                "email": e,
                "credits": 10
            }
            save_users()
            st.success("Account created")

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
user = st.session_state.user

st.title("📸 BULK PHOTO SAAS ULTIMATE (ALL FEATURES)")
st.success(f"Welcome {user}")

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
st.subheader("Settings")

preset = st.selectbox("Preset", ["Custom","Passport","NADRA","Job","HD"])

sizes = {
    "Passport": (300,300),
    "NADRA": (400,400),
    "Job": (300,400),
    "HD": (800,1000),
    "Custom": (300,300)
}

w, h = sizes[preset]

width = st.number_input("Width", value=w)
height = st.number_input("Height", value=h)

bg_color = st.selectbox("Background Color", ["none","white","blue","red","black"])
output_format = st.selectbox("Format", ["JPG","PNG","WEBP"])
dpi = st.selectbox("DPI", [72,150,300,600])

remove_bg = st.checkbox("Remove Background", True)
enhance = st.checkbox("AI Enhance (Remini Mode)", True)

prefix = st.text_input("File Prefix", "photo")

# =========================
# SMART COMPRESSION UI (NEW)
# =========================
st.subheader("Compression Control")

mode = st.selectbox("Compression Mode", ["Preset", "Custom KB"])

if mode == "Preset":
    kb_map = {
        "Low (20KB)": 20,
        "Medium (100KB)": 100,
        "High (300KB)": 300
    }
    choice = st.selectbox("Preset Size", list(kb_map.keys()))
    target_kb = kb_map[choice]
else:
    target_kb = st.number_input("Custom KB", 5, 5000, 100)

# =========================
# REMINI STYLE ENHANCEMENT
# =========================
def remini_enhance(img):
    img = ImageEnhance.Sharpness(img).enhance(3.0)
    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = ImageEnhance.Brightness(img).enhance(1.1)
    img = img.filter(ImageFilter.UnsharpMask(2,200,3))
    return img

# =========================
# SMART COMPRESS
# =========================
def smart_compress(img, target_kb):
    quality = 95
    while quality > 10:
        buffer = io.BytesIO()
        temp = img.convert("RGB")
        temp.save(buffer, format="JPEG", quality=quality)
        size_kb = len(buffer.getvalue()) / 1024

        if size_kb <= target_kb:
            buffer.seek(0)
            return buffer

        quality -= 5

    buffer.seek(0)
    return buffer

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
# BG COLOR APPLY
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

            img = img.resize((width, height))

            # ENHANCE (REMINI STYLE)
            if enhance:
                img = remini_enhance(img)

            # BG COLOR
            img = apply_bg(img, bg_color)

            if not preview:
                st.image(img, width=200)
                preview = True

            # FORMAT HANDLING
            fmt = output_format.upper()

            buffer = smart_compress(img, target_kb)

            zipf.writestr(f"{prefix}_{i+1}.{fmt.lower()}", buffer.getvalue())

            progress.progress((i+1)/len(images))

    st.session_state.history.append({
        "user": user,
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
