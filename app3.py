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
st.set_page_config(page_title="Bulk Photo SaaS PRO+ Commercial", layout="wide")

# =========================
# COOKIE SYSTEM
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
            "admin": {
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "credits": 999,
                "plan": "pro"
            },
            "user": {
                "password": hashlib.sha256("user123".encode()).hexdigest(),
                "credits": 20,
                "plan": "free"
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
# AUTO LOGIN (FIXED)
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
# AUTH ROUTE
# =========================
if not st.session_state.user:
    login()
    st.stop()

# =========================
# DASHBOARD
# =========================
user = st.session_state.user
st.title("🚀 MASTER BULK PHOTO SAAS (COMMERCIAL READY)")
st.success(f"Welcome {user}")

plan = USERS[user].get("plan", "free")
st.info(f"Plan: {plan} | Credits: {USERS[user]['credits']}")

if st.button("Logout"):
    logout()

# =========================
# CREDIT SYSTEM (SAFE)
# =========================
def use_credit(n):
    if USERS[user]["credits"] >= n:
        USERS[user]["credits"] -= n
        save_users()
        return True
    return False

# =========================
# UPLOAD + CAMERA (RESTORED FULL)
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
    with st.expander("📷 Camera Capture", expanded=False):
        camera = st.camera_input("Take Photo")

images = []
if files:
    images.extend(files)
if camera:
    images.append(camera)

# =========================
# SETTINGS (ALL RESTORED)
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
output_format = st.selectbox("Format", ["JPG","PNG","WEBP"])
dpi = st.selectbox("DPI", [72,150,300])

remove_bg = st.checkbox("Remove Background (AI)", True)
enhance = st.checkbox("Enhance Image (Clear Mode)", True)

prefix = st.text_input("File Prefix", "photo")

# =========================
# COMMERCIAL LIMIT (ADD ON ONLY)
# =========================
if len(images) > 50:
    st.error("Max 50 images per batch allowed")
    st.stop()

# =========================
# PROCESS ENGINE (FULL POWER RESTORED)
# =========================
if images and st.button("PROCESS ALL"):

    if not use_credit(len(images)):
        st.error("Not enough credits")
        st.stop()

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w") as zipf:

        preview = False

        for i, file in enumerate(images):

            img = Image.open(file)

            # background remove
            if remove_bg:
                out = remove(img)
                img = Image.open(io.BytesIO(out)).convert("RGBA")
            else:
                img = img.convert("RGB")

            img = img.resize((width, height))

            # ENHANCEMENT (FULL RESTORED)
            if enhance:
                img = ImageEnhance.Sharpness(img).enhance(2.5)
                img = ImageEnhance.Contrast(img).enhance(1.3)
                img = ImageEnhance.Brightness(img).enhance(1.05)
                img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

            if not preview:
                st.image(img, width=200)
                preview = True

            buffer = io.BytesIO()
            save_format = "JPEG" if output_format == "JPG" else output_format

            img.save(buffer, format=save_format, dpi=(dpi, dpi))
            buffer.seek(0)

            zipf.writestr(f"{prefix}_{i+1}.{output_format.lower()}", buffer.getvalue())

            progress.progress((i+1)/len(images))

    st.session_state.history.append({
        "user": user,
        "files": len(images),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[-20:]

    st.success("Processing Complete")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="output.zip"
    )

# =========================
# HISTORY (RESTORED)
# =========================
st.divider()
st.subheader("History")

for h in reversed(st.session_state.history):
    st.write(h)
