import streamlit as st
import zipfile
import io

from utils import process_image

st.set_page_config(
    page_title="Bulk Photo Processor",
    layout="wide"
)

st.title("📸 Bulk Photo Processor")

st.write(
    "Resize, Change Background, Convert Format and Download ZIP"
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

if compression == "High Quality":
    quality = 95
elif compression == "Medium":
    quality = 75
else:
    quality = 50

if uploaded_files:

    st.subheader("Preview")

    preview_cols = st.columns(4)

    for i, file in enumerate(uploaded_files):
        with preview_cols[i % 4]:
            st.image(
                file,
                use_container_width=True
            )
            st.caption(file.name)

    if st.button("🚀 Process Images"):

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            zip_buffer,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zipf:

            for file in uploaded_files:

                processed = process_image(
                    file,
                    width,
                    height,
                    bg_color,
                    output_format,
                    quality
                )

                filename = (
                    file.name.rsplit(".", 1)[0]
                    + "."
                    + output_format.lower()
                )

                zipf.writestr(
                    filename,
                    processed.getvalue()
                )

        st.success(
            "All Images Processed Successfully!"
        )

        st.download_button(
            label="📥 Download ZIP",
            data=zip_buffer.getvalue(),
            file_name="processed_images.zip",
            mime="application/zip"
        )
