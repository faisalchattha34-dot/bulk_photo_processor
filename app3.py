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
import os

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
# DATABASE FILE
# =========================
DB_FILE = "users.json"
HISTORY_FILE = "history.json"

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
            }
        }

def save_users():
    with open(DB_FILE, "w") as f:
        json.dump(st.session_state.USERS, f)

def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(st.session_state.history, f)

# =========================
# SESSION INIT
# =========================
if "USERS" not in st.session_state:
    st.session_state.USERS = load_users()

if "user" not in st.session_state:
    st.session_state.user = None

if "history" not in st.session_state:
    st.session_state.history = load_history()

USERS = st.session_state.USERS

# =========================
# LOGIN RESTORE
# =========================
def restore_login():
    saved = cookies.get("user")
    if saved and saved in USERS:
        st.session_state.user = saved

if st.session_state.user is None:
    restore_login()

# =========================
# AUTH FUNCTIONS
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

    if st.button("Create Account"):
        if u in USERS:
            st.error("User already exists")
        else:
            USERS[u] = {
                "password": hash_pass(p),
                "email": e,
                "credits": 10
            }
            save_users()
            st.success("Account created!")

def logout():
    cookies["user"] = ""
    cookies.save()
    st.session_state.user = None
    st.rerun()

# =========================
# ROUTING (FIXED)
# =========================
if not st.session_state.user:

    page = st.radio("Account", ["Login", "Register"], horizontal=True)

    if page == "Login":
        login()
    else:
        register()

    st.stop()

# =========================
# DASHBOARD
# =========================
st.title("📸 BULK PHOTO SAAS ULTIMATE")
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
# RESIZE PRESETS
# =========================
st.subheader("Resize")

preset = st.selectbox(
    "Choose Type",
    ["Custom", "CNIC", "Passport", "Job", "CV", "A4"]
)

size_map = {
    "CNIC": (413, 531),
    "Passport": (600, 600),
    "Job": (300, 300),
    "CV": (400, 400),
    "A4": (1080, 1350),
    "Custom": (300, 300)
}

w, h = size_map[preset]

width = st.number_input("Width", value=w)
height = st.number_input("Height", value=h)

# =========================
# SETTINGS
# =========================
bg = st.selectbox("Background", ["none", "white", "blue", "black"])
fmt = st.selectbox("Format", ["JPG", "PNG", "WEBP"])
enhance = st.checkbox("Enhance Image", True)

# =========================
# ENHANCE
# =========================
def enhance_img(img):
    img = ImageEnhance.Sharpness(img).enhance(2)
    img = ImageEnhance.Contrast(img).enhance(1.5)
    return img

# =========================
# BG REMOVE SAFE
# =========================
def safe_remove(img):
    out = remove(img)
    if isinstance(out, (bytes, bytearray)):
        return Image.open(io.BytesIO(out))
    return out

# =========================
# BG APPLY
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
    with zipfile.ZipFile(zip_buffer, "w") as zipf:

        for i, file in enumerate(images):

            img = Image.open(file)

            img = safe_remove(img).convert("RGBA")

            img = img.resize((int(width), int(height)))

            if enhance:
                img = enhance_img(img)

            img = apply_bg(img, bg)

            buffer = io.BytesIO()

            save_format = fmt.upper()
            save_img = img.convert("RGB") if fmt != "PNG" else img

            save_img.save(buffer, format=save_format)
            zipf.writestr(f"image_{i+1}.{fmt.lower()}", buffer.getvalue())

            # history save
            st.session_state.history.append({
                "user": st.session_state.user,
                "time": str(datetime.now()),
                "size": f"{width}x{height}",
                "format": fmt
            })

    save_history()

    st.success("Done!")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="photos.zip"
    )

# =========================
# HISTORY
# =========================
st.divider()
st.subheader("History")

for h in reversed(st.session_state.history[-10:]):
    st.write(h)
