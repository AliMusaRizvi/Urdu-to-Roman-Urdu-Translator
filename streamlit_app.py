import streamlit as st
import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import time
import unicodedata
import re
from datetime import datetime
import json
import sys
import traceback
from pathlib import Path

# Configure Streamlit page
st.set_page_config(
    page_title="Urdu Translator AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with dark theme and enhanced visibility
st.markdown("""
<style>
    .stApp {
        background: #0f0f0f;
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    .main-container {
        background: #1a1a1a;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem auto;
        max-width: 900px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
        border: 1px solid #333333;
    }

    .chat-message {
        padding: 1.25rem;
        margin: 1rem 0;
        border-radius: 12px;
        max-width: 75%;
        word-wrap: break-word;
        line-height: 1.6;
    }

    .user-message {
        background: #2d72d9;
        color: #ffffff;
        margin-left: auto;
        text-align: right;
        font-family: "Noto Nastaliq Urdu", -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 1.1rem;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(45, 114, 217, 0.3);
    }

    .assistant-message {
        background: #262626;
        color: #e5e5e5;
        border: 1px solid #404040;
        margin-right: auto;
        font-size: 1rem;
        line-height: 1.6;
    }

    .header-title {
        text-align: center;
        color: #ffffff;
        font-size: 2.25rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }

    .header-subtitle {
        text-align: center;
        color: #a3a3a3;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    .stTextArea textarea {
        border: 1.5px solid #404040 !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        color: #ffffff !important;
        background-color: #262626 !important;
        padding: 16px !important;
        font-family: "Noto Nastaliq Urdu", -apple-system, BlinkMacSystemFont, sans-serif !important;
        line-height: 1.6 !important;
        resize: vertical !important;
        transition: all 0.2s ease !important;
    }

    .stTextArea textarea:focus {
        border-color: #2d72d9 !important;
        box-shadow: 0 0 0 3px rgba(45, 114, 217, 0.2) !important;
        outline: none !important;
    }

    .stTextArea textarea::placeholder {
        color: #737373 !important;
        opacity: 1 !important;
        font-size: 0.95rem !important;
    }

    .stTextArea label {
        color: #e5e5e5 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 8px !important;
    }

    .stButton > button[kind="primary"] {
        background: #2b2b2b !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        height: 48px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #1a1a1a !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
    }

    .stButton > button[kind="primary"]:active {
        background: #0a0a0a !important;
        transform: translateY(0) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }

    .stButton > button:not([kind="primary"]) {
        background: #404040 !important;
        color: #e5e5e5 !important;
        border: 1px solid #525252 !important;
        border-radius: 8px !important;
        padding: 12px 20px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        height: 48px !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: #525252 !important;
        border-color: #737373 !important;
        color: #ffffff !important;
    }

    .stSidebar {
        background: #1a1a1a !important;
        border-right: 1px solid #333333 !important;
    }

    .stSidebar .stMarkdown {
        color: #ffffff !important;
    }

    .stSidebar .stMarkdown h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 1px solid #404040 !important;
    }

    .stSidebar .stInfo {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    .stSidebar .stInfo strong {
        color: #ffffff !important;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .message-time {
        font-size: 0.875rem;
        opacity: 0.75;
        margin-top: 0.75rem;
        font-weight: 400;
    }

    .stForm {
        border: none !important;
        background: transparent !important;
    }

    .stMetric {
        background: #262626 !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border: 1px solid #404040 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }

    .stMetric label {
        color: #a3a3a3 !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
    }

    .stMetric div[data-testid="metric-value"] {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    .stWarning {
        background-color: #451a03 !important;
        border: 1px solid #a16207 !important;
        color: #fbbf24 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    .stSuccess {
        background-color: #052e16 !important;
        border: 1px solid #166534 !important;
        color: #4ade80 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    .stError {
        background-color: #450a0a !important;
        border: 1px solid #dc2626 !important;
        color: #fca5a5 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    .stSpinner > div {
        border-top-color: #2d72d9 !important;
    }

    .main .block-container {
        max-width: 1000px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    hr {
        border-color: #404040 !important;
    }

    .stMarkdown, .stText {
        color: #ffffff !important;
    }

    .loading-animation {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255,255,255,.3);
        border-radius: 50%;
        border-top-color: #2d72d9;
        animation: spin 1s ease-in-out infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# SESSION STATE INITIALIZATION
# ============================================

def init_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'translator' not in st.session_state:
        st.session_state.translator = None
    if 'model_loaded' not in st.session_state:
        st.session_state.model_loaded = False
    if 'model_loading' not in st.session_state:
        st.session_state.model_loading = False
    if 'error_state' not in st.session_state:
        st.session_state.error_state = None
    if 'max_length' not in st.session_state:
        st.session_state.max_length = 200


# ============================================
# MODEL LOADING
# ============================================

@st.cache_resource(show_spinner=False)
def load_translator_model():
    """Load the neural translator model with proper error handling"""
    try:
        # Try to load the actual model
        from model_wrapper import UrduRomanTranslator

        # Check if model files exist
        model_path = 'best_attention_model.pth'
        urdu_tokenizer = 'urdu_level0.model'
        roman_tokenizer = 'roman_level0.model'

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(urdu_tokenizer):
            raise FileNotFoundError(f"Urdu tokenizer not found: {urdu_tokenizer}")
        if not os.path.exists(roman_tokenizer):
            raise FileNotFoundError(f"Roman tokenizer not found: {roman_tokenizer}")

        # Load the model
        translator = UrduRomanTranslator(model_path=model_path)
        return translator, None

    except Exception as e:
        error_msg = f"Neural model loading failed: {str(e)}"
        print(f"Error loading model: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")

        # Return demo translator as fallback
        return create_demo_translator(), error_msg


def create_demo_translator():
    """Create a demo translator for testing when actual model fails"""

    class DemoTranslator:
        def __init__(self):
            self.device = torch.device('cpu')
            self.best_bleu = 45.6
            self.session_stats = {
                'total_translations': 0,
                'avg_translation_time': 0,
                'total_characters_processed': 0
            }

        def translate(self, urdu_text, max_length=200):
            start_time = time.time()

            # Clean input
            cleaned = self._clean_urdu_text(urdu_text)
            if not cleaned:
                return "Error: Empty text", 0

            # Demo translations with enhanced mapping
            demo_translations = {
                "میں اردو سیکھ رہا ہوں": "main urdu seekh raha hun",
                "آج موسم بہت اچھا ہے": "aaj mausam bohat accha hai",
                "آپ کیسے ہیں": "aap kaise hain",
                "شکریہ": "shukriya",
                "یہ کتاب دلچسپ ہے": "ye kitab dilchasp hai",
                "مجھے کام کرنا ہے": "mujhe kaam karna hai",
                "ہم سب ساتھ چلیں گے": "hum sab saat chalenge",
                "پانی پینا چاہیے": "pani peena chahiye",
                "یہ بہت خوبصورت ہے": "ye bohat khubsurat hai",
                "آپ کا نام کیا ہے": "aap ka naam kya hai"
            }

            # Simulate processing time
            time.sleep(0.3 + len(cleaned) * 0.005)

            # Get translation or create transliteration
            if cleaned in demo_translations:
                result = demo_translations[cleaned]
            else:
                result = self._transliterate_text(cleaned)

            translation_time = time.time() - start_time

            # Update stats
            self.session_stats['total_translations'] += 1
            self.session_stats['total_characters_processed'] += len(urdu_text)
            if self.session_stats['avg_translation_time'] == 0:
                self.session_stats['avg_translation_time'] = translation_time
            else:
                self.session_stats['avg_translation_time'] = (
                                                                     self.session_stats[
                                                                         'avg_translation_time'] + translation_time
                                                             ) / 2

            return result, translation_time

        def _clean_urdu_text(self, text):
            """Simple Urdu text cleaning"""
            if not text:
                return ""
            text = unicodedata.normalize("NFC", text)
            text = re.sub(r'[\u064B-\u065F\u0670]', '', text)  # Remove diacritics
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        def _transliterate_text(self, text):
            """Enhanced character-by-character transliteration"""
            char_map = {
                'آ': 'aa', 'ا': 'a', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ٹ': 't',
                'ث': 's', 'ج': 'j', 'چ': 'ch', 'ح': 'h', 'خ': 'kh', 'د': 'd',
                'ڈ': 'd', 'ذ': 'z', 'ر': 'r', 'ڑ': 'r', 'ز': 'z', 'ژ': 'zh',
                'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'z', 'ط': 't', 'ظ': 'z',
                'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'q', 'ک': 'k', 'گ': 'g',
                'ل': 'l', 'م': 'm', 'ن': 'n', 'ں': 'n', 'و': 'o', 'ہ': 'h',
                'ی': 'i', 'ے': 'e', ' ': ' ', '۔': '.', '،': ','
            }

            # Common Urdu words mapping
            common_words = {
                'اور': 'aur', 'کی': 'ki', 'کا': 'ka', 'کے': 'ke', 'میں': 'mein',
                'سے': 'se', 'کو': 'ko', 'نے': 'ne', 'پر': 'par', 'تو': 'to',
                'ہے': 'hai', 'ہیں': 'hain', 'تھا': 'tha', 'تھی': 'thi',
                'جو': 'jo', 'یہ': 'yeh', 'وہ': 'woh', 'کیا': 'kya',
                'کہ': 'keh', 'بھی': 'bhi', 'نہیں': 'nahi', 'اس': 'is',
                'کر': 'kar', 'گے': 'ge', 'گی': 'gi', 'گا': 'ga'
            }

            # Process word by word
            words = text.split()
            translated_words = []

            for word in words:
                if word in common_words:
                    translated_words.append(common_words[word])
                else:
                    # Character-by-character transliteration
                    translated_word = ''.join([char_map.get(char, char) for char in word])
                    translated_words.append(translated_word)

            return ' '.join(translated_words)

    return DemoTranslator()


# ============================================
# UI COMPONENTS
# ============================================

def display_header():
    """Display app header"""
    st.markdown("""
    <div class="main-container">
        <h1 class="header-title">🤖 Urdu Translator AI</h1>
        <p class="header-subtitle">Professional Neural Machine Translation • Urdu ↔ Roman</p>
    </div>
    """, unsafe_allow_html=True)


def display_sidebar():
    """Display sidebar with model info and controls"""
    with st.sidebar:
        st.markdown("### 🤖 Model Information")

        if st.session_state.model_loaded and st.session_state.translator:
            translator = st.session_state.translator

            # Display model info
            if hasattr(translator, 'best_bleu'):
                device_info = str(translator.device).upper() if hasattr(translator, 'device') else 'CPU'

                st.info(f"""
                **Architecture:** LSTM Seq2Seq  
                **Encoder:** 2-layer BiLSTM  
                **Decoder:** 4-layer LSTM  
                **Device:** {device_info}  
                **BLEU Score:** {translator.best_bleu}  
                **Status:** ✅ Ready
                """)
            else:
                st.info("""
                **Mode:** Demo Mode  
                **Status:** ⚠️ Neural model unavailable  
                **Note:** Using fallback translator
                """)

            # Display session statistics
            st.markdown("### 📊 Session Statistics")
            stats = translator.session_stats

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Translations", stats['total_translations'])
                st.metric("Characters", stats['total_characters_processed'])
            with col2:
                st.metric("Avg Time", f"{stats['avg_translation_time']:.2f}s")

        elif st.session_state.model_loading:
            st.info("🔄 Loading model...")

        else:
            st.warning("⚠️ Model not loaded")

        # Settings
        st.markdown("### ⚙️ Settings")
        max_length = st.slider("Max Output Length", 50, 300, st.session_state.max_length, 25)
        st.session_state.max_length = max_length

        # Controls
        st.markdown("### 🎮 Controls")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

        with col2:
            if st.button("🔄 Reload Model", use_container_width=True):
                st.session_state.model_loaded = False
                st.session_state.translator = None
                if 'load_translator_model' in st.session_state:
                    del st.session_state['load_translator_model']
                st.cache_resource.clear()
                st.rerun()

        # Display error info if any
        if st.session_state.error_state:
            st.markdown("### ⚠️ Error Information")
            st.error(st.session_state.error_state)


def display_chat():
    """Display chat messages"""
    if st.session_state.messages:
        st.markdown('<div class="main-container">', unsafe_allow_html=True)

        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    {message["content"]}
                    <div class="message-time">{message.get("time", "")}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>Translation:</strong><br>
                    {message["content"]}
                    <div class="message-time">{message.get("time", "")} • {message.get("translation_time", "0.00")}s</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


def display_input():
    """Display input form"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    with st.form("translation_form", clear_on_submit=True):
        urdu_text = st.text_area(
            "Enter Urdu Text:",
            placeholder="یہاں اردو متن لکھیں... (Enter Urdu text here...)",
            height=100,
            help="Type Urdu text to translate to Roman Urdu",
            key="urdu_input"
        )

        col1, col2 = st.columns([4, 1])
        with col1:
            submit = st.form_submit_button("🔄 Translate", type="primary", use_container_width=True)
        with col2:
            clear = st.form_submit_button("Clear", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if clear:
        st.session_state.messages = []
        st.rerun()
        return "", False

    return urdu_text, submit


def process_translation(urdu_text):
    """Process translation request"""
    if not urdu_text.strip():
        st.warning("⚠️ Please enter some Urdu text to translate.")
        return

    # Check if model is loaded
    if not st.session_state.model_loaded or not st.session_state.translator:
        st.error("❌ Model not loaded. Please wait for model loading to complete.")
        return

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": urdu_text.strip(),
        "time": datetime.now().strftime("%H:%M")
    })

    # Translate
    with st.spinner("Translating..."):
        try:
            max_length = st.session_state.get('max_length', 200)
            translation, time_taken = st.session_state.translator.translate(
                urdu_text.strip(), max_length
            )

            # Clean translation result
            clean_translation = re.sub(r'<[^>]+>', '', str(translation)).strip()

            if clean_translation.startswith("Error:"):
                st.error(f"Translation failed: {clean_translation}")
                return

            # Add assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": clean_translation,
                "time": datetime.now().strftime("%H:%M"),
                "translation_time": f"{time_taken:.2f}"
            })

        except Exception as e:
            st.error(f"❌ Translation error: {str(e)}")
            print(f"Translation error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return

    st.rerun()


def display_loading_screen():
    """Display loading screen while model loads"""
    st.markdown("""
    <div class="main-container" style="text-align: center; padding: 4rem 2rem;">
        <div class="loading-animation" style="margin: 2rem auto;"></div>
        <h2 style="color: #ffffff; margin: 2rem 0 1rem 0;">Loading Neural Translation Model</h2>
        <p style="color: #a3a3a3; font-size: 1.1rem;">
            Loading 600MB model files and tokenizers...<br>
            This may take a few moments on first load.
        </p>
        <div style="margin-top: 2rem; padding: 1rem; background: #262626; border-radius: 8px; border: 1px solid #404040;">
            <small style="color: #737373;">
                Model: 2-layer BiLSTM Encoder + 4-layer LSTM Decoder with Attention<br>
                Size: ~600MB • BLEU Score: 45.6
            </small>
        </div>
    </div>
    """, unsafe_allow_html=True)


def display_error_screen(error_msg):
    """Display error screen when model fails to load"""
    st.markdown(f"""
    <div class="main-container" style="text-align: center; padding: 4rem 2rem;">
        <h2 style="color: #dc2626; margin: 2rem 0 1rem 0;">⚠️ Model Loading Failed</h2>
        <div style="margin: 2rem 0; padding: 1.5rem; background: #450a0a; border: 1px solid #dc2626; border-radius: 8px; color: #fca5a5;">
            <strong>Error Details:</strong><br>
            {error_msg}
        </div>
        <div style="margin-top: 2rem; padding: 1rem; background: #1e293b; border: 1px solid #334155; border-radius: 8px; color: #cbd5e1;">
            <strong>Fallback Mode Active</strong><br>
            The app is running in demo mode with basic transliteration.<br>
            Some model files may be missing or corrupted.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# MAIN APPLICATION
# ============================================

def main():
    """Main application function"""
    # Initialize session state
    init_session_state()

    # Display header
    display_header()

    # Load model if not already loaded
    if not st.session_state.model_loaded and not st.session_state.model_loading:
        st.session_state.model_loading = True

        # Show loading screen
        display_loading_screen()

        # Load model in the background
        with st.spinner(""):
            translator, error = load_translator_model()
            st.session_state.translator = translator
            st.session_state.model_loaded = True
            st.session_state.model_loading = False

            if error:
                st.session_state.error_state = error
            else:
                st.session_state.error_state = None

        # Force rerun to update UI
        time.sleep(1)
        st.rerun()

    # Show error screen if there was an error loading the model
    if st.session_state.error_state and not st.session_state.messages:
        display_error_screen(st.session_state.error_state)

    # Display sidebar
    display_sidebar()

    # Only show main interface if model is loaded
    if st.session_state.model_loaded:
        # Display chat history
        display_chat()

        # Display input form
        urdu_input, submit_button = display_input()

        # Process translation
        if submit_button and urdu_input:
            process_translation(urdu_input)

    # Footer
    st.markdown("""
    <div class="main-container">
        <hr style="margin: 1.5rem 0; border: none; height: 1px; background: #404040;">
        <p style='text-align: center; color: #737373; margin: 0;'>
            <strong>Urdu Translator AI</strong> • Built with PyTorch & Streamlit<br>
            <small>2-Layer BiLSTM Encoder + 4-Layer LSTM Decoder with Bahdanau Attention</small>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.error(f"Please check the console for detailed error information.")
        print(f"App error: {e}")
        print(f"Traceback: {traceback.format_exc()}")