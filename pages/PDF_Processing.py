import streamlit as st
from backend import PDFProcessor, DatabaseManager
import tempfile
import json
from pathlib import Path

# Initialize backend components
pdf_processor = PDFProcessor()
db_manager = DatabaseManager()

# Streamlit app configuration
st.set_page_config(page_title="Arabic PDF Processor", layout="wide")

# Custom CSS for uploader
st.markdown("""
<style>
    .upload-box {
        border: 2px dashed #cccccc;
        border-radius: 5px;
        padding: 25px;
        text-align: center;
        margin: 20px 0;
        background-color: #f9f9f9;
    }
    .upload-box.highlight {
        border-color: #6666ff;
        background-color: #f0f0ff;
    }
    #file-info {
        margin-top: 10px;
        font-weight: bold;
        color: #333333;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("Arabic PDF Processing System")
    st.header("Upload PDF")

    # Initialize session state
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
        st.session_state.file_ready = False

    # Custom HTML File Uploader with direct communication
    st.markdown("""
    <div class="upload-box" id="upload-box">
        <h4>📁 Drag & Drop PDF Here</h4>
        <p>or click to browse files</p>
        <input type="file" id="file-upload" accept=".pdf" style="display:none;">
        <div id="file-info">No file selected</div>
    </div>

    <script>
    const uploadBox = document.getElementById('upload-box');
    const fileInput = document.getElementById('file-upload');
    const fileInfo = document.getElementById('file-info');

    // Click handler
    uploadBox.addEventListener('click', () => fileInput.click());

    // Drag and drop handlers
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('highlight');
    });

    ['dragleave', 'dragend'].forEach(type => {
        uploadBox.addEventListener(type, () => {
            uploadBox.classList.remove('highlight');
        });
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('highlight');
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect(fileInput.files[0]);
        }
    });

    // File selection handler
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    function handleFileSelect(file) {
        fileInfo.innerHTML = `Selected: <strong>${file.name}</strong> (${(file.size/1024/1024).toFixed(2)} MB)`;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            const bytes = Array.from(new Uint8Array(e.target.result));
            
            // Create a custom event with the file data
            const event = new CustomEvent('fileUploaded', {
                detail: {
                    name: file.name,
                    bytes: bytes,
                    size: file.size,
                    type: file.type
                }
            });
            document.dispatchEvent(event);
        };
        reader.readAsArrayBuffer(file);
    }
    </script>
    """, unsafe_allow_html=True)

    # Create a custom component to receive file data
    file_data = st.components.v1.html(
        """
        <script>
        document.addEventListener('fileUploaded', function(e) {
            const data = e.detail;
            // Send to Streamlit through the component
            window.parent.postMessage({
                isStreamlitMessage: true,
                type: 'fileData',
                data: data
            }, '*');
        });
        </script>
        """,
        height=0,
        width=0
    )

    # Check for file data in session state
    if file_data and 'data' in file_data:
        try:
            file_info = file_data['data']
            st.session_state.uploaded_file = {
                "name": file_info['name'],
                "bytes": bytes(file_info['bytes'])
            }
            st.session_state.file_ready = True
            st.success(f"File ready for processing: {file_info['name']}")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

    # Process the file (your original logic - unchanged)
    if st.session_state.file_ready and st.session_state.uploaded_file:
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
                try:
                    book_id, report = pdf_processor.process_pdf_pages(
                        tmp_path,
                        pdf_name=cleaned_pdf_name,
                        start_page=start_page,
                        end_page=end_page
                    )
                    
                    if book_id:
                        st.session_state.current_book_id = book_id
                        st.session_state.file_ready = False
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
                except Exception as e:
                    st.error(f"Processing error: {str(e)}")

if __name__ == "__main__":
    main()