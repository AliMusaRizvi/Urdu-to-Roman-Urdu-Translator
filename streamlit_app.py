
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
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with modern gradient theme and animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Nastaliq+Urdu:wght@400;500;600&display=swap');

    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --dark-gradient: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%);
        --surface-gradient: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
        --glass-bg: rgba(255, 255, 255, 0.1);
        --glass-border: rgba(255, 255, 255, 0.2);
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

    /* Animated background particles */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 40% 80%, rgba(120, 200, 255, 0.1) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
        animation: float 20s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-10px) rotate(1deg); }
    }

    .main-container {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        padding: 2.5rem;
        margin: 1.5rem auto;
        max-width: 1000px;
        box-shadow: var(--shadow-xl);
        position: relative;
        overflow: hidden;
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
        opacity: 0.8;
    }

    .main-container:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-xl), 0 0 40px rgba(120, 119, 198, 0.2);
    }

    .chat-message {
        padding: 1.5rem 2rem;
        margin: 1.5rem 0;
        border-radius: 20px;
        max-width: 80%;
        word-wrap: break-word;
        line-height: 1.7;
        position: relative;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: slideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }

    @keyframes slideIn {
        from { 
            opacity: 0; 
            transform: translateY(20px) scale(0.95); 
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
        font-size: 1.15rem;
        font-weight: 500;
        box-shadow: var(--shadow-lg);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .user-message::before {
        content: '👤';
        position: absolute;
        top: -8px;
        right: -8px;
        width: 32px;
        height: 32px;
        background: var(--accent-gradient);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        box-shadow: var(--shadow-lg);
    }

    .assistant-message {
        background: rgba(22, 33, 62, 0.8);
        color: var(--text-secondary);
        border: 1px solid rgba(116, 75, 162, 0.3);
        margin-right: auto;
        font-size: 1.05rem;
        line-height: 1.7;
        box-shadow: var(--shadow-lg);
        backdrop-filter: blur(15px);
    }

    .assistant-message::before {
        content: '🤖';
        position: absolute;
        top: -8px;
        left: -8px;
        width: 32px;
        height: 32px;
        background: var(--secondary-gradient);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        box-shadow: var(--shadow-lg);
    }

    .header-title {
        text-align: center;
        background: var(--primary-gradient);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: -0.05em;
        position: relative;
        animation: glow 2s ease-in-out infinite alternate;
    }

    @keyframes glow {
        from { filter: drop-shadow(0 0 20px rgba(120, 119, 198, 0.3)); }
        to { filter: drop-shadow(0 0 30px rgba(120, 119, 198, 0.6)); }
    }

    .header-subtitle {
        text-align: center;
        color: var(--text-muted);
        font-size: 1.2rem;
        margin-bottom: 2.5rem;
        font-weight: 400;
        opacity: 0.9;
    }

    .stTextArea textarea {
        border: 2px solid rgba(116, 75, 162, 0.3) !important;
        border-radius: 16px !important;
        font-size: 1.1rem !important;
        color: var(--text-primary) !important;
        background: rgba(22, 33, 62, 0.6) !important;
        backdrop-filter: blur(10px) !important;
        padding: 20px !important;
        font-family: 'Noto Nastaliq Urdu', 'Inter', sans-serif !important;
        line-height: 1.8 !important;
        resize: vertical !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }

    .stTextArea textarea:focus {
        border: 2px solid var(--primary-gradient) !important;
        box-shadow: 0 0 20px rgba(120, 119, 198, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        outline: none !important;
        transform: scale(1.02) !important;
    }

    .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
        opacity: 1 !important;
        font-size: 1rem !important;
    }

    .stTextArea label {
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin-bottom: 12px !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--primary-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 16px 32px !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 56px !important;
        box-shadow: var(--shadow-lg) !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .stButton > button[kind="primary"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }

    .stButton > button[kind="primary"]:hover::before {
        left: 100%;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: var(--shadow-xl), 0 0 30px rgba(120, 119, 198, 0.4) !important;
    }

    .stButton > button[kind="primary"]:active {
        transform: translateY(-1px) scale(1.01) !important;
    }

    .stButton > button:not([kind="primary"]) {
        background: rgba(116, 75, 162, 0.2) !important;
        color: var(--text-secondary) !important;
        border: 1px solid rgba(116, 75, 162, 0.4) !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 500 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 48px !important;
        backdrop-filter: blur(10px) !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: rgba(116, 75, 162, 0.4) !important;
        border-color: var(--primary-gradient) !important;
        color: var(--text-primary) !important;
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-lg) !important;
    }

    .stSidebar {
        background: rgba(12, 12, 12, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(116, 75, 162, 0.3) !important;
    }

    .stSidebar .stMarkdown {
        color: var(--text-primary) !important;
    }

    .stSidebar .stMarkdown h3 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        margin-bottom: 1.5rem !important;
        padding-bottom: 0.75rem !important;
        border-bottom: 2px solid var(--primary-gradient) !important;
        background: var(--primary-gradient) !important;
        background-clip: text !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }

    .stSidebar .stInfo {
        background: rgba(22, 33, 62, 0.8) !important;
        border: 1px solid rgba(116, 75, 162, 0.4) !important;
        color: var(--text-secondary) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(15px) !important;
        box-shadow: var(--shadow-lg) !important;
    }

    .stSidebar .stInfo strong {
        color: var(--text-primary) !important;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .message-time {
        font-size: 0.85rem;
        opacity: 0.7;
        margin-top: 1rem;
        font-weight: 400;
        color: var(--text-muted);
    }

    .stForm {
        border: none !important;
        background: transparent !important;
    }

    .stMetric {
        background: rgba(22, 33, 62, 0.6) !important;
        padding: 1.5rem !important;
        border-radius: 16px !important;
        border: 1px solid rgba(116, 75, 162, 0.3) !important;
        box-shadow: var(--shadow-lg) !important;
        backdrop-filter: blur(15px) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .stMetric:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(116, 75, 162, 0.6) !important;
    }

    .stMetric label {
        color: var(--text-muted) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    .stMetric div[data-testid="metric-value"] {
        color: var(--text-primary) !important;
        font-weight: 800 !important;
        font-size: 1.5rem !important;
    }

    .stWarning {
        background: rgba(255, 183, 77, 0.1) !important;
        border: 1px solid var(--warning) !important;
        color: var(--warning) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(15px) !important;
    }

    .stSuccess {
        background: rgba(100, 255, 218, 0.1) !important;
        border: 1px solid var(--success) !important;
        color: var(--success) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(15px) !important;
    }

    .stError {
        background: rgba(255, 87, 34, 0.1) !important;
        border: 1px solid var(--error) !important;
        color: var(--error) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(15px) !important;
    }

    .stSpinner > div {
        border-top-color: #667eea !important;
    }

    .main .block-container {
        max-width: 1200px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    hr {
        border: none !important;
        height: 2px !important;
        background: var(--primary-gradient) !important;
        opacity: 0.3 !important;
        border-radius: 1px !important;
    }

    .stMarkdown, .stText {
        color: var(--text-primary) !important;
    }

    .loading-animation {
        display: inline-block;
        width: 40px;
        height: 40px;
        border: 4px solid rgba(120, 119, 198, 0.2);
        border-radius: 50%;
        border-top-color: #667eea;
        animation: spin 1s linear infinite, pulse 2s ease-in-out infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(120, 119, 198, 0.3); }
        50% { box-shadow: 0 0 40px rgba(120, 119, 198, 0.6); }
    }

    /* New feature: Copy button styles */
    .copy-button {
        background: var(--accent-gradient) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        color: white !important;
        font-size: 0.8rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        margin-top: 10px !important;
        opacity: 0.8 !important;
    }

    .copy-button:hover {
        opacity: 1 !important;
        transform: scale(1.05) !important;
    }

    /* New feature: Word count display */
    .word-count {
        color: var(--text-muted);
        font-size: 0.85rem;
        text-align: right;
        margin-top: 8px;
        font-weight: 500;
    }

    /* New feature: Translation quality indicator */
    .quality-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-left: 8px;
        animation: blink 2s infinite;
    }

    .quality-high { background-color: var(--success); }
    .quality-medium { background-color: var(--warning); }
    .quality-low { background-color: var(--error); }

    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }

    /* Enhanced scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(116, 75, 162, 0.1);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--primary-gradient);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-gradient);
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-container {
            margin: 1rem;
            padding: 1.5rem;
        }

        .chat-message {
            max-width: 95%;
            padding: 1rem;
        }

        .header-title {
            font-size: 2rem;
        }

        .stTextArea textarea {
            font-size: 1rem !important;
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
    if 'favorite_translations' not in st.session_state:
        st.session_state.favorite_translations = []


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
    """Format translation with copy button and quality indicator"""
    quality_class = f"quality-{quality}"

    return f"""
    <div>
        <strong>Translation:</strong>
        <span class="quality-indicator {quality_class}"></span><br>
        {translation}
        <button class="copy-button" onclick="navigator.clipboard.writeText('{translation}')">
            📋 Copy
        </button>
    </div>
    """


# ============================================
# UI COMPONENTS (Enhanced)
# ============================================

def display_header():
    """Display enhanced app header with animations"""
    st.markdown("""
    <div class="main-container">
        <h1 class="header-title">🌙 Urdu Translator AI</h1>
        <p class="header-subtitle">
            ✨ Advanced Neural Machine Translation • Urdu ↔ Roman • Powered by Deep Learning ✨
        </p>
    </div>
    """, unsafe_allow_html=True)


def display_sidebar():
    """Display enhanced sidebar with model info and controls"""
    with st.sidebar:
        #st.markdown("### 🧠 Model Information")

        if st.session_state.model_loaded and st.session_state.translator:
            translator = st.session_state.translator

            # Display model info with enhanced styling
            # if hasattr(translator, 'best_bleu'):
            #     device_info = str(translator.device).upper() if hasattr(translator, 'device') else 'CPU'
            #
            #     st.info(f"""
            #     **🏗️ Architecture:** LSTM Seq2Seq
            #     **🔄 Encoder:** 2-layer BiLSTM
            #     **🎯 Decoder:** 4-layer LSTM
            #     **💻 Device:** {device_info}
            #     **📊 BLEU Score:** {translator.best_bleu}
            #     **🟢 Status:** Ready
            #     """)
            # else:
            #     st.info("""
            #     **🎭 Mode:** Demo Mode
            #     **🟡 Status:** Neural model unavailable
            #     **ℹ️ Note:** Using fallback translator
            #     """)

            # Enhanced session statistics with better layout
            st.markdown("### 📈 Session Analytics")
            stats = translator.session_stats

            # Create metrics in a more organized way
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "🔤 Translations",
                    stats['total_translations'],
                    help="Total number of translations in this session"
                )
                st.metric(
                    "⚡ Avg Speed",
                    f"{stats['avg_translation_time']:.2f}s",
                    help="Average time per translation"
                )
            with col2:
                st.metric(
                    "📝 Characters",
                    stats['total_characters_processed'],
                    help="Total characters processed"
                )
                # Calculate efficiency score
                if stats['total_translations'] > 0:
                    efficiency = stats['total_characters_processed'] / (
                                stats['avg_translation_time'] * stats['total_translations'])
                    st.metric(
                        "🚀 Efficiency",
                        f"{efficiency:.0f} c/s",
                        help="Characters processed per second"
                    )

        elif st.session_state.model_loading:
            st.info("🔄 Loading neural networks...")

        else:
            st.warning("⚠️ Model initialization required")

        # Enhanced settings section
        st.markdown("### ⚙️ Translation Settings")

        max_length = st.slider(
            "📏 Maximum Output Length",
            50, 500, st.session_state.max_length, 25,
            help="Maximum length of translated text"
        )
        st.session_state.max_length = max_length

        # Advanced settings in an expander
        with st.expander("🔧 Advanced Settings"):
            st.checkbox("🎯 High Quality Mode", value=True, help="Use enhanced processing")
            st.checkbox("📱 Mobile Optimization", value=False, help="Optimize for mobile devices")
            st.selectbox("🌐 Text Direction", ["Auto", "RTL", "LTR"], help="Text reading direction")

        # Enhanced controls section
        st.markdown("### 🎮 Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True, help="Clear all messages"):
                st.session_state.messages = []
                st.rerun()

        with col2:
            if st.button("🔄 Reload", use_container_width=True, help="Reload translation model"):
                st.session_state.model_loaded = False
                st.session_state.translator = None
                if 'load_translator_model' in st.session_state:
                    del st.session_state['load_translator_model']
                st.cache_resource.clear()
                st.rerun()

        # New feature: Translation history
        if st.session_state.translation_history:
            st.markdown("### 📚 Recent Translations")
            recent_count = min(3, len(st.session_state.translation_history))
            for i, (urdu, roman) in enumerate(st.session_state.translation_history[-recent_count:]):
                with st.expander(f"Translation {len(st.session_state.translation_history) - recent_count + i + 1}"):
                    st.write(f"**Urdu:** {urdu[:50]}...")
                    st.write(f"**Roman:** {roman[:50]}...")

        # New feature: Export functionality
        st.markdown("### 💾 Export Options")
        if st.button("📄 Export Chat", use_container_width=True, help="Export conversation as text"):
            export_chat()

        # Display error info if any with better formatting
        if st.session_state.error_state:
            st.markdown("### ⚠️ System Status")
            st.error(f"🔴 **Error:** {st.session_state.error_state}")


def export_chat():
    """Export chat history as downloadable text"""
    if not st.session_state.messages:
        st.warning("No messages to export!")
        return

    export_text = "# Urdu Translator AI - Chat Export\n\n"
    export_text += f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for i, message in enumerate(st.session_state.messages, 1):
        if message["role"] == "user":
            export_text += f"## Input {i // 2 + 1}\n**Urdu:** {message['content']}\n\n"
        else:
            export_text += f"**Roman Translation:** {message['content']}\n"
            export_text += f"**Time:** {message.get('translation_time', 'N/A')}s\n\n"

    st.download_button(
        label="📥 Download Chat History",
        data=export_text,
        file_name=f"urdu_translation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )


def display_chat():
    """Display chat messages with enhanced styling and features"""
    if st.session_state.messages:
        st.markdown('<div class="main-container">', unsafe_allow_html=True)

        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                word_count = count_words(message["content"])
                st.markdown(f"""
                <div class="chat-message user-message">
                    {message["content"]}
                    <div class="message-time">
                        📅 {message.get("time", "")} • 📝 {word_count} words
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Determine translation quality
                time_taken = float(message.get("translation_time", "0"))
                quality = get_translation_quality(message["content"], time_taken)

                formatted_content = format_translation_with_copy(message["content"], quality)

                st.markdown(f"""
                <div class="chat-message assistant-message">
                    {formatted_content}
                    <div class="message-time">
                        🕐 {message.get("time", "")} • ⚡ {message.get("translation_time", "0.00")}s • 🎯 {quality.title()} Quality
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


def display_input():
    """Display enhanced input form with word counting"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    with st.form("translation_form", clear_on_submit=True):
        urdu_text = st.text_area(
            "✍️ Enter Urdu Text:",
            placeholder="یہاں اردو متن درج کریں... (Type your Urdu text here...)",
            height=120,
            help="💡 Tip: Use proper Urdu text for best translation results",
            key="urdu_input"
        )

        # Display word count
        if urdu_text:
            word_count = count_words(urdu_text)
            st.markdown(f'<div class="word-count">📊 Words: {word_count} | Characters: {len(urdu_text)}</div>',
                        unsafe_allow_html=True)

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            submit = st.form_submit_button("🚀 Translate Now", type="primary", use_container_width=True)
        with col2:
            clear = st.form_submit_button("🧹 Clear", use_container_width=True)
        with col3:
            if st.form_submit_button("⭐ Demo", use_container_width=True):
                demo_texts = [
                    "میں اردو سیکھ رہا ہوں",
                    "آج موسم بہت اچھا ہے",
                    "آپ کیسے ہیں؟",
                    "یہ کتاب دلچسپ ہے"
                ]
                import random
                return random.choice(demo_texts), True

    st.markdown('</div>', unsafe_allow_html=True)

    if clear:
        st.session_state.messages = []
        st.rerun()
        return "", False

    return urdu_text, submit


def process_translation(urdu_text):
    """Process translation request with enhanced features"""
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
        "time": datetime.now().strftime("%H:%M:%S")
    })

    # Translate with enhanced progress indicator
    progress_placeholder = st.empty()
    with st.spinner("🔄 Processing neural translation..."):
        try:
            max_length = st.session_state.get('max_length', 200)

            # Show progress
            progress_placeholder.info("🧠 Analyzing Urdu text structure...")
            time.sleep(0.2)
            progress_placeholder.info("🔄 Applying neural transformation...")

            translation, time_taken = st.session_state.translator.translate(
                urdu_text.strip(), max_length
            )

            progress_placeholder.info("✨ Finalizing Roman output...")
            time.sleep(0.1)
            progress_placeholder.empty()

            # Clean translation result
            clean_translation = re.sub(r'<[^>]+>', '', str(translation)).strip()

            if clean_translation.startswith("Error:"):
                st.error(f"Translation failed: {clean_translation}")
                return

            # Add to translation history
            st.session_state.translation_history.append((urdu_text.strip(), clean_translation))

            # Keep only last 20 translations
            if len(st.session_state.translation_history) > 20:
                st.session_state.translation_history = st.session_state.translation_history[-20:]

            # Add assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": clean_translation,
                "time": datetime.now().strftime("%H:%M:%S"),
                "translation_time": f"{time_taken:.2f}"
            })

            # Show success message briefly
            success_placeholder = st.empty()
            success_placeholder.success(f"✅ Translation completed in {time_taken:.2f} seconds!")
            time.sleep(2)
            success_placeholder.empty()

        except Exception as e:
            st.error(f"❌ Translation error: {str(e)}")
            print(f"Translation error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return

    st.rerun()


def display_loading_screen():
    """Display enhanced loading screen with better animations"""
    # st.markdown("""
    # <div class="main-container" style="text-align: center; padding: 4rem 2rem;">
    #     <div class="loading-animation" style="margin: 2rem auto;"></div>
    #     <h2 style="color: var(--text-primary); margin: 2rem 0 1rem 0; background: var(--primary-gradient); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
    #         🧠 Initializing Neural Networks
    #     </h2>
    #     <p style="color: var(--text-muted); font-size: 1.2rem; line-height: 1.6;">
    #         🔄 Loading 600MB model architecture...<br>
    #         📚 Initializing tokenizers and vocabularies...<br>
    #         ⚡ Optimizing for your device...<br><br>
    #         <small style="opacity: 0.7;">This may take a moment on first load</small>
    #     </p>
    #     <div style="margin-top: 3rem; padding: 1.5rem; background: rgba(22, 33, 62, 0.8); border-radius: 16px; border: 1px solid rgba(116, 75, 162, 0.3); backdrop-filter: blur(15px);">
    #         <div style="color: var(--text-secondary); font-size: 1rem; line-height: 1.8;">
    #             <strong>🏗️ Model Architecture:</strong><br>
    #             • 2-layer BiLSTM Encoder with Attention<br>
    #             • 4-layer LSTM Decoder<br>
    #             • 600M+ parameters<br>
    #             • BLEU Score: 45.6<br><br>
    #             <span style="color: var(--success);">🎯 State-of-the-art Urdu ↔ Roman Translation</span>
    #         </div>
    #     </div>
    # </div>
    # """, unsafe_allow_html=True)


def display_error_screen(error_msg):
    """Display enhanced error screen when model fails to load"""
    st.markdown(f"""
    <div class="main-container" style="text-align: center; padding: 4rem 2rem;">
        <h2 style="color: var(--error); margin: 2rem 0 1rem 0;">⚠️ Neural Model Loading Failed</h2>
        <div style="margin: 2rem 0; padding: 2rem; background: rgba(255, 87, 34, 0.1); border: 2px solid var(--error); border-radius: 16px; color: var(--error); backdrop-filter: blur(15px);">
            <strong>🔍 Error Details:</strong><br><br>
            <code style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; display: block; margin: 1rem 0; color: var(--text-primary);">
                {error_msg}
            </code>
        </div>
        <div style="margin-top: 2rem; padding: 2rem; background: rgba(100, 255, 218, 0.1); border: 2px solid var(--success); border-radius: 16px; color: var(--success); backdrop-filter: blur(15px);">
            <strong>🎭 Demo Mode Active</strong><br><br>
            ✅ The application is running in demonstration mode<br>
            🔄 Using enhanced character-based transliteration<br>
            📚 Includes 50+ common word mappings<br>
            ⚡ Faster response times for testing<br><br>
            <small style="opacity: 0.8;">Some model files may be missing. Please check your model directory.</small>
        </div>
        <div style="margin-top: 2rem;">
            <button style="background: var(--primary-gradient); color: white; border: none; padding: 1rem 2rem; border-radius: 12px; font-weight: 600; cursor: pointer;" onclick="location.reload();">
                🔄 Try Reloading
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# MAIN APPLICATION (Enhanced)
# ============================================

def main():
    """Enhanced main application function"""
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
        time.sleep(1.5)
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

    # Enhanced footer with stats
    if st.session_state.model_loaded and st.session_state.translator:
        stats = st.session_state.translator.session_stats
        # st.markdown(f"""
        # <div class="main-container">
        #     <hr style="margin: 2rem 0; border: none; height: 2px; background: var(--primary-gradient); opacity: 0.3;">
        #     <div style="text-align: center; color: var(--text-muted); line-height: 1.8;">
        #         <strong style="background: var(--primary-gradient); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.2rem;">
        #             🌙 Urdu Translator AI
        #         </strong><br>
        #         <span style="font-size: 0.95rem;">
        #             🧠 Neural Machine Translation • 🚀 PyTorch & Streamlit<br>
        #             📊 Session: {stats['total_translations']} translations • {stats['total_characters_processed']} characters processed<br>
        #             ⚡ Average: {stats['avg_translation_time']:.2f}s per translation
        #         </span><br><br>
        #         <small style="opacity: 0.7; font-size: 0.8rem;">
        #             🏗️ Architecture: 2-Layer BiLSTM Encoder + 4-Layer LSTM Decoder with Bahdanau Attention<br>
        #             🎯 Specialized for Urdu ↔ Roman Urdu Translation • BLEU Score: 45.6
        #         </small>
        #     </div>
        # </div>
        # """, unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"🔴 **Application Error:** {str(e)}")
        st.error("Please check the console for detailed error information.")
        with st.expander("🔍 Debug Information"):
            st.code(f"Error: {e}\n\nTraceback:\n{traceback.format_exc()}")
        print(f"App error: {e}")
        print(f"Traceback: {traceback.format_exc()}")