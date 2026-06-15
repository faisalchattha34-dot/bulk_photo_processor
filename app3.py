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
st.set_page_config(page_title="Commercial Photo SaaS", layout="wide")

# =========================
# COOKIE SYSTEM
# =========================
cookies = EncryptedCookieManager(
    prefix="comm_saas",
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
# INIT
# =========================
if "USERS" not in st.session_state:
    st.session_state.USERS = load_users()

if "user" not in st.session_state:
    st.session_state.user = None

if "history" not in st.session_state:
    st.session_state.history = []

USERS = st.session_state.USERS

# =========================
# AUTH RESTORE SAFE
# =========================
def restore_login():
    u = cookies.get("user")
    if u and u in USERS:
        st.session_state.user = u

if st.session_state.user is None:
    restore_login()

# =========================
# AUTH
# =========================
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login():
    st.title("🔐 Commercial SaaS Login")

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
# ROUTING
# =========================
if not st.session_state.user:
    login()
    st.stop()

# =========================
# DASHBOARD
# =========================
user = st.session_state.user
st.title("🏢 COMMERCIAL PHOTO SaaS PLATFORM")
st.success(f"Welcome {user}")

plan = USERS[user].get("plan", "free")
credits = USERS[user]["credits"]

st.info(f"Plan: {plan.upper()} | Credits: {credits}")

if st.button("Logout"):
    logout()

# =========================
# CREDIT SYSTEM (COMMERCIAL LOGIC)
# =========================
def use_credit(n):
    if USERS[user]["credits"] >= n:
        USERS[user]["credits"] -= n
        save_users()
        return True
    return False

# =========================
# INPUTS (UPLOAD + CAMERA)
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
preset = st.selectbox("Preset", ["Passport","NADRA","HD","Custom"])

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
# COMMERCIAL LIMIT
# =========================
if len(images) > 20:
    st.error("Free limit: Max 20 images per batch")
    st.stop()

# =========================
# PROCESS ENGINE
# =========================
if images and st.button("PROCESS (PRO)"):

    if not use_credit(len(images)):
        st.error("Not enough credits")
        st.stop()

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
                img = ImageEnhance.Sharpness(img).enhance(2.5)
                img = ImageEnhance.Contrast(img).enhance(1.3)
                img = img.filter(ImageFilter.UnsharpMask(2,150,3))

            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)

            zipf.writestr(f"comm_{i+1}.jpg", buf.getvalue())

            progress.progress((i+1)/len(images))

    st.session_state.history.append({
        "user": user,
        "files": len(images),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    st.success("Commercial Processing Done")

    st.download_button(
        "Download Output",
        zip_buf.getvalue(),
        file_name="commercial_output.zip"
    )

# =========================
# HISTORY
# =========================
st.divider()
st.subheader("Usage History")

for h in reversed(st.session_state.history):
    st.write(h)
