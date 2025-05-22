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
    #file-upload-container {
        padding: 20px;
        border: 2px dashed #ccc;
        border-radius: 5px;
        margin-bottom: 20px;
        text-align: center;
    }
    #file-upload-container:hover {
        border-color: #aaa;
    }
    #file-input {
        display: none;
    }
    #file-label {
        cursor: pointer;
        display: block;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("Arabic PDF Processing System")
    st.header("Upload PDF")

    # Custom HTML File Uploader
    st.markdown("""
    <div id="file-upload-container">
        <input type="file" id="file-input" accept=".pdf">
        <label for="file-input" id="file-label">
            <h3>Click to upload PDF</h3>
            <p>or drag and drop file here</p>
            <div id="file-info"></div>
        </label>
    </div>

    <script>
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileInfo.innerHTML = `<p>Selected: <strong>${file.name}</strong> (${(file.size/1024/1024).toFixed(2)} MB)</p>`;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const bytes = Array.from(new Uint8Array(e.target.result));
                window.parent.postMessage({
                    type: 'fileUpload',
                    data: {
                        name: file.name,
                        size: file.size,
                        type: file.type,
                        bytes: bytes,
                        lastModified: file.lastModified
                    }
                }, '*');
            };
            reader.readAsArrayBuffer(file);
        }
    });

    // Handle drag and drop
    const container = document.getElementById('file-upload-container');
    container.addEventListener('dragover', (e) => {
        e.preventDefault();
        container.style.borderColor = '#666';
    });
    container.addEventListener('dragleave', () => {
        container.style.borderColor = '#ccc';
    });
    container.addEventListener('drop', (e) => {
        e.preventDefault();
        container.style.borderColor = '#ccc';
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });
    </script>
    """, unsafe_allow_html=True)

    # Handle the uploaded file
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None

    # Custom component to receive file data
    file_data = st.empty()
    
    # JavaScript to Python communication
    st.markdown("""
    <script>
    // Listen for messages from the iframe (Streamlit)
    window.addEventListener('message', (event) => {
        if (event.data.type === 'fileUpload') {
            const fileData = event.data.data;
            // Send to Streamlit
            window.parent.postMessage({
                isStreamlitMessage: true,
                type: 'fileData',
                data: fileData
            }, '*');
        }
    });
    </script>
    """, unsafe_allow_html=True)

    # Check for file data
    try:
        file_data = st.session_state.get('file_data')
        if file_data:
            file_name = file_data['name']
            file_bytes = bytes(file_data['bytes'])
            st.session_state.uploaded_file = {
                "name": file_name,
                "bytes": file_bytes
            }
            st.success(f"File ready for processing: {file_name}")
    except:
        pass

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