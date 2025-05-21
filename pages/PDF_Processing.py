import streamlit as st
from backend import PDFProcessor, DatabaseManager, TextToSpeech
from datetime import datetime
import tempfile
import base64
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Initialize backend components
pdf_processor = PDFProcessor()
db_manager = DatabaseManager()
tts = TextToSpeech()

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
</style>
""", unsafe_allow_html=True)

def main():
    st.title("Arabic PDF Processing System")

    st.header("Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file is not None:
        # Extract original PDF name before creating temp file
        original_pdf_name = uploaded_file.name

        cleaned_pdf_name = pdf_processor.clean_pdf_name(original_pdf_name)
        # Display the extracted name
        st.info(f"Original PDF name: {original_pdf_name}")
        st.info(f"Cleaned PDF name: {cleaned_pdf_name}")
        # Create temp file with original extension preserved
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
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
                    # Show processing report
                    with st.expander("Processing Details"):
                        st.write(f"**Total pages in PDF:** {report['total_pages']}")
                        st.write(f"**Newly processed pages:** {report['newly_processed']}")
                        st.write(f"**Previously processed pages:** {report['skipped_pages']}")
                        # Visual progress
                        progress = len(report['processed_pages']) / report['total_pages']
                        st.progress(progress)
                        st.caption(f"{int(progress*100)}% complete")
                else:
                    st.error("Failed to process PDF")


if __name__ == "__main__":
    main()