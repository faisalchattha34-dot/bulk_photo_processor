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
st.set_page_config(page_title="Bulk Photo SaaS PRO", layout="wide")

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
# LOGIN RESTORE
# =========================
def restore_login():
    saved = cookies.get("user")
    if saved and str(saved).strip() in USERS:
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

    if st.button("Create Account"):
        st.session_state.page = "register"
        st.rerun()

def register():
    st.title("📝 Register")

    u = st.text_input("Username")
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")

    if st.button("Create Account"):
        if not u or not e or not p:
            st.error("All fields required")
        elif u in USERS:
            st.error("User exists")
        else:
            USERS[u] = {
                "password": hash_pass(p),
                "email": e,
                "credits": 10,
                "plan": "free"
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

st.title("🚀 BULK PHOTO SaaS PRO")
st.success(f"Welcome {user}")

st.info(f"Credits: {USERS[user]['credits']}")

if st.button("Logout"):
    cookies["user"] = ""
    cookies.save()
    st.session_state.user = None
    st.rerun()

# =========================
# UPLOAD
# =========================
st.subheader("Upload Images")

files = st.file_uploader(
    "Upload",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

# =========================
# SETTINGS
# =========================
st.subheader("Settings")

bg_color = st.selectbox("Background", ["white", "blue", "red", "black"])
remove_bg = st.checkbox("Remove Background", True)

width = st.number_input("Width", 300)
height = st.number_input("Height", 300)

prefix = st.text_input("File Name", "photo")

# =========================
# BACKGROUND MAP
# =========================
bg_map = {
    "white": (255, 255, 255),
    "blue": (0, 102, 255),
    "red": (255, 0, 0),
    "black": (0, 0, 0)
}

# =========================
# PROCESS
# =========================
if files and st.button("PROCESS"):

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w") as zipf:

        preview = False

        for i, file in enumerate(files):

            img = Image.open(file)

            # =========================
            # SAFE BACKGROUND FIX
            # =========================
            if remove_bg:
                try:
                    output = remove(img)
                    img = Image.open(io.BytesIO(output)).convert("RGBA")
                except:
                    img = img.convert("RGBA")

                bg = Image.new("RGBA", img.size, bg_map.get(bg_color))
                img = Image.alpha_composite(bg, img).convert("RGB")
            else:
                img = img.convert("RGB")

            img = img.resize((int(width), int(height)))

            if not preview:
                st.image(img, width=200)
                preview = True

            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)

            zipf.writestr(f"{prefix}_{i+1}.jpg", buf.getvalue())

            progress.progress((i+1)/len(files))

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

for h in st.session_state.history:
    st.write(h)
