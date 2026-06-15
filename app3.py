import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
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
st.set_page_config(page_title="Pro Photo SaaS", layout="wide")

# =========================
# COOKIE SYSTEM
# =========================
cookies = EncryptedCookieManager(
    prefix="pro_saas",
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
                "credits": 999
            },
            "user": {
                "password": hashlib.sha256("user123".encode()).hexdigest(),
                "credits": 20
            }
        }

def save_users():
    with open(DB_FILE, "w") as f:
        json.dump(st.session_state.USERS, f)

# =========================
# INIT STATE
# =========================
if "USERS" not in st.session_state:
    st.session_state.USERS = load_users()

if "user" not in st.session_state:
    st.session_state.user = None

if "history" not in st.session_state:
    st.session_state.history = []

USERS = st.session_state.USERS

# =========================
# AUTH RESTORE
# =========================
def restore_login():
    u = cookies.get("user")
    if u and u in USERS:
        st.session_state.user = u

if st.session_state.user is None:
    restore_login()

# =========================
# AUTH FUNCTIONS
# =========================
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login():
    st.title("🔐 Pro SaaS Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == hash_pass(p):
            st.session_state.user = u
            cookies["user"] = u
            cookies.save()
            st.rerun()
        else:
            st.error("Invalid login")

def logout():
    cookies["user"] = ""
    cookies.save()
    st.session_state.user = None
    st.rerun()

# =========================
# AUTH ROUTE
# =========================
if not st.session_state.user:
    login()
    st.stop()

# =========================
# DASHBOARD
# =========================
st.title("🚀 PRO PHOTO SaaS STUDIO")
st.success(f"Welcome {st.session_state.user}")

if st.button("Logout"):
    logout()

# =========================
# UPLOAD + CAMERA (PRO UI)
# =========================
col1, col2 = st.columns(2)

with col1:
    files = st.file_uploader(
        "Upload Images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True
    )

with col2:
    with st.expander("📷 Camera Capture"):
        camera = st.camera_input("Take Photo")

images = []
if files:
    images.extend(files)
if camera:
    images.append(camera)

# =========================
# SETTINGS
# =========================
preset = st.selectbox("Size", ["Passport","NADRA","HD","Custom"])

sizes = {
    "Passport": (300,300),
    "NADRA": (400,400),
    "HD": (800,1000),
    "Custom": (500,500)
}

w, h = sizes[preset]

enhance = st.checkbox("AI Enhance", True)
remove_bg = st.checkbox("Remove BG", True)

# =========================
# PROCESS ENGINE
# =========================
if images and st.button("PROCESS PRO"):

    zip_buf = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buf, "w") as zipf:

        for i, f in enumerate(images):

            img = Image.open(f)

            if remove_bg:
                out = remove(img)
                img = Image.open(io.BytesIO(out)).convert("RGBA")
            else:
                img = img.convert("RGB")

            img = img.resize((w, h))

            if enhance:
                img = ImageEnhance.Sharpness(img).enhance(2.8)
                img = ImageEnhance.Contrast(img).enhance(1.4)
                img = img.filter(ImageFilter.UnsharpMask(2,150,3))

            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)

            zipf.writestr(f"pro_{i+1}.jpg", buf.getvalue())

            progress.progress((i+1)/len(images))

    st.success("PRO Processing Done")

    st.download_button(
        "Download PRO ZIP",
        zip_buf.getvalue(),
        file_name="pro_output.zip"
    )
