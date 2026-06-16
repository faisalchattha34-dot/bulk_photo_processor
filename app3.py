import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
import zipfile
import io
from datetime import datetime
import random
from streamlit_cookies_manager import EncryptedCookieManager

# =========================
# COOKIE SETUP
# =========================
cookies = EncryptedCookieManager(
    prefix="photo_saas",
    password="my_secret_password"
)

if not cookies.ready():
    st.stop()

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Bulk Photo SaaS V5.5", layout="wide")

# =========================
# SESSION STATE
# =========================
if "USERS" not in st.session_state:
    st.session_state.USERS = {
        "admin": {"password": "admin123", "email": "admin@demo.com", "credits": 999},
        "user": {"password": "user123", "email": "user@demo.com", "credits": 20}
    }

if "user" not in st.session_state:
    st.session_state.user = None

if "credits" not in st.session_state:
    st.session_state.credits = 0

if "history" not in st.session_state:
    st.session_state.history = []

if "page" not in st.session_state:
    st.session_state.page = "login"

if "otp" not in st.session_state:
    st.session_state.otp = None

if "reset_user" not in st.session_state:
    st.session_state.reset_user = None

USERS = st.session_state.USERS

# =========================
# AUTO LOGIN (COOKIE)
# =========================
if not st.session_state.user:
    saved_user = cookies.get("user")
    if saved_user and saved_user in USERS:
        st.session_state.user = saved_user
        st.session_state.credits = USERS[saved_user]["credits"]

# =========================
# REGISTER
# =========================
def register():
    st.title("📝 Register")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):

        if username == "" or email == "":
            st.error("All fields required")

        elif username in USERS:
            st.error("User already exists")

        else:
            USERS[username] = {
                "password": password,
                "email": email,
                "credits": 10
            }
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

            if username in USERS and USERS[username]["password"] == password:

                st.session_state.user = username
                st.session_state.credits = USERS[username]["credits"]

                cookies["user"] = username
                cookies.save()

                st.success("Login Success")
                st.rerun()

            else:
                st.error("Invalid credentials")

    with col2:
        if st.button("Register"):
            st.session_state.page = "register"
            st.rerun()

    if st.button("Forgot Password"):
        st.session_state.page = "forgot"
        st.rerun()

# =========================
# FORGOT PASSWORD
# =========================
def forgot_password():
    st.title("Forgot Password")

    username = st.text_input("Username")

    if st.button("Send Code"):

        if username in USERS:

            otp = str(random.randint(100000, 999999))
            st.session_state.otp = otp
            st.session_state.reset_user = username

            st.success(f"Your Code: {otp}")  # demo only

        else:
            st.error("User not found")

    code = st.text_input("Enter Code")
    new_pass = st.text_input("New Password", type="password")

    if st.button("Reset Password"):

        if code == st.session_state.otp:

            USERS[st.session_state.reset_user]["password"] = new_pass

            st.success("Password Updated")
            st.session_state.page = "login"

        else:
            st.error("Invalid Code")

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
# ROUTING
# =========================
if not st.session_state.user:

    if st.session_state.page == "register":
        register()

    elif st.session_state.page == "forgot":
        forgot_password()

    else:
        login()

    st.stop()

# =========================
# DASHBOARD
# =========================
st.title("📸 Bulk Photo SaaS V5.5 (FIXED)")
st.success(f"Welcome {st.session_state.user} | Credits: {st.session_state.credits}")

if st.button("Logout"):
    logout()

# =========================
# CAMERA + UPLOAD
# =========================
st.subheader("Camera / Upload")

camera = st.camera_input("Take Photo")
uploads = st.file_uploader(
    "Upload Images",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

files = []

if camera:
    files.append(camera)

if uploads:
    files.extend(uploads)

# =========================
# FILTERS
# =========================
filter_type = st.selectbox("Filter", ["None", "Sharp", "Bright", "B&W"])

# =========================
# SETTINGS
# =========================
bg_color = st.selectbox("Background", ["white", "blue", "red", "green", "black"])
width = st.number_input("Width", 50, value=300)
height = st.number_input("Height", 50, value=300)

# =========================
# PROCESS
# =========================
if files and st.button("PROCESS"):

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w") as zipf:

        for i, file in enumerate(files):

            img = Image.open(file)

            img = remove(img)
            img = img.convert("RGBA")

            bg = Image.new("RGBA", img.size, bg_color)
            img = Image.alpha_composite(bg, img)

            img = img.resize((width, height))

            if filter_type == "Sharp":
                img = ImageEnhance.Sharpness(img).enhance(3)

            elif filter_type == "Bright":
                img = ImageEnhance.Brightness(img).enhance(1.5)

            elif filter_type == "B&W":
                img = img.convert("L")

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            zipf.writestr(f"img_{i+1}.png", buffer.getvalue())

            progress.progress((i+1)/len(files))

    st.success("Done")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="output.zip"
    )
