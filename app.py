import streamlit as st
from PIL import Image, ImageEnhance
from rembg import remove
import zipfile
import io
import json
import hashlib

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Bulk Photo SaaS PRO FINAL", layout="wide")

# =========================
# COOKIE (SAFE INIT)
# =========================
try:
    from streamlit_cookies_manager import EncryptedCookieManager

    cookies = EncryptedCookieManager(
        prefix="master_saas",
        password="super_secure_key"
    )

    if not cookies.ready():
        st.stop()

except:
    cookies = None

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
            "admin": {"password": hashlib.sha256("admin123".encode()).hexdigest(), "credits": 999},
            "user": {"password": hashlib.sha256("user123".encode()).hexdigest(), "credits": 50}
        }

def save_users():
    with open(DB_FILE, "w") as f:
        json.dump(st.session_state.USERS, f)

# =========================
# SESSION INIT (SAFE)
# =========================
if "USERS" not in st.session_state:
    st.session_state.USERS = load_users()

if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "login"

USERS = st.session_state.USERS

# =========================
# LOGIN RESTORE
# =========================
def restore_login():
    if cookies:
        saved = cookies.get("user")
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
            if cookies:
                cookies["user"] = u
                cookies.save()
            st.rerun()
        else:
            st.error("Invalid credentials")

    if st.button("Register"):
        st.session_state.page = "register"
        st.rerun()

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
                "credits": 20
            }
            save_users()
            st.success("Account created")
            st.session_state.page = "login"
            st.rerun()

# =========================
# ROUTING
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
user = st.session_state.user
st.title("🚀 BULK PHOTO SaaS PRO FINAL")
st.success(f"Welcome {user}")

# FIX KeyError SAFE ACCESS
credits = USERS.get(user, {}).get("credits", 0)
st.info(f"Credits: {credits}")

# =========================
# UPLOAD + CAMERA
# =========================
st.subheader("Upload / Camera")

files = st.file_uploader("Upload Images", type=["png","jpg","jpeg","webp"], accept_multiple_files=True)
camera = st.camera_input("Camera")

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

bg_on = st.checkbox("Background Apply", True)
bg_color = st.selectbox("Background Color", ["white","blue","red","black"])

dpi = st.number_input("DPI", 72, 600, 300)

enhance = st.checkbox("Enhance Image", True)

size_type = st.selectbox("Size Type", ["KB","MB","GB"])
target_size = st.number_input("Target Size", 10, 5000, 200)

prefix = st.text_input("File Name", "photo")

bg_map = {
    "white": (255,255,255),
    "blue": (0,102,255),
    "red": (255,0,0),
    "black": (0,0,0)
}

# =========================
# SIZE CONVERT
# =========================
def size_to_kb(value, unit):
    if unit == "KB":
        return value
    if unit == "MB":
        return value * 1024
    if unit == "GB":
        return value * 1024 * 1024

# =========================
# COMPRESS
# =========================
def compress(img, target_kb):
    quality = 95
    while quality > 10:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, dpi=(dpi, dpi))
        if len(buf.getvalue())/1024 <= target_kb:
            return buf.getvalue()
        quality -= 5
    return buf.getvalue()

# =========================
# PROCESS
# =========================
if images and st.button("PROCESS ALL"):

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w") as zipf:

        preview_done = False

        for i, file in enumerate(images):

            img = Image.open(file)

            # =========================
            # BACKGROUND SYSTEM FIXED
            # =========================
            if bg_on:
                try:
                    cut = remove(img)
                    img = Image.open(io.BytesIO(cut)).convert("RGBA")
                except:
                    img = img.convert("RGBA")

                bg = Image.new("RGBA", img.size, bg_map[bg_color])
                img = Image.alpha_composite(bg, img).convert("RGB")
            else:
                img = img.convert("RGB")

            # resize
            img = img.resize((int(width), int(height)))

            # enhance
            if enhance:
                img = ImageEnhance.Sharpness(img).enhance(2.5)
                img = ImageEnhance.Contrast(img).enhance(1.3)

            # preview
            if not preview_done:
                st.image(img, width=200)
                preview_done = True

            # size convert
            kb_target = size_to_kb(target_size, size_type)

            final = compress(img, kb_target)

            zipf.writestr(f"{prefix}_{i+1}.jpg", final)

            progress.progress((i+1)/len(images))

    st.success("Processing Done")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="output.zip"
    )
