import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
import zipfile
import io
import hashlib
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Smart Photo SaaS PRO", layout="wide")

# =========================
# COOKIE
# =========================
cookies = EncryptedCookieManager(
    prefix="photo_saas",
    password="secure_key_123"
)

if not cookies.ready():
    st.stop()

# =========================
# USERS (SIMPLE)
# =========================
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {"password": hash_pass("admin123"), "credits": 999},
        "user": {"password": hash_pass("user123"), "credits": 20}
    }

users = st.session_state.users

# =========================
# SESSION
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "login"

# =========================
# LOGIN RESTORE
# =========================
def restore():
    saved = cookies.get("user")
    if saved in users:
        st.session_state.user = saved

restore()

# =========================
# AUTH
# =========================
def login():
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u]["password"] == hash_pass(p):
            st.session_state.user = u
            cookies["user"] = u
            cookies.save()
            st.rerun()
        else:
            st.error("Invalid login")

    if st.button("Register"):
        st.session_state.page = "register"
        st.rerun()

def register():
    st.title("📝 Register")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Create"):
        if u in users:
            st.error("User exists")
        else:
            users[u] = {"password": hash_pass(p), "credits": 10}
            st.success("Created")
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

user = st.session_state.user

# =========================
# DASHBOARD
# =========================
st.title("🚀 Smart Photo SaaS PRO")
st.success(f"Welcome {user}")
st.info(f"Credits: {users[user]['credits']}")

# =========================
# INPUT (UPLOAD + CAMERA)
# =========================
files = st.file_uploader("Upload Images", accept_multiple_files=True, type=["png","jpg","jpeg"])
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

preset_map = {
    "Passport": (300,300),
    "NADRA": (400,400),
    "Job": (300,400),
    "HD": (1024,1024),
    "Custom": (300,300)
}

w, h = preset_map[preset]

width = st.number_input("Width", value=w)
height = st.number_input("Height", value=h)

bg_color = st.selectbox("Background Color", ["white","blue","red","black"])
remove_bg = st.checkbox("Remove Background", True)
enhance = st.checkbox("Enhance Image", True)

dpi = st.selectbox("DPI", [72,150,300,600])

# SIZE CONTROL
size_type = st.selectbox("Size Type", ["KB","MB","GB"])
target_size = st.number_input("Target Size", value=200)

prefix = st.text_input("File Name", "photo")

bg_map = {
    "white": (255,255,255),
    "blue": (0,102,255),
    "red": (255,0,0),
    "black": (0,0,0)
}

# =========================
# SIZE CONVERTER
# =========================
def size_to_kb(value, typ):
    if typ == "KB":
        return value
    if typ == "MB":
        return value * 1024
    if typ == "GB":
        return value * 1024 * 1024

# =========================
# COMPRESS FUNCTION
# =========================
def compress(img, target_kb):
    q = 95
    while q > 10:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q, dpi=(dpi, dpi))
        if len(buf.getvalue()) / 1024 <= target_kb:
            return buf.getvalue()
        q -= 5
    return buf.getvalue()

# =========================
# PROCESS
# =========================
if images and st.button("PROCESS ALL"):

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    preview = False

    for i, file in enumerate(images):

        img = Image.open(file)

        # REMOVE BG
        if remove_bg:
            cut = remove(img)
            img = Image.open(io.BytesIO(cut)).convert("RGBA")
            bg = Image.new("RGBA", img.size, bg_map[bg_color])
            img = Image.alpha_composite(bg, img).convert("RGB")
        else:
            img = img.convert("RGB")

        # RESIZE
        img = img.resize((int(width), int(height)))

        # ENHANCE
        if enhance:
            img = ImageEnhance.Sharpness(img).enhance(2.5)
            img = ImageEnhance.Contrast(img).enhance(1.3)
            img = img.filter(ImageFilter.UnsharpMask(2,150,3))

        # PREVIEW
        if not preview:
            st.image(img, width=200)
            preview = True

        # COMPRESS
        final = compress(img, size_to_kb(target_size, size_type))

        zip_buffer = zip_buffer
        with zipfile.ZipFile(zip_buffer, "a") as zipf:
            zipf.writestr(f"{prefix}_{i+1}.jpg", final)

        progress.progress((i+1)/len(images))

    st.success("Processing Done")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="photos.zip"
    )
