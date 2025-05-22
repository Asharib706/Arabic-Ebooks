import streamlit as st
from backend import PDFProcessor, DatabaseManager
import tempfile
import json
import uuid

# Initialize backend components
pdf_processor = PDFProcessor()
db_manager = DatabaseManager()

# Streamlit app configuration
st.set_page_config(page_title="Arabic PDF Processor", layout="wide")

# Custom CSS for uploader
st.markdown("""
<style>
    .upload-container {
        border: 2px dashed #ccc;
        border-radius: 5px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }
    .upload-container:hover {
        border-color: #aaa;
    }
    #file-name {
        margin-top: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("Arabic PDF Processing System")
    st.header("Upload PDF")

    # Initialize session state
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
        st.session_state.file_processed = False

    # Custom HTML File Uploader
    st.markdown("""
    <div class="upload-container">
        <input type="file" id="file-upload" accept=".pdf">
        <p>Drag and drop your PDF here or click to browse</p>
        <div id="file-name"></div>
    </div>

    <script>
    const fileUpload = document.getElementById('file-upload');
    const fileNameDisplay = document.getElementById('file-name');

    fileUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileNameDisplay.innerHTML = `Selected: <strong>${file.name}</strong>`;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const bytes = Array.from(new Uint8Array(e.target.result));
                
                // Send data to Streamlit
                const data = {
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    bytes: bytes,
                    lastModified: file.lastModified
                };
                
                // Create a hidden element to store the data
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.id = 'file-data';
                hiddenInput.value = JSON.stringify(data);
                document.body.appendChild(hiddenInput);
                
                // Notify Streamlit to check for the data
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: 'file_uploaded'
                }, '*');
            };
            reader.readAsArrayBuffer(file);
        }
    });
    </script>
    """, unsafe_allow_html=True)

    # Create a dummy component to trigger Python callback
    uploaded = st.checkbox("File uploaded", key="file_uploaded", disabled=True, label_visibility="hidden")

    # When the checkbox changes (triggered by JavaScript)
    if uploaded:
        # Get the file data from the hidden HTML element
        file_data = st.components.v1.html(
            """
            <script>
            const fileData = document.getElementById('file-data').value;
            window.parent.postMessage({
                type: 'streamlit:reportData',
                data: fileData
            }, '*');
            </script>
            """,
            height=0,
            width=0,
        )

        # Listen for the file data
        if file_data:
            try:
                file_json = json.loads(file_data)
                st.session_state.uploaded_file = {
                    "name": file_json["name"],
                    "bytes": bytes(file_json["bytes"])
                }
                st.success(f"File ready for processing: {file_json['name']}")
                st.session_state.file_processed = False
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

    # Process the file (your original logic)
    if st.session_state.uploaded_file and not st.session_state.file_processed:
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
                        st.session_state.file_processed = True
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