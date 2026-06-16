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
st.set_page_config(page_title="Bulk Photo SaaS FIXED", layout="wide")

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
        if saved_user:
            saved_user = str(saved_user).strip()
            if saved_user in USERS:
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
# LOGIN
# =========================
def login():
    st.title("🔐 Login")

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
        if st.button("Register"):
            st.session_state.page = "register"
            st.rerun()

# =========================
# REGISTER
# =========================
def register():
    st.title("📝 Register")

    u = st.text_input("Username")
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Create Account"):
            if not u or not e or not p:
                st.error("All fields required")
            elif u in USERS:
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
# DASHBOARD
# =========================
st.title("📸 BULK PHOTO SaaS FIXED SYSTEM")
st.success(f"Welcome {st.session_state.user}")

if st.button("Logout"):
    logout()

# =========================
# UPLOAD
# =========================
st.subheader("Upload / Camera")

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

remove_bg = st.checkbox("Remove BG", True)
enhance = st.checkbox("Enhance", True)

prefix = st.text_input("File Prefix", "photo")

# =========================
# DPI
# =========================
st.subheader("DPI Settings")

dpi_mode = st.radio("DPI Mode", ["Preset", "Manual"], horizontal=True)

if dpi_mode == "Preset":
    dpi = st.selectbox("Select DPI", [72, 150, 300, 600])
else:
    dpi = st.number_input("Enter Custom DPI", min_value=10, max_value=5000, value=300)

# =========================
# COMPRESSION (KB/MB/GB FIXED)
# =========================
st.subheader("Compression Settings")

size_type = st.selectbox("Select Unit", ["KB", "MB", "GB"])
size_value = st.number_input("Enter Size", min_value=1, value=100)

# convert to bytes
if size_type == "KB":
    target_bytes = size_value * 1024
elif size_type == "MB":
    target_bytes = size_value * 1024 * 1024
else:
    target_bytes = size_value * 1024 * 1024 * 1024

st.info(f"Target per image: {target_bytes/1024:.2f} KB")

# =========================
# ENHANCE
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

# =========================
# PROCESS
# =========================
if images and st.button("PROCESS"):

    zip_buffer = io.BytesIO()
    progress = st.progress(0)
    preview = st.empty()

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

            preview.image(img, caption=f"Processed {i+1}", width=200)

            buffer = io.BytesIO()

            fmt = output_format
            quality_try = 95

            # =========================
            # SMART COMPRESSION ENGINE
            # =========================
            if fmt == "JPG":
                img = img.convert("RGB")

                while True:
                    temp = io.BytesIO()
                    img.save(temp, format="JPEG", quality=quality_try, dpi=(dpi, dpi), optimize=True)

                    if len(temp.getvalue()) <= target_bytes or quality_try <= 10:
                        buffer = temp
                        break

                    quality_try -= 5

                file_name = f"{prefix}_{i+1}.jpg"

            elif fmt == "PNG":
                img.save(buffer, format="PNG", dpi=(dpi, dpi), optimize=True)
                file_name = f"{prefix}_{i+1}.png"

            elif fmt == "WEBP":
                while True:
                    temp = io.BytesIO()
                    img.save(temp, format="WEBP", quality=quality_try, dpi=(dpi, dpi), method=6)

                    if len(temp.getvalue()) <= target_bytes or quality_try <= 10:
                        buffer = temp
                        break

                    quality_try -= 5

                file_name = f"{prefix}_{i+1}.webp"

            buffer.seek(0)
            zipf.writestr(file_name, buffer.getvalue())

            progress.progress((i+1)/len(images))

    st.success("Processing Done")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="processed_images.zip"
    )

# =========================
# HISTORY
# =========================
st.divider()
st.subheader("History")

if not st.session_state.history:
    st.info("No history yet")
else:
    for h in reversed(st.session_state.history):
        st.write(f"👤 {h['user']} | 📁 {h['files']} files | 🕒 {h['time']}")
