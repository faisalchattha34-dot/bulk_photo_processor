import streamlit as st
from PIL import Image
from rembg import remove
import zipfile
import io

st.set_page_config(
    page_title="Bulk Photo Processor",
    layout="wide"
)

st.title("📸 Bulk Photo Processor")

st.write(
    "Resize Images, Change Background Color, Convert Format and Download ZIP"
)

uploaded_files = st.file_uploader(
    "Upload Images",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

col1, col2 = st.columns(2)

with col1:
    width = st.number_input(
        "Width",
        min_value=50,
        value=300
    )

with col2:
    height = st.number_input(
        "Height",
        min_value=50,
        value=300
    )

bg_color = st.selectbox(
    "Background Color",
    [
        "white",
        "blue",
        "red",
        "green",
        "yellow",
        "black"
    ]
)

output_format = st.selectbox(
    "Output Format",
    [
        "JPG",
        "PNG",
        "WEBP"
    ]
)

compression = st.selectbox(
    "Compression Level",
    [
        "High Quality",
        "Medium",
        "Low Size"
    ]
)

remove_background = st.checkbox(
    "Replace Existing Background (AI)",
    value=True
)

if compression == "High Quality":
    quality = 95
elif compression == "Medium":
    quality = 75
else:
    quality = 50

if uploaded_files:

    st.subheader("Preview")

    cols = st.columns(4)

    for i, file in enumerate(uploaded_files):
        with cols[i % 4]:
            st.image(file, use_container_width=True)
            st.caption(file.name)

    if st.button("🚀 Process Images"):

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            zip_buffer,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zipf:

            progress = st.progress(0)

            for index, file in enumerate(uploaded_files):

                try:

                    image = Image.open(file)

                    if remove_background:

                        image = remove(image)
                        image = image.convert("RGBA")

                        new_bg = Image.new(
                            "RGBA",
                            image.size,
                            bg_color
                        )

                        image = Image.alpha_composite(
                            new_bg,
                            image
                        )

                    else:

                        image = image.convert("RGB")

                    image = image.resize(
                        (
                            int(width),
                            int(height)
                        )
                    )

                    if output_format == "JPG":
                        image = image.convert("RGB")

                    img_bytes = io.BytesIO()

                    save_format = (
                        "JPEG"
                        if output_format == "JPG"
                        else output_format
                    )

                    image.save(
                        img_bytes,
                        format=save_format,
                        quality=quality
                    )

                    img_bytes.seek(0)

                    filename = (
                        file.name.rsplit(".", 1)[0]
                        + "."
                        + output_format.lower()
                    )

                    zipf.writestr(
                        filename,
                        img_bytes.getvalue()
                    )

                    progress.progress(
                        (index + 1)
                        / len(uploaded_files)
                    )

                except Exception as e:

                    st.error(
                        f"Error processing {file.name}: {e}"
                    )

        st.success(
            "✅ All Images Processed Successfully!"
        )

        st.download_button(
            label="📥 Download ZIP",
            data=zip_buffer.getvalue(),
            file_name="processed_images.zip",
            mime="application/zip"
        )
