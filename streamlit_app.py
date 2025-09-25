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
from streamlit.components.v1 import html as st_html

# Configure Streamlit page
st.set_page_config(
    page_title="Urdu Translator AI",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mobile detection JavaScript
mobile_js = """
<script>
function isMobile() {
    return window.innerWidth <= 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

if (isMobile()) {
    document.body.classList.add('mobile-mode');
    // Store mobile state in sessionStorage
    sessionStorage.setItem('isMobile', 'true');
}
</script>
"""

st.components.v1.html(mobile_js, height=0)

# Enhanced CSS with mobile-first responsive design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Nastaliq+Urdu:wght@400;500;600&display=swap');

    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --dark-gradient: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%);
        --surface-gradient: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
        --glass-bg: rgba(255, 255, 255, 0.08);
        --glass-border: rgba(255, 255, 255, 0.15);
        --text-primary: #ffffff;
        --text-secondary: #b4c6fc;
        --text-muted: #8892b0;
        --success: #64ffda;
        --warning: #ffb74d;
        --error: #ff5722;
        --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
        --shadow-xl: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }

    .stApp {
        background: var(--dark-gradient);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
    }

    /* Animated background particles - subtle on mobile */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 40% 80%, rgba(120, 200, 255, 0.05) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
        animation: float 30s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-5px) rotate(0.5deg); }
    }

    .main-container {
        background: var(--glass-bg);
        backdrop-filter: blur(15px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem auto;
        max-width: 900px;
        box-shadow: var(--shadow-lg);
        position: relative;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .main-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--primary-gradient);
        opacity: 0.6;
        border-radius: 20px 20px 0 0;
    }

    .chat-message {
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-radius: 16px;
        max-width: 85%;
        word-wrap: break-word;
        line-height: 1.6;
        position: relative;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    @keyframes slideIn {
        from { 
            opacity: 0; 
            transform: translateY(15px) scale(0.98); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0) scale(1); 
        }
    }

    .user-message {
        background: var(--primary-gradient);
        color: var(--text-primary);
        margin-left: auto;
        text-align: right;
        font-family: 'Noto Nastaliq Urdu', 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 500;
        box-shadow: var(--shadow-lg);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .user-message::before {
        content: '👤';
        position: absolute;
        top: -6px;
        right: -6px;
        width: 24px;
        height: 24px;
        background: var(--accent-gradient);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        box-shadow: var(--shadow-lg);
    }

    .assistant-message {
        background: rgba(22, 33, 62, 0.7);
        color: var(--text-secondary);
        border: 1px solid rgba(116, 75, 162, 0.3);
        margin-right: auto;
        font-size: 0.95rem;
        line-height: 1.6;
        box-shadow: var(--shadow-lg);
        backdrop-filter: blur(15px);
    }

    .assistant-message::before {
        content: '🤖';
        position: absolute;
        top: -6px;
        left: -6px;
        width: 24px;
        height: 24px;
        background: var(--secondary-gradient);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        box-shadow: var(--shadow-lg);
    }

    .header-title {
        text-align: center;
        background: var(--primary-gradient);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: -0.03em;
        position: relative;
        animation: glow 3s ease-in-out infinite alternate;
    }

    @keyframes glow {
        from { filter: drop-shadow(0 0 15px rgba(120, 119, 198, 0.2)); }
        to { filter: drop-shadow(0 0 25px rgba(120, 119, 198, 0.4)); }
    }

    .stTextArea textarea {
        border: 2px solid rgba(116, 75, 162, 0.3) !important;
        border-radius: 14px !important;
        font-size: 1rem !important;
        color: var(--text-primary) !important;
        background: rgba(22, 33, 62, 0.5) !important;
        backdrop-filter: blur(10px) !important;
        padding: 16px !important;
        font-family: 'Noto Nastaliq Urdu', 'Inter', sans-serif !important;
        line-height: 1.7 !important;
        resize: vertical !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }

    .stTextArea textarea:focus {
        border: 2px solid #667eea !important;
        box-shadow: 0 0 15px rgba(120, 119, 198, 0.2), inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        outline: none !important;
        transform: scale(1.01) !important;
    }

    .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
        opacity: 1 !important;
        font-size: 0.95rem !important;
    }

    .stTextArea label {
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 10px !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--primary-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 28px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 50px !important;
        box-shadow: var(--shadow-lg) !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: var(--shadow-xl), 0 0 25px rgba(120, 119, 198, 0.3) !important;
    }

    .stButton > button:not([kind="primary"]) {
        background: rgba(116, 75, 162, 0.15) !important;
        color: var(--text-secondary) !important;
        border: 1px solid rgba(116, 75, 162, 0.3) !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 42px !important;
        backdrop-filter: blur(10px) !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: rgba(116, 75, 162, 0.25) !important;
        border-color: rgba(116, 75, 162, 0.5) !important;
        color: var(--text-primary) !important;
        transform: translateY(-1px) !important;
    }

    .stSidebar {
        background: rgba(12, 12, 12, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(116, 75, 162, 0.2) !important;
    }

    .stSidebar .stMarkdown h3 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid var(--primary-gradient) !important;
        background: var(--primary-gradient) !important;
        background-clip: text !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }

    .message-time {
        font-size: 0.8rem;
        opacity: 0.6;
        margin-top: 0.75rem;
        font-weight: 400;
        color: var(--text-muted);
    }

    .stForm {
        border: none !important;
        background: transparent !important;
    }

    .stSpinner > div {
        border-top-color: #667eea !important;
    }

    .loading-animation {
        display: inline-block;
        width: 36px;
        height: 36px;
        border: 3px solid rgba(120, 119, 198, 0.2);
        border-radius: 50%;
        border-top-color: #667eea;
        animation: spin 1s linear infinite, pulse 2s ease-in-out infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 15px rgba(120, 119, 198, 0.2); }
        50% { box-shadow: 0 0 25px rgba(120, 119, 198, 0.4); }
    }

    .copy-button {
        background: var(--accent-gradient) !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 4px 10px !important;
        color: white !important;
        font-size: 0.75rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        margin-top: 8px !important;
        opacity: 0.8 !important;
    }

    .copy-button:hover {
        opacity: 1 !important;
        transform: scale(1.05) !important;
    }

    .word-count {
        color: var(--text-muted);
        font-size: 0.8rem;
        text-align: right;
        margin-top: 6px;
        font-weight: 500;
        opacity: 0.4;
        transition: opacity 0.3s ease;
    }

    .quality-indicator {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-left: 6px;
        animation: blink 2s infinite;
    }

    .quality-high { background-color: var(--success); }
    .quality-medium { background-color: var(--warning); }
    .quality-low { background-color: var(--error); }

    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.4; }
    }

    .main .block-container {
        max-width: 1000px !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }

    hr {
        border: none !important;
        height: 1px !important;
        background: var(--primary-gradient) !important;
        opacity: 0.2 !important;
        border-radius: 1px !important;
    }

    .stMarkdown, .stText {
        color: var(--text-primary) !important;
    }

    /* Enhanced scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(116, 75, 162, 0.1);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--primary-gradient);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-gradient);
    }

    /* Mobile optimizations */
    @media (max-width: 768px) {
        .main-container {
            margin: 0.5rem;
            padding: 1rem;
            border-radius: 16px;
        }

        .chat-message {
            max-width: 95%;
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
        }

        .header-title {
            font-size: 2rem;
            margin-bottom: 1rem;
        }

        .stTextArea textarea {
            font-size: 0.95rem !important;
            padding: 12px !important;
        }

        .stButton > button[kind="primary"] {
            height: 46px !important;
            font-size: 0.95rem !important;
            padding: 12px 24px !important;
        }

        .stButton > button:not([kind="primary"]) {
            height: 40px !important;
            font-size: 0.85rem !important;
        }

        .user-message::before,
        .assistant-message::before {
            width: 20px;
            height: 20px;
            font-size: 0.6rem;
            top: -4px;
        }

        .user-message::before {
            right: -4px;
        }

        .assistant-message::before {
            left: -4px;
        }

        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        .word-count {
            font-size: 0.75rem;
            opacity: 0.3;
        }

        .stApp::before {
            animation: float 40s ease-in-out infinite;
        }
    }

    /* Extra small devices */
    @media (max-width: 480px) {
        .main-container {
            margin: 0.25rem;
            padding: 0.75rem;
        }

        .header-title {
            font-size: 1.75rem;
        }

        .chat-message {
            padding: 0.5rem 0.75rem;
        }
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
    if 'translation_history' not in st.session_state:
        st.session_state.translation_history = []


# ============================================
# MODEL LOADING (Original logic preserved)
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
            time.sleep(0.2 + len(cleaned) * 0.003)

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
# UTILITY FUNCTIONS (New features)
# ============================================

def get_translation_quality(translation, time_taken):
    """Determine translation quality based on length and time"""
    if len(translation) > 50 and time_taken < 1.0:
        return "high"
    elif len(translation) > 20 and time_taken < 2.0:
        return "medium"
    else:
        return "low"


def count_words(text):
    """Count words in text"""
    if not text:
        return 0
    return len(text.split())


def format_translation_with_copy(translation, quality):
    quality_class = f"quality-{quality}"
    safe_translation = translation.replace("'", "\\'").replace("\n", "\\n")

    st.markdown(f"""
    <div>
        <strong>Translation:</strong>
        <span class="quality-indicator {quality_class}"></span><br>
        {translation}
    </div>
    """, unsafe_allow_html=True)

    js_button = f"""
    <button class="copy-button" onclick="navigator.clipboard.writeText('{safe_translation}'); this.innerText='Copied!';">
      📋 Copy
    </button>
    """
    st_html(js_button, height=35)


# ============================================
# UI COMPONENTS (Enhanced & Mobile-Optimized)
# ============================================

def display_header():
    """Display clean, mobile-optimized header"""
    st.markdown("""
    <div class="main-container">
        <h1 class="header-title">🌙 Urdu Translator AI</h1>
    </div>
    """, unsafe_allow_html=True)


def display_sidebar():
    """Streamlined sidebar - mobile optimized with essential features only"""
    with st.sidebar:
        st.markdown("### 📚 Chat History")

        # Show recent translations in compact format
        if st.session_state.translation_history:
            recent_count = min(5, len(st.session_state.translation_history))
            for i, (urdu, roman) in enumerate(st.session_state.translation_history[-recent_count:]):
                with st.expander(f"#{len(st.session_state.translation_history) - recent_count + i + 1}",
                                 expanded=False):
                    st.write(f"**اردو:** {urdu[:40]}...")
                    st.write(f"**Roman:** {roman[:40]}...")
        else:
            st.info("No translations yet")

        st.markdown("---")

        # Essential controls only
        st.markdown("### 🎮 Controls")

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.translation_history = []
            st.rerun()

        if st.button("🔄 Reload Model", use_container_width=True):
            st.session_state.model_loaded = False
            st.session_state.translator = None
            st.cache_resource.clear()
            st.rerun()

        # Compact export feature
        if st.session_state.messages:
            st.markdown("---")
            if st.button("📄 Export", use_container_width=True):
                export_chat()


def export_chat():
    """Simplified export function"""
    if not st.session_state.messages:
        st.warning("No messages to export!")
        return

    export_text = f"# Urdu Translator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for i, message in enumerate(st.session_state.messages, 1):
        if message["role"] == "user":
            export_text += f"**Input {i // 2 + 1}:** {message['content']}\n"
        else:
            export_text += f"**Translation:** {message['content']}\n\n"

    st.download_button(
        label="📥 Download",
        data=export_text,
        file_name=f"urdu_translations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )


def display_chat():
    """Mobile-optimized chat display"""
    if st.session_state.messages:
        st.markdown('<div class="main-container">', unsafe_allow_html=True)

        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                word_count = count_words(message["content"])
                st.markdown(f"""
                <div class="chat-message user-message">
                    {message["content"]}
                    <div class="message-time">
                        {message.get("time", "")} • {word_count} words
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                time_taken = float(message.get("translation_time", "0"))
                quality = get_translation_quality(message["content"], time_taken)

                st.markdown('<div class="chat-message assistant-message">', unsafe_allow_html=True)
                format_translation_with_copy(message["content"], quality)
                st.markdown(f"""
                    <div class="message-time">
                        {message.get("time", "")} • {message.get("translation_time", "0.00")}s • {quality.title()}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


def display_input():
    """Mobile-optimized input form"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    with st.form("translation_form", clear_on_submit=True):
        urdu_text = st.text_area(
            "Enter Urdu Text:",
            placeholder="یہاں اردو متن لکھیں... (Type your Urdu text here...)",
            height=100,
            help="Enter Urdu text to translate to Roman Urdu",
            key="urdu_input"
        )

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            submit = st.form_submit_button("🚀 Translate", type="primary", use_container_width=True)
        with col2:
            clear = st.form_submit_button("Clear", use_container_width=True)
        with col3:
            if st.form_submit_button("Demo", use_container_width=True):
                demo_texts = [
                    "میں اردو سیکھ رہا ہوں",
                    "آج موسم بہت اچھا ہے",
                    "آپ کیسے ہیں؟",
                    "یہ کتاب دلچسپ ہے"
                ]
                import random
                return random.choice(demo_texts), True

    st.markdown('</div>', unsafe_allow_html=True)

    # Word count below form (transparent)
    if urdu_text:
        word_count = count_words(urdu_text)
        st.markdown(f'<div class="word-count">Words: {word_count} | Characters: {len(urdu_text)}</div>',
                    unsafe_allow_html=True)

    if clear:
        st.session_state.messages = []
        st.rerun()
        return "", False

    return urdu_text, submit


def process_translation(urdu_text):
    """Streamlined translation processing"""
    if not urdu_text.strip():
        st.warning("Please enter some Urdu text to translate.")
        return

    if not st.session_state.model_loaded or not st.session_state.translator:
        st.error("Model not loaded. Please wait for initialization.")
        return

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": urdu_text.strip(),
        "time": datetime.now().strftime("%H:%M:%S")
    })

    # Translate
    with st.spinner("Translating..."):
        try:
            max_length = st.session_state.get('max_length', 200)
            translation, time_taken = st.session_state.translator.translate(
                urdu_text.strip(), max_length
            )

            clean_translation = re.sub(r'<[^>]+>', '', str(translation)).strip()

            if clean_translation.startswith("Error:"):
                st.error(f"Translation failed: {clean_translation}")
                return

            # Add to history
            st.session_state.translation_history.append((urdu_text.strip(), clean_translation))

            # Keep only last 10 translations
            if len(st.session_state.translation_history) > 10:
                st.session_state.translation_history = st.session_state.translation_history[-10:]

            # Add assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": clean_translation,
                "time": datetime.now().strftime("%H:%M:%S"),
                "translation_time": f"{time_taken:.2f}"
            })

        except Exception as e:
            st.error(f"Translation error: {str(e)}")
            print(f"Translation error: {e}")
            return

    st.rerun()


def display_classy_loading():
    """Clean loading spinner for app startup"""
    st.markdown("""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
        text-align: center;
        padding: 2rem;
    ">
        <div class="loading-animation" style="margin-bottom: 2rem;"></div>
        <h3 style="
            color: var(--text-secondary);
            font-weight: 600;
            margin: 0;
            background: var(--primary-gradient);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        ">
            Initializing Urdu Translator
        </h3>
        <p style="
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-top: 1rem;
            opacity: 0.8;
        ">
            Setting up neural translation model...
        </p>
    </div>
    """, unsafe_allow_html=True)


def display_error_fallback(error_msg):
    """Clean error screen for model loading failures"""
    st.markdown(f"""
    <div class="main-container" style="text-align: center; padding: 3rem 2rem;">
        <h3 style="color: var(--warning); margin: 1rem 0;">
            Running in Demo Mode
        </h3>
        <div style="
            margin: 1.5rem 0;
            padding: 1.5rem;
            background: rgba(255, 183, 77, 0.1);
            border: 1px solid var(--warning);
            border-radius: 12px;
            color: var(--text-secondary);
            line-height: 1.6;
        ">
            <p style="margin: 0;">
                Neural model unavailable. Using enhanced transliteration with common word mappings.
            </p>
        </div>
        <small style="color: var(--text-muted); opacity: 0.7;">
            Error: {error_msg[:100]}...
        </small>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# MAIN APPLICATION
# ============================================

def main():
    """Clean, mobile-optimized main application"""
    # Initialize session state
    init_session_state()

    # Show loading only on first visit
    if not st.session_state.model_loaded and not st.session_state.model_loading and not st.session_state.messages:
        display_classy_loading()
        st.session_state.model_loading = True

        # Load model
        with st.spinner(""):
            translator, error = load_translator_model()
            st.session_state.translator = translator
            st.session_state.model_loaded = True
            st.session_state.model_loading = False
            st.session_state.error_state = error

        st.rerun()

    # Display header
    display_header()

    # Show error fallback if model failed but continue with demo
    if st.session_state.error_state and not st.session_state.messages:
        display_error_fallback(st.session_state.error_state)

    # Display sidebar
    display_sidebar()

    # Main interface
    if st.session_state.model_loaded:
        # Display chat
        display_chat()

        # Display input
        urdu_input, submit_button = display_input()

        # Process translation
        if submit_button and urdu_input:
            process_translation(urdu_input)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        with st.expander("Debug Info"):
            st.code(f"Error: {e}\n\nTraceback:\n{traceback.format_exc()}")
        print(f"App error: {e}")
        print(f"Traceback: {traceback.format_exc()}")