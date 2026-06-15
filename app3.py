import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
import zipfile
import io
from datetime import datetime

st.set_page_config(page_title="Bulk Photo SaaS V5.3", layout="wide")

# =========================
# DATABASE (SESSION DEMO)
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


USERS = st.session_state.USERS


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
                st.success("Login Success")
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
    st.session_state.user = None
    st.session_state.credits = 0
    st.session_state.page = "login"
    st.rerun()


# =========================
# SMART COMPRESSION
# =========================
def smart_compress(img, min_kb, max_kb, fmt):
    quality = 95
    save_format = "JPEG" if fmt in ["JPG", "JPEG"] else fmt

    while quality >= 10:
        buffer = io.BytesIO()

        save_kwargs = {"format": save_format}
        if save_format in ["JPEG", "WEBP"]:
            save_kwargs["quality"] = quality

        img.save(buffer, **save_kwargs)
        size_kb = len(buffer.getvalue()) / 1024

        if min_kb <= size_kb <= max_kb:
            buffer.seek(0)
            return buffer

        quality -= 5

    buffer.seek(0)
    return buffer


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
st.title("📸 Bulk Photo SaaS V5.3")
st.success(f"Welcome {st.session_state.user} | Credits: {st.session_state.credits}")

if st.button("Logout"):
    logout()


# =========================
# CREDIT SYSTEM
# =========================
def use_credit(n):
    if st.session_state.credits >= n:
        st.session_state.credits -= n
        USERS[st.session_state.user]["credits"] -= n
        return True
    return False


# =========================
# UPLOAD
# =========================
files = st.file_uploader(
    "Upload Images",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
) or []


# =========================
# FORMAT
# =========================
output_format = st.selectbox("Format", ["JPG", "JPEG", "PNG", "WEBP"])


# =========================
# RESOLUTION (MIN 600x800)
# =========================
st.subheader("Resolution")

res_mode = st.radio("Mode", ["Preset", "Custom"], horizontal=True)

if res_mode == "Preset":
    preset = st.selectbox("Preset", ["600x800", "800x1200", "1024x1366"])
    preset_map = {
        "600x800": (600, 800),
        "800x1200": (800, 1200),
        "1024x1366": (1024, 1366)
    }
    width, height = preset_map[preset]
else:
    col1, col2 = st.columns(2)
    with col1:
        width = st.number_input("Width", min_value=600, value=600)
    with col2:
        height = st.number_input("Height", min_value=800, value=800)


# =========================
# SETTINGS
# =========================
bg_color = st.selectbox("BG Color", ["white", "blue", "red", "green", "black"])
remove_bg = st.checkbox("Remove Background", True)
enhance = st.checkbox("Enhance Image", True)
prefix = st.text_input("File Prefix", "photo")


# =========================
# DPI
# =========================
dpi_mode = st.radio("DPI Mode", ["Preset", "Custom"], horizontal=True)

if dpi_mode == "Preset":
    dpi = st.selectbox("DPI", [72, 150, 300, 600])
else:
    dpi = st.number_input("DPI", min_value=10, max_value=5000, value=300)


# =========================
# SIZE RANGE (10–25 KB DEFAULT)
# =========================
st.subheader("File Size Control")

size_mode = st.radio("Compression", ["ON (10-25KB)", "OFF"], horizontal=True)

min_kb, max_kb = None, None

if size_mode == "ON (10-25KB)":
    min_kb = 10
    max_kb = 25


# =========================
# PROCESS
# =========================
if files and st.button("🚀 PROCESS"):

    if not use_credit(len(files)):
        st.error("Not enough credits")
        st.stop()

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:

        preview_done = False

        for i, file in enumerate(files):

            img = Image.open(file)

            if remove_bg:
                img = remove(img)
                img = img.convert("RGBA")
                bg = Image.new("RGBA", img.size, bg_color)
                img = Image.alpha_composite(bg, img)
            else:
                img = img.convert("RGB")

            img = img.resize((width, height))

            if enhance:
                img = img.filter(ImageFilter.SHARPEN)
                img = ImageEnhance.Sharpness(img).enhance(2)
                img = ImageEnhance.Contrast(img).enhance(1.2)

            if output_format in ["JPG", "JPEG"]:
                img = img.convert("RGB")

            if not preview_done:
                st.subheader("Preview")
                st.image(img, width=250)
                preview_done = True

            buffer = io.BytesIO()

            img.save(buffer, format="JPEG" if output_format in ["JPG","JPEG"] else output_format, dpi=(dpi, dpi))
            buffer.seek(0)

            if min_kb and max_kb:
                buffer = smart_compress(img, min_kb, max_kb, output_format)

            filename = f"{prefix}_{i+1}.{output_format.lower()}"
            zipf.writestr(filename, buffer.getvalue())

            progress.progress((i+1)/len(files))

    st.session_state.history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": st.session_state.user,
        "files": len(files),
        "credits": st.session_state.credits
    })

    st.success("Done")

    st.download_button(
        "Download ZIP",
        zip_buffer.getvalue(),
        file_name="output_v5_3.zip"
    )


# =========================
# HISTORY
# =========================
st.divider()
st.subheader("History")

for h in reversed(st.session_state.history):
    st.write(f"{h['time']} | {h['user']} | files: {h['files']} | credits: {h['credits']}")
