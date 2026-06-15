import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove
import zipfile
import io
from datetime import datetime

st.set_page_config(page_title="Bulk Photo SaaS V5.1", layout="wide")

# =========================
# FAKE DATABASE (UPGRADED)
# =========================
if "USERS" not in st.session_state:
    st.session_state.USERS = {
        "admin": {"password": "admin123", "credits": 999},
        "user": {"password": "user123", "credits": 20}
    }

USERS = st.session_state.USERS

# =========================
# SESSION STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "credits" not in st.session_state:
    st.session_state.credits = 0

if "history" not in st.session_state:
    st.session_state.history = []

if "page" not in st.session_state:
    st.session_state.page = "login"


# =========================
# REGISTER SYSTEM
# =========================
def register():
    st.title("📝 Create New Account")

    username = st.text_input("Choose Username")
    password = st.text_input("Choose Password", type="password")

    if st.button("Register"):
        if username in USERS:
            st.error("❌ Username already exists")
        elif username == "":
            st.error("❌ Username cannot be empty")
        else:
            USERS[username] = {
                "password": password,
                "credits": 10  # 🎁 free signup credits
            }
            st.success("✅ Account created! You can login now.")
            st.session_state.page = "login"
            st.rerun()


# =========================
# LOGIN SYSTEM
# =========================
def login():
    st.title("🔐 SaaS Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.user = username
                st.session_state.credits = USERS[username]["credits"]
                st.success("Login Successful")
                st.rerun()
            else:
                st.error("Invalid Credentials")

    with col2:
        if st.button("Create Account"):
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
# COMPRESSION ENGINE
# =========================
def compress_to_target(img, target_kb, fmt):
    quality = 95
    save_format = "JPEG" if fmt == "JPG" else fmt

    while quality >= 10:
        buffer = io.BytesIO()

        save_kwargs = {"format": save_format}
        if save_format in ["JPEG", "WEBP"]:
            save_kwargs["quality"] = quality

        img.save(buffer, **save_kwargs)

        if len(buffer.getvalue()) / 1024 <= target_kb:
            buffer.seek(0)
            return buffer

        quality -= 5

    buffer.seek(0)
    return buffer


# =========================
# ROUTING (LOGIN / REGISTER / DASHBOARD)
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
st.title("📸 Bulk Photo SaaS V5.1")
st.success(f"Welcome {st.session_state.user} | Credits: {st.session_state.credits}")

if st.button("Logout"):
    logout()


# =========================
# CREDIT SYSTEM
# =========================
def use_credit(count):
    if st.session_state.credits >= count:
        st.session_state.credits -= count
        USERS[st.session_state.user]["credits"] -= count
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
# SETTINGS
# =========================
preset = st.selectbox("Preset", ["Custom", "Passport", "NADRA", "Job"])

size_map = {
    "Passport": (300, 300),
    "NADRA": (400, 400),
    "Job": (300, 400),
    "Custom": (300, 300)
}

width, height = size_map[preset]

col1, col2 = st.columns(2)
with col1:
    width = st.number_input("Width", value=width)
with col2:
    height = st.number_input("Height", value=height)

bg_color = st.selectbox("Background", ["white", "blue", "red", "green", "black"])
output_format = st.selectbox("Format", ["JPG", "PNG", "WEBP"])

remove_bg = st.selectbox("Background Removal", ["ON (AI)", "OFF"]) == "ON (AI)"
enhance = st.checkbox("Enhance Image", True)

prefix = st.text_input("File Prefix", "photo")

dpi = st.selectbox("DPI", [72, 150, 300, 600])
size_choice = st.selectbox("File Size", ["No Limit", "20 KB", "50 KB", "100 KB"])


# =========================
# PROCESS
# =========================
if files and st.button("🚀 PROCESS (V5.1 SaaS)"):

    if not use_credit(len(files)):
        st.error("❌ Not enough credits")
        st.stop()

    zip_buffer = io.BytesIO()
    progress = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:

        preview = False

        for i, file in enumerate(files):

            image = Image.open(file)

            # BG REMOVE
            if remove_bg:
                image = remove(image)
                image = image.convert("RGBA")
                bg = Image.new("RGBA", image.size, bg_color)
                image = Image.alpha_composite(bg, image)
            else:
                image = image.convert("RGB")

            image = image.resize((width, height))

            if enhance:
                image = image.filter(ImageFilter.SHARPEN)
                image = ImageEnhance.Sharpness(image).enhance(2)
                image = ImageEnhance.Contrast(image).enhance(1.2)

            if output_format == "JPG":
                image = image.convert("RGB")

            if not preview:
                st.subheader("Preview")
                st.image(image, width=250)
                preview = True

            save_format = "JPEG" if output_format == "JPG" else output_format
            buffer = io.BytesIO()

            image.save(buffer, format=save_format, dpi=(dpi, dpi))
            buffer.seek(0)

            if size_choice == "20 KB":
                buffer = compress_to_target(image, 20, output_format)
            elif size_choice == "50 KB":
                buffer = compress_to_target(image, 50, output_format)
            elif size_choice == "100 KB":
                buffer = compress_to_target(image, 100, output_format)

            filename = f"{prefix}_{i+1}.{output_format.lower()}"
            zipf.writestr(filename, buffer.getvalue())

            progress.progress((i + 1) / len(files))

    st.session_state.history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": st.session_state.user,
        "files": len(files),
        "credits_left": st.session_state.credits
    })

    st.success("✅ Done")

    st.download_button(
        "📥 Download ZIP",
        zip_buffer.getvalue(),
        file_name="bulk_v5_1.zip",
        mime="application/zip"
    )


# =========================
# HISTORY
# =========================
st.divider()
st.subheader("📊 History")

for h in reversed(st.session_state.history):
    st.write(f"🕒 {h['time']} | 👤 {h['user']} | 📁 {h['files']} | 💳 {h['credits_left']}")
