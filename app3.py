import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
import zipfile
import io
from datetime import datetime
import json
import hashlib
from streamlit_cookies_manager import EncryptedCookieManager

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Bulk Photo SaaS V6.1", layout="wide")

# =========================
# COOKIE MANAGER
# =========================
cookies = EncryptedCookieManager(
    prefix="photo_saas",
    password="my_secret_password"
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
            },
            "user": {
                "password": hashlib.sha256("user123".encode()).hexdigest(),
                "email": "user@demo.com",
                "credits": 20
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

if "credits" not in st.session_state:
    st.session_state.credits = 0

if "history" not in st.session_state:
    st.session_state.history = []

if "page" not in st.session_state:
    st.session_state.page = "login"

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
        st.session_state.credits = USERS[saved]["credits"]

if st.session_state.user is None:
    restore_login()

# =========================
# HASH
# =========================
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

# =========================
# REGISTER
# =========================
def register():
    st.title("📝 Register")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if not username or not email or not password:
            st.error("All fields required")
        elif username in USERS:
            st.error("User already exists")
        else:
            USERS[username] = {
                "password": hash_pass(password),
                "email": email,
                "credits": 10
            }
            save_users()
            st.success("Account created")
            st.session_state.page = "login"
            st.rerun()

# =========================
# LOGIN
# =========================
def login():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            if username in USERS and USERS[username]["password"] == hash_pass(password):

                st.session_state.user = username
                st.session_state.credits = USERS[username]["credits"]

                cookies["user"] = username
                cookies.save()

                st.success("Login Successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with col2:
        if st.button("Register"):
            st.session_state.page = "register"
            st.rerun()

# =========================
# LOGOUT
# =========================
def logout():
    cookies["user"] = ""
    cookies.save()

    st.session_state.user = None
    st.session_state.credits = 0
    st.session_state.page = "login"

    st.rerun()

# =========================
# AUTH ROUTING
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
st.title("📸 Bulk Photo SaaS V6.1")
st.success(f"Welcome {st.session_state.user} | Credits: {st.session_state.credits}")

if st.button("Logout"):
    logout()

# =========================
# CREDIT SYSTEM
# =========================
def use_credit(n):
    if USERS[st.session_state.user]["credits"] >= n:
        USERS[st.session_state.user]["credits"] -= n
        st.session_state.credits = USERS[st.session_state.user]["credits"]
        save_users()
        return True
    return False

# =========================
# UPLOAD + CAMERA (CLEAN UI FIX)
# =========================
st.subheader("Upload / Capture")

col1, col2 = st.columns(2)

with col1:
    files = st.file_uploader(
        "Upload Images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True
    )

with col2:
    with st.expander("📷 Camera (Click to open)", expanded=False):
        camera = st.camera_input("Take Photo")

all_files = []

if files:
    all_files.extend(files)

if camera:
    all_files.append(camera)

files = all_files

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

output_format = st.selectbox("Format", ["JPG","PNG","WEBP"])
remove_bg = st.checkbox("Remove Background", True)
enhance = st.checkbox("Enhance Image", True)
prefix = st.text_input("File Prefix", "photo")

dpi = st.selectbox("DPI", [72,150,300])

# =========================
# PROCESS
# =========================
if files and st.button("PROCESS"):

    if not use_credit(len(files)):
        st.error("Not enough credits")
        st.stop()

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w") as zipf:

        preview = False

        for i, file in enumerate(files):

            img = Image.open(file)

            if remove_bg:
                output = remove(img)
                img = Image.open(io.BytesIO(output)).convert("RGBA")
            else:
                img = img.convert("RGB")

            img = img.resize((width, height))

            # STRONG ENHANCEMENT
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

            filename = f"{prefix}_{i+1}.{output_format.lower()}"
            zipf.writestr(filename, buffer.getvalue())

            progress.progress((i+1)/len(files))

    st.session_state.history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user": st.session_state.user,
        "files": len(files)
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
# HISTORY
# =========================
st.divider()
st.subheader("History")

for h in reversed(st.session_state.history):
    st.write(h)
