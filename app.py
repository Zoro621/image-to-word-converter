"""
DocuVision - Image to Document Extraction
A modern Streamlit application that extracts text from handwritten images
using Qwen2.5-VL vision model and generates formatted Word documents.
"""
import streamlit as st
from PIL import Image
import os
import time
from pathlib import Path

# Import custom utilities
from utils.image_utils import validate_image, prepare_image_for_model, get_image_dimensions
from utils.vision_extractor import VisionExtractor, get_available_models, get_model_info, AVAILABLE_MODELS
from utils.docx_generator import generate_docx


# Page configuration
st.set_page_config(
    page_title="DocuVision - Image to Document",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def load_css():
    """Load custom CSS styles."""
    css_path = Path(__file__).parent / "styles" / "custom.css"
    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Additional inline styles for components
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
        }
        
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(99, 102, 241, 0.5);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(99, 102, 241, 0.7);
        }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the application header."""
    st.markdown("""
    <div class="title-container" style="text-align: center; padding: 2rem 0;">
        <h1 style="
            font-family: 'Outfit', sans-serif;
            font-size: 3.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #818cf8 0%, #a855f7 50%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        ">📄 DocuVision</h1>
        <p style="
            font-family: 'Inter', sans-serif;
            font-size: 1.2rem;
            color: #94a3b8;
            font-weight: 400;
            letter-spacing: 0.02em;
        ">Transform handwritten notes into editable documents with AI</p>
    </div>
    """, unsafe_allow_html=True)


def render_features():
    """Render feature cards using Streamlit columns."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            height: 200px;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🔍</div>
            <h3 style="
                font-family: 'Outfit', sans-serif;
                font-size: 1.1rem;
                font-weight: 600;
                color: #f8fafc;
                margin-bottom: 0.5rem;
            ">Smart Extraction</h3>
            <p style="
                font-family: 'Inter', sans-serif;
                font-size: 0.85rem;
                color: #94a3b8;
                line-height: 1.5;
            ">AI-powered text recognition for handwritten notes and diagrams</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            height: 200px;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📝</div>
            <h3 style="
                font-family: 'Outfit', sans-serif;
                font-size: 1.1rem;
                font-weight: 600;
                color: #f8fafc;
                margin-bottom: 0.5rem;
            ">Format Preservation</h3>
            <p style="
                font-family: 'Inter', sans-serif;
                font-size: 0.85rem;
                color: #94a3b8;
                line-height: 1.5;
            ">Maintains headings, lists, tables, and text emphasis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            height: 200px;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📄</div>
            <h3 style="
                font-family: 'Outfit', sans-serif;
                font-size: 1.1rem;
                font-weight: 600;
                color: #f8fafc;
                margin-bottom: 0.5rem;
            ">Word Export</h3>
            <p style="
                font-family: 'Inter', sans-serif;
                font-size: 0.85rem;
                color: #94a3b8;
                line-height: 1.5;
            ">Download formatted .docx files ready for editing</p>
        </div>
        """, unsafe_allow_html=True)


def render_upload_zone():
    """Render the file upload zone."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
        border: 2px dashed rgba(99, 102, 241, 0.4);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    ">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📤</div>
        <p style="
            font-family: 'Inter', sans-serif;
            color: #94a3b8;
            font-size: 1rem;
        ">
            <strong style="color: #818cf8;">Drop your image here</strong> or click to browse
        </p>
        <p style="
            font-family: 'Inter', sans-serif;
            color: #64748b;
            font-size: 0.85rem;
            margin-top: 0.5rem;
        ">Supports JPG and PNG • Max 10MB</p>
    </div>
    """, unsafe_allow_html=True)


def render_processing_animation():
    """Render processing animation."""
    st.markdown("""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem;
        text-align: center;
    ">
        <div style="
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        ">
            <div style="
                width: 12px;
                height: 12px;
                background: #6366f1;
                border-radius: 50%;
                animation: bounce 1.4s infinite ease-in-out;
                animation-delay: -0.32s;
            "></div>
            <div style="
                width: 12px;
                height: 12px;
                background: #8b5cf6;
                border-radius: 50%;
                animation: bounce 1.4s infinite ease-in-out;
                animation-delay: -0.16s;
            "></div>
            <div style="
                width: 12px;
                height: 12px;
                background: #a855f7;
                border-radius: 50%;
                animation: bounce 1.4s infinite ease-in-out;
            "></div>
        </div>
        <p style="
            font-family: 'Inter', sans-serif;
            color: #94a3b8;
            font-size: 1.1rem;
        ">Analyzing your image with AI...</p>
        <p style="
            font-family: 'Inter', sans-serif;
            color: #64748b;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        ">This may take a moment</p>
    </div>
    <style>
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
    </style>
    """, unsafe_allow_html=True)


def render_success_message(message: str):
    """Render success message."""
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem 1.5rem;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        color: #34d399;
        font-family: 'Inter', sans-serif;
        margin: 1rem 0;
    ">
        <span style="font-size: 1.25rem;">✅</span>
        <span>{message}</span>
    </div>
    """, unsafe_allow_html=True)


