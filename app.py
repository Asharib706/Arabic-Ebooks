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

def display_audio_player(audio_bytes: bytes):
    """Display audio player for generated speech"""
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    audio_html = f"""
    <audio controls class="audio-player">
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

def main():
    st.title("Arabic PDF Processing System")

    # Tab layout
    tab1, tab2, tab3 = st.tabs(["Upload PDF", "Browse Library", "Search"])

    with tab1:
        st.header("Upload New PDF")
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

    with tab2:
        st.header("Browse Library")

#         # Get all books sorted by date (using book_id now)
#         all_books = list(db_manager.pdf_collection.find().sort("created_at", -1))

#         if not all_books:
#             st.info("No books found in the library")
#         else:
#             # Book selection dropdown (using book_id as key)
#             selected_book = st.selectbox(
#                 "Select a book",
#                 options=all_books,
#                 format_func=lambda x: f"{x['title']} (ID: {x['book_id'][:8]}...)"
#             )

#             if selected_book:
#                 st.subheader(selected_book["title"])
#                 st.write(f"**Author:** {selected_book.get('author', 'N/A')}")
#                 st.write(f"**Subject:** {selected_book.get('subject', 'N/A')}")

#                 # Show processing status
#                 status = db_manager.get_processing_status(selected_book["book_id"])
#                 progress = len(status["processed_pages"]) / status["total_pages"] if status["total_pages"] > 0 else 0

#                 st.progress(progress)
#                 st.caption(f"Processed {len(status['processed_pages'])} of {status['total_pages']} pages ({progress:.0%})")

#                 # Chapter selection
#                 if selected_book.get("chapters"):
#                     chapter_names = [chap["name"] for chap in selected_book["chapters"]]
#                     selected_chapter = st.selectbox(
#                         "Select chapter",
#                         options=chapter_names,
#                         index=0
#                     )
#                     chapter_idx = chapter_names.index(selected_chapter)
#                     # pages = db_manager.get_chapter_pages(selected_book["book_id"], chapter_idx)
#                 else:
#                     st.warning("No chapters detected - showing first available pages")
#                     pages = list(db_manager.pages_collection.find(
#                         {"book_id": selected_book["book_id"]}
#                     ).sort("page_number", 1).limit(10))

#                 if pages:
#                     # Page navigation with status indicators
#                     page_options = []
#                     for p in range(1, status["total_pages"] + 1):
#                         status_icon = "✅" if p in status["processed_pages"] else "❌"
#                         page_options.append(f"{status_icon} Page {p}")

#                     selected_page_idx = st.selectbox(
#                         "Select page",
#                         options=range(1, status["total_pages"] + 1),
#                         format_func=lambda x: f"{'✅' if x in status['processed_pages'] else '❌'} Page {x}"
#                     )

#                     # Get page content if processed
#                     if selected_page_idx in status["processed_pages"]:
#                         selected_page = db_manager.get_page(selected_book["book_id"], selected_page_idx)

#                         # Display options
#                         view_mode = st.radio(
#                             "View mode",
#                             ["Read", "Listen"],
#                             horizontal=True
#                         )

#                         if view_mode == "Read":
#                             st.markdown(f'<div class="rtl-text">{selected_page["cleaned_text"]}</div>', 
#                                        unsafe_allow_html=True)
#                         else:
#                             if st.button("Generate Audio"):
#                                 with st.spinner("Generating audio..."):
#                                     audio_bytes = tts.generate_speech(selected_page["cleaned_text"])
#                                     display_audio_player(audio_bytes)
#                     else:
#                         st.warning("This page hasn't been processed yet")

#                         if st.button(f"Process Page {selected_page_idx} now"):
#                             with st.spinner(f"Processing page {selected_page_idx}..."):
#                                 _, report = pdf_processor.process_pdf_pages(
#                                     "",  # Would need original path here
#                                     start_page=selected_page_idx,
#                                     end_page=selected_page_idx,
#                                     book_id=selected_book["book_id"]
#                                 )
#                                 st.experimental_rerun()
#                 else:
#                     st.warning("No processed pages found for this selection")

    with tab3:
        st.header("Search Library")
#         search_query = st.text_input("Search by title, author or keyword")

#         if search_query:
#             results = db_manager.search_books(search_query)
#             if not results:
#                 st.info("No matching books found")
#             else:
#                 for book in results:
#                     with st.expander(f"{book['title']} by {book.get('author', 'Unknown')}"):
#                         st.write(f"**Subject:** {book.get('subject', 'N/A')}")
#                         status = db_manager.get_processing_status(book["book_id"])

#                         cols = st.columns([3,1])
#                         with cols[0]:
#                             st.caption(f"📄 {len(status['processed_pages'])}/{status['total_pages']} pages processed")
#                         with cols[1]:
#                             if st.button("View", key=f"view_{book['book_id']}"):
#                                 st.session_state.selected_book = book
#                                 st.session_state.current_tab = "Browse Library"
#                                 st.experimental_rerun()

if __name__ == "__main__":
    main()