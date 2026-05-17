"""
- google-generativeai  (Gemini 1.5 Flash multimodal — free tier)
- Pillow               (image pre-processing)
- streamlit            (UI)
"""

import io
import textwrap
import base64
import os
from pathlib import Path

import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
os.environ["GEMINI_API_KEY"] = "GEMINI_API_KEY" 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# CONFIG
GEMINI_MODEL   = "gemini-2.5-flash"
MAX_IMAGE_SIZE = (1024, 1024)   # resize before sending to API because of token limmits high resolution images can easily exceed Gemini's token limits

─
st.set_page_config(
    page_title="VisionMind — Image QA",
    page_icon="🔍",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1 { font-weight: 700; letter-spacing: -0.5px; }

.stButton>button {
    background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
    color: #d1fae5;
    border: 1px solid #10b981;
    border-radius: 8px;
    padding: 0.5rem 1.4rem;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #047857 0%, #059669 100%);
    border-color: #34d399;
    color: #fff;
}

.result-box {
    background: linear-gradient(135deg, #022c22 0%, #064e3b 100%);
    border-left: 4px solid #10b981;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    color: #d1fae5;
    font-size: 0.95rem;
    line-height: 1.8;
    margin-top: 0.8rem;
}
.ocr-box {
    background: #1c1c1c;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    color: #f9fafb;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.7;
    white-space: pre-wrap;
    margin-top: 0.5rem;
}
.task-badge {
    display: inline-block;
    background: #065f46;
    color: #6ee7b7;
    border: 1px solid #059669;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 2px;
    cursor: pointer;
}
.sidebar-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #34d399;
    margin-bottom: 0.4rem;
}
.info-pill {
    background: #1e3a2e;
    border: 1px solid #065f46;
    border-radius: 6px;
    padding: 0.4rem 0.8rem;
    color: #6ee7b7;
    font-size: 0.78rem;
    margin-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)

# SESSION STATE 
for k, v in {
    "pil_image": None,
    "image_bytes": None,
    "history": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# HELPERS

def preprocess_image(img: Image.Image, enhance_for_ocr: bool = False) -> Image.Image:
    """Resize and optionally sharpen image for better OCR results."""
    img = img.convert("RGB")
    img.thumbnail(MAX_IMAGE_SIZE, Image.LANCZOS)
    if enhance_for_ocr:
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
    return img


def image_to_bytes(img: Image.Image, quality: int = 85) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def build_image_part(img_bytes: bytes) -> dict:
    return {"mime_type": "image/jpeg", "data": img_bytes}


def run_gemini_vision(api_key: str, prompt: str, img_bytes: bytes) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content([
        build_image_part(img_bytes),
        prompt
    ])
    return response.text


# Preset task prompts
TASK_PROMPTS = {
    "📝 Full Description": textwrap.dedent("""
        Describe this image in detail. Include:
        - Overall scene / subject
        - Key objects, people, or elements and their positions
        - Colors, textures, lighting, mood
        - Any text visible in the image
        - Context or setting
        Be thorough but organized.
    """).strip(),

    "🔍 OCR — Extract All Text": textwrap.dedent("""
        Extract EVERY piece of text visible in this image.
        Return the text exactly as it appears, preserving:
        - Line breaks
        - Bullet points or numbering
        - Table structure (use | as column separator)
        - Headings vs body text (mark headings with ##)
        If no text is found, say "No readable text detected."
        Do not add any commentary — output only the extracted text.
    """).strip(),

    "📊 Table / Data Extraction": textwrap.dedent("""
        If this image contains a table or structured data, extract it.
        Format output as a markdown table with | separators.
        If there is no table, extract any key-value pairs or lists present.
        Be precise — do not invent data.
    """).strip(),

    "🏷️ Object & Label Detection": textwrap.dedent("""
        List all distinct objects, items, or elements visible in this image.
        For each object, note:
        - Name
        - Approximate location (top-left, center, etc.)
        - Estimated count if multiple
        Format as a clean bullet list.
    """).strip(),

    "🌐 Language Detection & Translation": textwrap.dedent("""
        Identify any text in this image.
        For each block of text:
        1. State the detected language
        2. Provide an English translation if not already in English
        3. Show original text → translation side by side
        If no text is present, say so.
    """).strip(),

    "🧾 Document / Receipt Analysis": textwrap.dedent("""
        Analyze this image as a document, receipt, invoice, or form.
        Extract:
        - Document type
        - Key fields (dates, names, amounts, addresses, IDs)
        - Line items if present
        - Totals or summaries
        Present the data in a structured format.
    """).strip(),
}

# SIDEBAR
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ Configuration</div>', unsafe_allow_html=True)
    if GEMINI_API_KEY:
        st.markdown('<div class="info-pill">✅ API Key loaded from .env</div>', unsafe_allow_html=True)
    else:
        st.error("⚠️ GEMINI_API_KEY not found in .env file")

    st.markdown("---")
    st.markdown('<div class="sidebar-title">🖼️ Upload Image</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Supported: JPG · PNG · WEBP · BMP · TIFF",
        type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
        label_visibility="collapsed"
    )

    enhance_ocr = st.checkbox("Enhance image for OCR",
                               value=False,
                               help="Boosts contrast & sharpness — helps with faded or low-quality text.")

    if uploaded_file:
        pil_img = Image.open(uploaded_file)
        processed = preprocess_image(pil_img, enhance_for_ocr=enhance_ocr)
        img_bytes  = image_to_bytes(processed)
        st.session_state.pil_image    = processed
        st.session_state.image_bytes  = img_bytes
        st.image(processed, caption=f"{uploaded_file.name} · {processed.size[0]}×{processed.size[1]}px",
                 use_container_width=True)

        st.markdown(f"""
        <div class="info-pill">Mode: {pil_img.mode}</div>
        <div class="info-pill">Original: {pil_img.size[0]}×{pil_img.size[1]}px</div>
        <div class="info-pill">Processed: {processed.size[0]}×{processed.size[1]}px</div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    st.markdown("""
    ---
    **VisionMind** · Phase 2  
    *Free stack: Gemini 1.5 Flash Vision*
    """)

# MAIN
st.markdown("## 🔍 VisionMind — Image Understanding & QA")
st.markdown("Upload an image, pick a task or ask a custom question — powered by Gemini Vision.")

if st.session_state.pil_image is None:
    st.info("⬆️ Upload an image from the sidebar to begin.")
    st.stop()

st.markdown("---")

# ── Preset task buttons
st.markdown("### ⚡ Quick Tasks")
cols = st.columns(3)
task_names = list(TASK_PROMPTS.keys())
selected_task = None

for i, task_name in enumerate(task_names):
    if cols[i % 3].button(task_name, key=f"task_{i}", use_container_width=True):
        selected_task = task_name

st.markdown("---")

# ── Custom question
st.markdown("### 💬 Custom Question")
col_q, col_btn = st.columns([5, 1])
with col_q:
    custom_q = st.text_input("Ask anything about the image",
                              placeholder="e.g. How many people are in this image? / What currency is on the receipt?",
                              label_visibility="collapsed")
with col_btn:
    ask_custom = st.button("Ask →", type="primary", use_container_width=True)

# ── Trigger inference
query_prompt = None
query_label  = None

if selected_task:
    query_prompt = TASK_PROMPTS[selected_task]
    query_label  = selected_task

if ask_custom and custom_q.strip():
    query_prompt = f"""
You are a precise image analysis assistant.
Answer the following question about the image.
Base your answer ONLY on what is visible in the image.
If you cannot determine the answer from the image, say so clearly.

QUESTION: {custom_q.strip()}
""".strip()
    query_label = f"❓ {custom_q.strip()}"

if query_prompt:
    if not GEMINI_API_KEY:
        st.error("⚠️ GEMINI_API_KEY not found. Please add it to your .env file.")
    else:
        with st.spinner("Analyzing image…"):
            result = run_gemini_vision(GEMINI_API_KEY, query_prompt, st.session_state.image_bytes)

        st.session_state.history.append({
            "label":  query_label,
            "result": result,
            "is_ocr": "OCR" in query_label or "Extract" in query_label,
        })

# Display history
for turn in reversed(st.session_state.history):
    st.markdown(f"**{turn['label']}**")
    if turn["is_ocr"]:
        st.markdown(f'<div class="ocr-box">{turn["result"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="result-box">{turn["result"]}</div>', unsafe_allow_html=True)
    st.markdown("---")