def render_error_message(message: str):
    """Render error message."""
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem 1.5rem;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 12px;
        color: #fca5a5;
        font-family: 'Inter', sans-serif;
        margin: 1rem 0;
    ">
        <span style="font-size: 1.25rem;">❌</span>
        <span>{message}</span>
    </div>
    """, unsafe_allow_html=True)


def get_extractor(model_key: str = "Qwen3-VL-8B"):
    """Get or create the vision extractor instance for the selected model."""
    # Create a unique key for each model
    extractor_key = f'extractor_{model_key}'
    
    if extractor_key not in st.session_state:
        # Check for HuggingFace token safely
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            try:
                hf_token = st.secrets.get("HF_TOKEN", None)
            except Exception:
                hf_token = None
        
        # Check for OpenAI API key safely
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            try:
                openai_key = st.secrets.get("OPENAI_API_KEY", None)
            except Exception:
                openai_key = None
        
        try:
            st.session_state[extractor_key] = VisionExtractor(
                hf_token=hf_token,
                openai_key=openai_key,
                model_key=model_key
            )
        except Exception as e:
            st.session_state[extractor_key] = None
            st.session_state[f'{extractor_key}_error'] = str(e)
    
    return st.session_state.get(extractor_key)


def process_image(uploaded_file, model_key: str = "Qwen3-VL-8B") -> tuple[str, bool]:
    """
    Process the uploaded image and extract text.
    
    Args:
        uploaded_file: The uploaded image file
        model_key: The model to use for extraction
    
    Returns:
        Tuple of (extracted_text, success)
    """
    try:
        # Prepare image
        image, _ = prepare_image_for_model(uploaded_file)
        
        # Get extractor for selected model
        extractor = get_extractor(model_key)
        
        if extractor is None:
            error_key = f'extractor_{model_key}_error'
            error_msg = st.session_state.get(error_key, 'Vision extractor not available')
            return f"Error: {error_msg}", False
        
        # Extract text
        extracted_text = extractor.extract_text(image)
        
        return extracted_text, True
        
    except Exception as e:
        return f"Error processing image: {str(e)}", False


def main():
    """Main application entry point."""
    # Load CSS
    load_css()
    
    # Render header
    render_header()
    
    # Initialize session state
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = None
    if 'uploaded_image' not in st.session_state:
        st.session_state.uploaded_image = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "Qwen3-VL-8B"
    
    # Render features
    render_features()
    
    # Main content area with model selector
    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
    ">
    """, unsafe_allow_html=True)
    
    # Model selector section
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <span style="font-size: 1.5rem;">🤖</span>
        <span style="
            font-family: 'Outfit', sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: #f8fafc;
        ">Select Vision Model</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Model selector dropdown
    model_options = get_available_models()
    model_col1, model_col2 = st.columns([2, 3])
    
    with model_col1:
        selected_model = st.selectbox(
            "Vision Model",
            options=model_options,
            index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0,
            label_visibility="collapsed",
            key="model_selector"
        )
        st.session_state.selected_model = selected_model
    
    with model_col2:
        model_info = get_model_info(selected_model)
        st.markdown(f"""
        <p style="
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            color: #94a3b8;
            margin: 0;
            padding: 0.5rem 0;
        ">💡 {model_info['description']}</p>
        """, unsafe_allow_html=True)
    
    # File uploader
    render_upload_zone()
    uploaded_file = st.file_uploader(
        "Upload Image",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a JPG or PNG image of handwritten notes",
        label_visibility="collapsed"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Process uploaded file
    if uploaded_file is not None:
        # Store uploaded image
        st.session_state.uploaded_image = uploaded_file
        
        # Create columns for preview
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 1.5rem;
                margin-top: 1rem;
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    margin-bottom: 1rem;
                    padding-bottom: 0.75rem;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                ">
                    <span style="font-size: 1.25rem;">🖼️</span>
                    <span style="
                        font-family: 'Outfit', sans-serif;
                        font-size: 1rem;
                        font-weight: 600;
                        color: #f8fafc;
                    ">Original Image</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Display image
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)
            
            # Show image info
            dims = get_image_dimensions(image)
            st.markdown(f"""
                <p style="
                    font-family: 'Inter', sans-serif;
                    font-size: 0.85rem;
                    color: #64748b;
                    margin-top: 0.5rem;
                ">📐 {dims['width']} × {dims['height']} pixels</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 1.5rem;
                margin-top: 1rem;
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    margin-bottom: 1rem;
                    padding-bottom: 0.75rem;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                ">
                    <span style="font-size: 1.25rem;">📝</span>
                    <span style="
                        font-family: 'Outfit', sans-serif;
                        font-size: 1rem;
                        font-weight: 600;
                        color: #f8fafc;
                    ">Extracted Text</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Extract button
            if st.button("🚀 Extract Text", use_container_width=True, type="primary"):
                st.session_state.processing = True
                
                with st.spinner(""):
                    render_processing_animation()
                    
                    # Reset file position
                    uploaded_file.seek(0)
                    
                    # Process image with selected model
                    extracted_text, success = process_image(uploaded_file, st.session_state.selected_model)
                    
                    if success:
                        st.session_state.extracted_text = extracted_text
                        st.session_state.processing = False
                        st.rerun()
                    else:
                        st.session_state.processing = False
                        render_error_message(extracted_text)
            
            # Display extracted text if available
            if st.session_state.extracted_text:
                st.markdown(f"""
                <div style="
                    font-family: 'Inter', sans-serif;
                    font-size: 0.9rem;
                    color: #94a3b8;
                    line-height: 1.7;
                    max-height: 400px;
                    overflow-y: auto;
                    padding-right: 0.5rem;
                    white-space: pre-wrap;
                ">{st.session_state.extracted_text[:2000]}{'...' if len(st.session_state.extracted_text) > 2000 else ''}</div>
                """, unsafe_allow_html=True)
                
                render_success_message("Text extracted successfully!")
            else:
                st.markdown("""
                <p style="
                    font-family: 'Inter', sans-serif;
                    font-size: 0.9rem;
                    color: #64748b;
                    text-align: center;
                    padding: 2rem;
                ">Click "Extract Text" to begin processing</p>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Download section
        if st.session_state.extracted_text:
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Generate document
            try:
                doc_buffer = generate_docx(
                    st.session_state.extracted_text,
                    title="Extracted Document"
                )
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label="📥 Download Word Document",
                        data=doc_buffer,
                        file_name="extracted_document.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                    
            except Exception as e:
                render_error_message(f"Error generating document: {str(e)}")
    
    # Footer
    st.markdown("""
    <div style="
        text-align: center;
        padding: 3rem 0 1rem 0;
        color: #64748b;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
    ">
        <p>Powered by <strong style="color: #818cf8;">Qwen2.5-VL</strong> Vision Model</p>
        <p style="margin-top: 0.5rem; opacity: 0.7;">Built with ❤️ using Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
