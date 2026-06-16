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
st.set_page_config(page_title="Bulk Photo SaaS PRO FIX", layout="wide")

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
# DATABASE (UNCHANGED)
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
# SESSION INIT (UNCHANGED)
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
# COOKIE RESTORE FIX ONLY
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
# AUTH (UNCHANGED LOGIC)
# =========================
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def register():
    st.title("📝 Register")

    u = st.text_input("Username")
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")

    if st.button("Create Account"):
        if not u or not e or not p:
            st.error("All fields required")
        elif u in USERS:
            st.error("User already exists")
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

def logout():
    cookies["user"] = ""
    cookies.save()
    st.session_state.user = None
    st.rerun()

# =========================
# ROUTING (UNCHANGED)
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
st.title("🚀 BULK PHOTO SaaS PRO (STABLE FIX)")
st.success(f"Welcome {user}")

st.info(f"Credits: {USERS[user]['credits']}")

if st.button("Logout"):
    logout()

# =========================
# CREDIT SYSTEM (UNCHANGED)
# =========================
def use_credit(n):
    if USERS[user]["credits"] >= n:
        USERS[user]["credits"] -= n
        save_users()
        return True
    return False

# =========================
# UPLOAD + CAMERA (UNCHANGED)
# =========================
st.subheader("Upload / Camera")

col1, col2 = st.columns(2)

with col1:
    files = st.file_uploader(
        "Upload Images",
        type=["png","jpg","jpeg","webp"],
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
enhance = st.checkbox("Enhance Image", True)

prefix = st.text_input("File Prefix", "photo")

# =========================
# PROCESS (UNCHANGED LOGIC)
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
            if remove_bg:
                out = remove(img)
                img = Image.open(io.BytesIO(out)).convert("RGBA")

                bg_map = {
                    "white": (255, 255, 255),
                    "blue": (0, 102, 255),
                    "red": (255, 0, 0),
                    "black": (0, 0, 0)
                }

                background = Image.new(
                    "RGBA",
                    img.size,
                    bg_map.get(bg_color, (255, 255, 255))
                )

                img = Image.alpha_composite(background, img)
                img = img.convert("RGB")

            else:
                img = img.convert("RGB")

            img = img.resize((int(width), int(height)))
           


            if enhance:
                img = ImageEnhance.Sharpness(img).enhance(2.5)
                img = ImageEnhance.Contrast(img).enhance(1.3)
                img = ImageEnhance.Brightness(img).enhance(1.05)
                img = img.filter(ImageFilter.UnsharpMask(2,150,3))

            if not preview:
                st.image(img, width=200)
                preview = True

            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)

            zipf.writestr(f"{prefix}_{i+1}.jpg", buf.getvalue())

            progress.progress((i+1)/len(images))

    st.session_state.history.append({
        "user": user,
        "files": len(images),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    st.success("Processing Done")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="output.zip"
    )

# =========================
# HISTORY (UNCHANGED)
# =========================
st.divider()
st.subheader("History")

for h in reversed(st.session_state.history):
    st.write(h) 
