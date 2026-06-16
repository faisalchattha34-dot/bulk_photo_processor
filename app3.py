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
# PAGE CONFIG (MODERN UI)
# =========================
st.set_page_config(
    page_title="Bulk Photo SaaS PRO",
    layout="wide",
    page_icon="📸"
)

# =========================
# CUSTOM CSS (SAAS LOOK)
# =========================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg,#0f172a,#1e293b);
}

.main {
    background-color: transparent;
}

.block-container {
    padding: 2rem;
}

.stButton > button {
    background: linear-gradient(90deg,#6366f1,#3b82f6);
    color: white;
    border-radius: 12px;
    height: 45px;
    font-weight: bold;
    border: none;
}

.stButton > button:hover {
    transform: scale(1.02);
}

.card {
    background: rgba(255,255,255,0.05);
    padding: 15px;
    border-radius: 15px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.1);
}

h1, h2, h3 {
    color: white;
}

label {
    color: #cbd5e1 !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# COOKIE MANAGER
# =========================
cookies = EncryptedCookieManager(
    prefix="photo_saas",
    password="super_secure_key_123"
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

if "page" not in st.session_state:
    st.session_state.page = "login"

if "history" not in st.session_state:
    st.session_state.history = []

USERS = st.session_state.USERS

# =========================
# LOGIN RESTORE
# =========================
def restore_login():
    try:
        saved_user = cookies.get("user")
        if saved_user and saved_user in USERS:
            st.session_state.user = saved_user
            return True
    except:
        pass
    return False

if st.session_state.user is None:
    restore_login()

# =========================
# HASH
# =========================
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

# =========================
# LOGIN UI (MODERN CARD)
# =========================
def login():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.title("🔐 Login to Bulk Photo SaaS")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            if u in USERS and USERS[u]["password"] == hash_pass(p):
                st.session_state.user = u
                cookies["user"] = u
                cookies.save()
                st.rerun()
            else:
                st.error("Invalid credentials")

    with col2:
        if st.button("Create Account"):
            st.session_state.page = "register"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# REGISTER UI
# =========================
def register():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.title("📝 Create Account")

    u = st.text_input("Username")
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Register"):
            if u in USERS:
                st.error("User already exists")
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

    with col2:
        if st.button("Back"):
            st.session_state.page = "login"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# LOGOUT
# =========================
def logout():
    cookies["user"] = ""
    cookies.save()
    st.session_state.user = None
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
# DASHBOARD HEADER
# =========================
st.markdown(f"""
# 📸 Bulk Photo SaaS PRO
### Welcome back, **{st.session_state.user}**
""")

col1, col2, col3 = st.columns(3)

col1.markdown("<div class='card'>⚡ Fast Processing</div>", unsafe_allow_html=True)
col2.markdown("<div class='card'>📁 Bulk Upload</div>", unsafe_allow_html=True)
col3.markdown("<div class='card'>☁️ ZIP Export</div>", unsafe_allow_html=True)

if st.button("🚪 Logout"):
    logout()

st.divider()

# =========================
# UPLOAD SECTION
# =========================
st.subheader("📤 Upload Images")

col1, col2 = st.columns(2)

with col1:
    files = st.file_uploader("Upload Images", type=["png","jpg","jpeg","webp"], accept_multiple_files=True)

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
st.subheader("⚙️ Processing Settings")

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

bg_color = st.selectbox("Background", ["none","white","blue","red","black"])
output_format = st.selectbox("Format", ["JPG","PNG","WEBP"])

remove_bg = st.checkbox("Remove Background", True)
enhance = st.checkbox("Enhance Image", True)

prefix = st.text_input("File Prefix", "photo")

# =========================
# COMPRESSION
# =========================
st.subheader("🗜 Compression")

size_type = st.selectbox("Unit", ["KB","MB","GB"])
size_value = st.number_input("Target Size", min_value=1, value=100)

if size_type == "KB":
    target_bytes = size_value * 1024
elif size_type == "MB":
    target_bytes = size_value * 1024 * 1024
else:
    target_bytes = size_value * 1024 * 1024 * 1024

st.info(f"Target Size per image: {target_bytes/1024:.2f} KB")

# =========================
# PROCESS
# =========================
def enhance_img(img):
    img = ImageEnhance.Sharpness(img).enhance(2.5)
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = ImageEnhance.Brightness(img).enhance(1.1)
    return img

color_map = {
    "white": (255,255,255),
    "blue": (0,0,255),
    "red": (255,0,0),
    "black": (0,0,0)
}

if images and st.button("🚀 PROCESS IMAGES"):

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w") as zipf:

        for i, file in enumerate(images):

            img = Image.open(file)

            if remove_bg:
                img = remove(img).convert("RGBA")
            else:
                img = img.convert("RGB")

            img = img.resize((width, height))

            if enhance:
                img = enhance_img(img)

            if bg_color != "none":
                base = Image.new("RGB", img.size, color_map[bg_color])
                if img.mode == "RGBA":
                    base.paste(img, mask=img.split()[-1])
                img = base

            img = img.convert("RGB")

            buffer = io.BytesIO()
            quality = 90

            if output_format == "JPG":
                while True:
                    temp = io.BytesIO()
                    img.save(temp, format="JPEG", quality=quality, optimize=True)
                    if len(temp.getvalue()) <= target_bytes or quality <= 10:
                        buffer = temp
                        break
                    quality -= 5
                name = f"{prefix}_{i+1}.jpg"

            elif output_format == "PNG":
                img.save(buffer, format="PNG", optimize=True)
                name = f"{prefix}_{i+1}.png"

            else:
                while True:
                    temp = io.BytesIO()
                    img.save(temp, format="WEBP", quality=quality)
                    if len(temp.getvalue()) <= target_bytes or quality <= 10:
                        buffer = temp
                        break
                    quality -= 5
                name = f"{prefix}_{i+1}.webp"

            zipf.writestr(name, buffer.getvalue())
            progress.progress((i+1)/len(images))

    st.success("Processing Complete 🎉")

    st.download_button(
        "⬇ Download ZIP",
        zip_buffer.getvalue(),
        file_name="bulk_photos.zip"
    )
