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
st.set_page_config(page_title="Bulk Photo SaaS FINAL FIX", layout="wide")

# =========================
# COOKIE
# =========================
cookies = EncryptedCookieManager(
    prefix="photo_saas",
    password="super_secure_key"
)

if not cookies.ready():
    st.stop()

# =========================
# DB
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
# SESSION
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
        if st.button("Register Here"):
            st.session_state.page = "register"
            st.rerun()

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
        if st.button("Back to Login"):
            st.session_state.page = "login"
            st.rerun()

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
user = st.session_state.user

st.title("📸 BULK PHOTO SAAS FINAL SYSTEM")
st.success(f"Welcome {user}")

if st.button("Logout"):
    logout()

# =========================
# UPLOAD + SMALL CAMERA UI (UPDATED)
# =========================
st.subheader("Upload / Camera")

col1, col2 = st.columns(2)

with col1:
    files = st.file_uploader("Upload Images", type=["png","jpg","jpeg","webp"], accept_multiple_files=True)

with col2:
    st.caption("📷 Camera")
    camera = st.camera_input("Take Photo", label_visibility="collapsed")

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

bg_color = st.selectbox("Background Color", ["none","white","blue","red","black"])
output_format = st.selectbox("Format", ["JPG","PNG","WEBP"])

remove_bg = st.checkbox("Remove BG", True)
enhance = st.checkbox("AI Enhance", True)

prefix = st.text_input("File Prefix", "photo")

# =========================
# DPI (CUSTOM + PRESET)
# =========================
st.subheader("DPI Settings")

dpi_mode = st.radio("DPI Mode", ["Preset", "Custom"], horizontal=True)

if dpi_mode == "Preset":
    dpi = st.selectbox("Select DPI", [72,150,300,600])
else:
    dpi = st.number_input("Enter DPI", min_value=10, max_value=5000, value=300)

# =========================
# ENHANCE
# =========================
def enhance_img(img):
    img = ImageEnhance.Sharpness(img).enhance(3.0)
    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = ImageEnhance.Brightness(img).enhance(1.1)
    img = img.filter(ImageFilter.UnsharpMask(2,200,3))
    return img

# =========================
# PROCESS
# =========================
if images and st.button("PROCESS"):

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    preview_area = st.empty()

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
                base = Image.new("RGB", img.size, bg_color)
                if img.mode == "RGBA":
                    base.paste(img, mask=img.split()[-1])
                img = base

            if img.mode != "RGB":
                img = img.convert("RGB")

            # 🔥 LIVE PREVIEW AFTER PROCESS
            preview_area.image(img, caption=f"Processed {i+1}", width=220)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=90, dpi=(dpi, dpi))
            buffer.seek(0)

            zipf.writestr(f"{prefix}_{i+1}.jpg", buffer.getvalue())

            progress.progress((i+1)/len(images))

    st.session_state.history.append({
        "user": user,
        "files": len(images),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    st.success("Done")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="output.zip"
    )

# =========================
# HISTORY (BEAUTIFUL UI)
# =========================
st.divider()
st.subheader("📊 History (User Activity)")

if not st.session_state.history:
    st.info("No history yet")

for h in reversed(st.session_state.history):
    st.markdown(f"""
    ---
    👤 **User:** {h['user']}  
    📁 **Files:** {h['files']}  
    🕒 **Time:** {h['time']}  
    """)
