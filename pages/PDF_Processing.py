import streamlit as st
from backend import PDFProcessor, DatabaseManager, TextToSpeech
from datetime import datetime
import tempfile
import base64
from docx.enum.text import WD_ALIGN_PARAGRAPH
import uuid

# Initialize backend components
pdf_processor = PDFProcessor()
db_manager = DatabaseManager()

# Streamlit app configuration
st.set_page_config(page_title="Arabic PDF Processor", layout="wide")

# Custom CSS for RTL support
st.markdown("""
<style>
    .rtl-text {
        text-align: right;
        direction: rtl;
    }
    .audio-player {
        width: 100%;
        margin: 20px 0;
    }
    #file_upload {
        padding: 10px;
        border: 2px dashed #ccc;
        border-radius: 5px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("Arabic PDF Processing System")

    st.header("Upload PDF")
    
    # Custom HTML File Uploader
    st.markdown("""
    <h3>Choose a PDF file</h3>
    <input type="file" id="file_upload" accept=".pdf">
    <script>
    document.getElementById("file_upload").addEventListener("change", function(e) {
        const file = e.target.files[0];
        const reader = new FileReader();
        reader.onload = function(e) {
            const bytes = Array.from(new Uint8Array(e.target.result));
            window.parent.postMessage({
                file_data: {
                    name: file.name,
                    data: bytes,
                    size: file.size,
                    type: file.type
                }
            }, "*");
        };
        reader.readAsArrayBuffer(file);
    });
    </script>
    """, unsafe_allow_html=True)

    # Handle the uploaded file from JavaScript
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None

    # Check for messages from JavaScript
    try:
        file_data = st.experimental_get_query_params().get("file_data")
        if file_data:
            file_name = file_data[0]["name"]
            file_bytes = bytes(file_data[0]["data"])
            st.session_state.uploaded_file = {
                "name": file_name,
                "bytes": file_bytes
            }
    except:
        pass

    # Also keep the original uploader as fallback
    fallback_upload = st.file_uploader("Or use standard uploader", type="pdf")
    if fallback_upload:
        st.session_state.uploaded_file = {
            "name": fallback_upload.name,
            "bytes": fallback_upload.getvalue()
        }

    if st.session_state.uploaded_file:
        original_pdf_name = st.session_state.uploaded_file["name"]
        cleaned_pdf_name = pdf_processor.clean_pdf_name(original_pdf_name)
        
        st.info(f"Original PDF name: {original_pdf_name}")
        st.info(f"Cleaned PDF name: {cleaned_pdf_name}")
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(st.session_state.uploaded_file["bytes"])
            tmp_path = tmp_file.name

        # Add page range selection
        col1, col2 = st.columns(2)
        with col1:
            start_page = st.number_input("Start Page", min_value=1, value=1)
        with col2:
            end_page = st.number_input("End Page", min_value=1, value=10)
            
        if st.button("Process PDF"):
            with st.spinner(f"Processing pages {start_page} to {end_page}..."):
                # Process with page range and get processing report
                book_id, report = pdf_processor.process_pdf_pages(
                    tmp_path,
                    pdf_name=cleaned_pdf_name,
                    start_page=start_page,
                    end_page=end_page
                )
                
                if book_id:
                    st.session_state.current_book_id = book_id
                    st.success(f"Processed {len(report['newly_processed'])} pages successfully!")
                    
                    with st.expander("Processing Details"):
                        st.write(f"**Total pages in PDF:** {report['total_pages']}")
                        st.write(f"**Newly processed pages:** {report['newly_processed']}")
                        st.write(f"**Previously processed pages:** {report['skipped_pages']}")
                        progress = len(report['processed_pages']) / report['total_pages']
                        st.progress(progress)
                        st.caption(f"{int(progress*100)}% complete")
                else:
                    st.error("Failed to process PDF")

if __name__ == "__main__":
    main()