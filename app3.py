import streamlit as st
from PIL import Image, ImageEnhance
import io, zipfile
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Photo SaaS Pro", layout="wide")

# =========================
# SESSION INIT (LOGIN STABLE)
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "history" not in st.session_state:
    st.session_state.history = []

# =========================
# SIMPLE DATABASE (DEMO)
# =========================
if "USERS" not in st.session_state:
    st.session_state.USERS = {
        "admin@gmail.com": "admin"
    }

# =========================
# AUTH
# =========================
def register():
    st.subheader("Register")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Create Account"):
        if email in st.session_state.USERS:
            st.error("User already exists")
        else:
            st.session_state.USERS[email] = password
            st.success("Registered successfully")


def login():
    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email in st.session_state.USERS and st.session_state.USERS[email] == password:
            st.session_state.user = email
            st.success("Login success")
        else:
            st.error("Invalid credentials")


def logout():
    st.session_state.user = None
    st.success("Logged out")


# =========================
# IMAGE FUNCTIONS
# =========================
def enhance(img, sharpness):
    return ImageEnhance.Sharpness(img).enhance(sharpness)


def resize_custom(img, w, h):
    return img.resize((w, h))


def compress(img, target_kb):
    quality = 95
    while quality > 10:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        size = len(buf.getvalue()) / 1024

        if size <= target_kb:
            return buf

        quality -= 5

    return buf


# =========================
# MAIN APP
# =========================
def app():
    st.title("📸 Photo SaaS PRO (Full System)")

    # =========================
    # SIDEBAR SETTINGS
    # =========================
    st.sidebar.header("Settings")

    upload_mode = st.sidebar.radio("Input", ["Upload Image", "Camera"])

    preset = st.sidebar.selectbox(
        "Size Preset",
        ["Custom", "Passport", "Admission", "Job"]
    )

    # preset sizes
    preset_sizes = {
        "Passport": (413, 531),
        "Admission": (600, 800),
        "Job": (800, 800)
    }

    if preset == "Custom":
        width = st.sidebar.number_input("Width", 50, 3000, 500)
        height = st.sidebar.number_input("Height", 50, 3000, 500)
    else:
        width, height = preset_sizes[preset]

    dpi = st.sidebar.selectbox("DPI", [72, 150, 300, 600])

    target_kb = st.sidebar.number_input("Target Size KB", 10, 5000, 200)

    sharpness = st.sidebar.slider("Enhance Sharpness", 0.5, 3.0, 1.0)

    remove_bg = st.sidebar.checkbox("Remove Background (optional)")

    bg_color = st.sidebar.color_picker("Background Color (if replace)", "#ffffff")

    # =========================
    # INPUT
    # =========================
    if upload_mode == "Upload Image":
        file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
    else:
        file = st.camera_input("Take Photo")

    if file:
        img = Image.open(file).convert("RGB")

        st.subheader("Preview Original")
        st.image(img, use_container_width=True)

        # =========================
        # PROCESS BUTTON
        # =========================
        if st.button("Process Image"):
            # resize
            img = resize_custom(img, width, height)

            # enhance
            img = enhance(img, sharpness)

            # DPI set
            img.info["dpi"] = (dpi, dpi)

            # background option (simple replace simulation)
            if remove_bg:
                img = Image.new("RGB", img.size, bg_color)

            # compress
            final_img = compress(img, target_kb)

            st.subheader("Preview Final")
            st.image(img, use_container_width=True)

            # =========================
            # DOWNLOAD ZIP
            # =========================
            zip_buffer = io.BytesIO()
            zipf = zipfile.ZipFile(zip_buffer, "w")

            zipf.writestr("image.jpg", final_img.getvalue())
            zipf.close()
            zip_buffer.seek(0)

            st.download_button(
                "⬇ Download ZIP",
                zip_buffer,
                file_name="processed_image.zip",
                mime="application/zip"
            )

            # =========================
            # HISTORY SAVE
            # =========================
            st.session_state.history.append({
                "user": st.session_state.user,
                "time": str(datetime.now()),
                "size": f"{width}x{height}",
                "kb": target_kb
            })


# =========================
# HISTORY PAGE
# =========================
def show_history():
    st.subheader("📜 User History")

    for h in st.session_state.history:
        if h["user"] == st.session_state.user:
            st.write(h)


# =========================
# NAVIGATION
# =========================
st.sidebar.title("Menu")

menu = st.sidebar.radio("Go To", ["Login", "Register", "App", "History"])

if menu == "Login":
    login()
elif menu == "Register":
    register()
elif menu == "App":
    if st.session_state.user:
        app()
    else:
        st.warning("Please login first")
elif menu == "History":
    if st.session_state.user:
        show_history()
    else:
        st.warning("Login required")
