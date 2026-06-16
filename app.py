import streamlit as st
from PIL import Image, ImageEnhance
from rembg import remove
import zipfile
import io
import json
import hashlib
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Bulk Photo SaaS PRO FIX V6", layout="wide")

# =========================
# COOKIE
# =========================
cookies = EncryptedCookieManager(
    prefix="master_saas",
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
            "admin": {"password": hashlib.sha256("admin123".encode()).hexdigest(), "credits": 999},
            "user": {"password": hashlib.sha256("user123".encode()).hexdigest(), "credits": 20}
        }

def save_users():
    with open(DB_FILE, "w") as f:
        json.dump(st.session_state.USERS, f)

# =========================
# SESSION
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
            st.error("User exists")
        else:
            USERS[u] = {
                "password": hash_pass(p),
                "email": e,
                "credits": 10
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

st.title("🚀 BULK PHOTO SaaS PRO V6")
st.success(f"Welcome {user}")
st.info(f"Credits: {USERS[user]['credits']}")

# =========================
# UPLOAD
# =========================
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

bg_color = st.selectbox("Background", ["white","blue","red","black"])

# ✅ DPI FIX (custom + apply)
dpi = st.number_input("DPI (custom)", min_value=72, max_value=600, value=300)

output_format = st.selectbox("Format", ["JPG","PNG","WEBP"])
remove_bg = st.checkbox("Remove Background", True)
enhance = st.checkbox("Enhance Image", True)

target_kb = st.number_input("Target Size KB", 10, 5000, 200)
prefix = st.text_input("File Name", "photo")

# =========================
# BG COLORS
# =========================
bg_map = {
    "white": (255,255,255),
    "blue": (0,102,255),
    "red": (255,0,0),
    "black": (0,0,0)
}

# =========================
# COMPRESS
# =========================
def compress(img, target_kb):
    quality = 95
    while quality > 10:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, dpi=(dpi, dpi))
        if len(buf.getvalue()) / 1024 <= target_kb:
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

        preview = False

        for i, file in enumerate(images):

            img = Image.open(file)

            # =========================
            # FIXED BACKGROUND SYSTEM
            # =========================
            if remove_bg:
                try:
                    cut = remove(img)
                    img = Image.open(io.BytesIO(cut)).convert("RGBA")
                except:
                    img = img.convert("RGBA")

                bg = Image.new("RGBA", img.size, bg_map[bg_color])

                # FIX: proper alpha composite safety
                img = Image.alpha_composite(bg, img).convert("RGB")

            else:
                img = img.convert("RGB")

            # resize
            img = img.resize((int(width), int(height)))

            # enhance
            if enhance:
                img = ImageEnhance.Sharpness(img).enhance(2.5)
                img = ImageEnhance.Contrast(img).enhance(1.3)

            # preview once
            if not preview:
                st.image(img, width=200)
                preview = True

            # compress with DPI
            final = compress(img, target_kb)

            zipf.writestr(f"{prefix}_{i+1}.jpg", final)

            progress.progress((i+1)/len(images))

    st.success("Processing Done")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="output.zip"
    )
