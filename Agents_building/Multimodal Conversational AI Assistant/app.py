import streamlit as st
import os
import hashlib
from dotenv import load_dotenv
from router import route_input
from audio_handler import transcribe_audio
from image_handler import analyze_image

load_dotenv()

st.set_page_config(
    page_title="MultiModal AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
}

.stApp { background-color: #0f0f0f; color: #e8e8e8; }

header[data-testid="stHeader"],
footer, #MainMenu,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #141414 !important;
    border-right: 1px solid #222 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1rem 0.85rem 1.5rem !important;
}

.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.4rem 0.25rem 1.2rem;
    border-bottom: 1px solid #222;
    margin-bottom: 0.75rem;
}
.sidebar-logo-icon {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, #00c896, #007a5a);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 700; color: #fff;
    flex-shrink: 0;
}
.sidebar-logo-name {
    font-size: 15px;
    font-weight: 600;
    color: #e8e8e8;
    letter-spacing: -0.01em;
}
.sidebar-label {
    font-size: 10.5px;
    font-weight: 600;
    color: #444;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    padding: 1rem 0.25rem 0.4rem;
}
.pipeline-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #444;
    padding: 5px 0.25rem;
}
.pipeline-row span { color: #555; }

/* ── Buttons ── */
.stButton > button {
    background: #1a1a1a !important;
    color: #c8c8c8 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.15s !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: #222 !important;
    border-color: #333 !important;
    color: #e8e8e8 !important;
}
.send-btn > div > button {
    background: #00c896 !important;
    border-color: #00c896 !important;
    color: #0a1f18 !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    font-size: 13.5px !important;
}
.send-btn > div > button:hover {
    background: #00b085 !important;
    border-color: #00b085 !important;
}

/* ── Radio ── */
.stRadio > div { gap: 2px !important; }
.stRadio > label { display: none !important; }
.stRadio label {
    background: transparent !important;
    border-radius: 7px !important;
    padding: 8px 10px !important;
    color: #555 !important;
    font-size: 13.5px !important;
    cursor: pointer;
    transition: all 0.15s;
    width: 100%;
}
.stRadio label:hover { background: #1e1e1e !important; color: #999 !important; }
.stRadio [data-baseweb="radio"] { accent-color: #00c896; }
div[role="radiogroup"] > label[data-selected="true"] {
    background: #0d2420 !important;
    color: #00c896 !important;
}

hr { border-color: #1e1e1e !important; margin: 0.5rem 0 !important; }

/* ── Welcome ── */
.welcome-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 5rem 1rem 2.5rem;
    text-align: center;
}
.welcome-orb {
    width: 64px; height: 64px;
    background: radial-gradient(circle at 35% 35%, #00e8a8, #007a5a);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; color: #fff; font-weight: 700;
    margin: 0 auto 1.5rem;
    box-shadow: 0 0 40px rgba(0,200,150,0.2), 0 0 80px rgba(0,200,150,0.07);
}
.welcome-title {
    font-size: 2rem; font-weight: 600;
    color: #e8e8e8; margin-bottom: 0.6rem;
    letter-spacing: -0.03em;
}
.welcome-sub {
    font-size: 14px; color: #555;
    max-width: 360px; line-height: 1.7;
}
.chips-row {
    display: flex; gap: 10px;
    flex-wrap: wrap; justify-content: center;
    margin-top: 2.5rem; max-width: 640px;
}
.chip {
    background: #161616;
    border: 1px solid #252525;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 13px; color: #777;
    cursor: pointer;
    max-width: 185px; text-align: left; line-height: 1.5;
    transition: all 0.15s;
}
.chip:hover { background: #1e1e1e; border-color: #333; color: #ccc; }

/* ── Chat messages ── */
.msg-wrap {
    max-width: 760px;
    margin: 0 auto;
    padding: 1rem 1rem 0.5rem;
}
.msg-block {
    display: flex;
    align-items: flex-start;
    gap: 13px;
    padding: 16px 0;
    border-bottom: 1px solid #161616;
    animation: fadeSlide 0.25s ease;
}
.msg-block:last-child { border-bottom: none; }
.msg-block.user-block { flex-direction: row-reverse; }

@keyframes fadeSlide {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.avatar {
    width: 32px; height: 32px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; flex-shrink: 0; font-weight: 600;
}
.av-ai  { background: linear-gradient(135deg, #00c896, #007a5a); color: #fff; font-size: 15px; }
.av-user { background: #1a1a30; color: #7070b0; font-size: 11px; border: 1px solid #252540; }

.msg-content { flex: 1; font-size: 14.5px; line-height: 1.78; }

.user-content {
    background: #141420;
    border: 1px solid #20203a;
    border-radius: 14px 3px 14px 14px;
    padding: 10px 15px;
    color: #b8b8d8;
    max-width: 72%;
    margin-left: auto;
    font-size: 14px;
}
.ai-content { color: #ccc; padding: 2px 0; }

.voice-label {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 10.5px;
    color: #00c896;
    font-family: 'DM Mono', monospace;
    background: #0a2a20;
    border: 1px solid #00c89630;
    border-radius: 20px;
    padding: 2px 8px;
    margin-bottom: 5px;
}

/* ── Text input ── */
.stTextInput > div > div > input {
    background: #181818 !important;
    border: 1px solid #272727 !important;
    border-radius: 12px !important;
    color: #e8e8e8 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14.5px !important;
    padding: 0.75rem 1.1rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00c896 !important;
    box-shadow: 0 0 0 3px rgba(0,200,150,0.1) !important;
}
.stTextInput label { display: none !important; }
.stTextInput > div > div > input::placeholder { color: #3a3a3a !important; }

/* ── Voice panel ── */
.voice-panel {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 18px;
    padding: 2rem 1.5rem;
    max-width: 480px;
    margin: 0 auto 1.5rem;
    text-align: center;
}
.voice-panel-title {
    font-size: 16px; font-weight: 600;
    color: #ddd; margin-bottom: 0.4rem;
}
.voice-panel-sub {
    font-size: 13px; color: #444;
    margin-bottom: 1.5rem; line-height: 1.65;
}
.voice-steps {
    display: flex; justify-content: center;
    gap: 28px; margin-bottom: 1.5rem; flex-wrap: wrap;
}
.voice-step {
    display: flex; flex-direction: column;
    align-items: center; gap: 6px;
    font-size: 12px; color: #444;
}
.voice-step-num {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: #0d2420;
    border: 1px solid #00c89640;
    color: #00c896;
    font-size: 12px; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
}

[data-testid="stAudioInput"] { background: transparent !important; border: none !important; }
[data-testid="stAudioInput"] label { display: none !important; }

/* ── Image uploader ── */
[data-testid="stFileUploader"] {
    background: #111;
    border: 1.5px dashed #252525;
    border-radius: 12px;
    padding: 0.75rem 1rem;
}

/* ── Mode badge ── */
.mode-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #141414; border: 1px solid #222;
    border-radius: 20px; padding: 4px 12px;
    font-size: 11px; color: #444; margin-bottom: 1rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.03em;
}

[data-testid="stSpinner"] svg { stroke: #00c896 !important; }

[data-testid="stAlert"] {
    background: #1a1010 !important; border: 1px solid #3a1515 !important;
    border-radius: 10px !important; color: #c88 !important; font-size: 13px !important;
}

.disclaimer {
    text-align: center; font-size: 11px; color: #2a2a2a;
    padding: 0.5rem 0 1rem; font-family: 'DM Mono', monospace;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #252525; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages"        not in st.session_state: st.session_state.messages        = []
if "input_mode"      not in st.session_state: st.session_state.input_mode      = "text"
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">✦</div>
        <div class="sidebar-logo-name">MultiModal AI</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("＋  New Chat", use_container_width=True):
        st.session_state.messages        = []
        st.session_state.input_mode      = "text"
        st.session_state.last_audio_hash = None
        st.rerun()

    st.markdown('<div class="sidebar-label">Input Mode</div>', unsafe_allow_html=True)
    mode_map = {
        "💬  Text":   "text",
        "🎙️  Voice":  "voice",
        "🖼️  Image":  "image",
    }
    selected = st.radio(
        "mode", list(mode_map.keys()),
        index=list(mode_map.values()).index(st.session_state.input_mode),
        label_visibility="collapsed",
    )
    st.session_state.input_mode = mode_map[selected]

    st.markdown("---")
    st.markdown('<div class="sidebar-label">Pipeline</div>', unsafe_allow_html=True)
    for icon, label in [
        ("🎙️", "Voice → Groq Whisper"),
        ("🖼️", "Image → Qwen VL"),
        ("💬", "Text → Direct"),
        ("⚡", "All → LLaMA‑3"),
    ]:
        st.markdown(
            f'<div class="pipeline-row">{icon} <span>{label}</span></div>',
            unsafe_allow_html=True,
        )

# ── Mode ──────────────────────────────────────────────────────────────────────
mode = st.session_state.input_mode

# ── Chat history ──────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-wrap">
        <div class="welcome-orb">✦</div>
        <div class="welcome-title">How can I help?</div>
        <div class="welcome-sub">Type a message, record your voice, or upload an image.</div>
        <div class="chips-row">
            <div class="chip">💡 Explain a concept simply</div>
            <div class="chip">🖼️ Analyze an image for me</div>
            <div class="chip">🎙️ Ask me with your voice</div>
            <div class="chip">✍️ Help me write something</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown('<div class="msg-wrap">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="msg-block user-block">
                <div class="avatar av-user">You</div>
                <div class="msg-content user-content">{msg["content"]}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-block">
                <div class="avatar av-ai">✦</div>
                <div class="msg-content ai-content">{msg["content"]}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ── TEXT MODE ─────────────────────────────────────────────────────────────────
if mode == "text":
    st.markdown('<div class="mode-badge">⬜ text mode</div>', unsafe_allow_html=True)
    col_in, col_btn = st.columns([7, 1])
    with col_in:
        user_text = st.text_input(
            "msg", placeholder="Message MultiModal AI…",
            label_visibility="collapsed", key="text_msg",
        )
    with col_btn:
        st.markdown('<div class="send-btn">', unsafe_allow_html=True)
        send = st.button("Send ↑", use_container_width=True, key="send_text")
        st.markdown("</div>", unsafe_allow_html=True)

    if send and user_text.strip():
        st.session_state.messages.append({"role": "user", "content": user_text.strip()})
        with st.spinner("Thinking…"):
            reply = route_input(user_text.strip(), input_type="text")
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ── VOICE MODE ────────────────────────────────────────────────────────────────
elif mode == "voice":
    st.markdown('<div class="mode-badge">🎙 voice mode</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="voice-panel">
        <div class="voice-panel-title">🎙️ Voice Input</div>
        <div class="voice-panel-sub">Speak your question — it will be transcribed and answered instantly.</div>
        <div class="voice-steps">
            <div class="voice-step"><div class="voice-step-num">1</div>Click mic</div>
            <div class="voice-step"><div class="voice-step-num">2</div>Speak</div>
            <div class="voice-step"><div class="voice-step-num">3</div>Stop &amp; wait</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    audio_value = st.audio_input(" ", key="mic_recorder", label_visibility="collapsed")

    if audio_value is not None:
        # MD5 hash the raw bytes — only process if it's a brand-new recording
        raw = audio_value.read()
        audio_value.seek(0)   # reset so transcribe_audio can read it
        audio_hash = hashlib.md5(raw).hexdigest()

        if st.session_state.last_audio_hash != audio_hash:
            st.session_state.last_audio_hash = audio_hash   # lock before rerun

            with st.spinner("Transcribing your voice…"):
                transcript = transcribe_audio(audio_value)

            if transcript:
                st.session_state.messages.append({
                    "role": "user",
                    "content": (
                        '<span class="voice-label">🎙 voice</span><br>'
                        f"{transcript}"
                    ),
                })
                with st.spinner("Thinking…"):
                    reply = route_input(transcript, input_type="voice")
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
            else:
                st.error("Transcription failed — please check your GROQ_API_KEY in .env")

# ── IMAGE MODE ────────────────────────────────────────────────────────────────
elif mode == "image":
    st.markdown('<div class="mode-badge">🖼 image mode</div>', unsafe_allow_html=True)
    img_file = st.file_uploader(
        "Upload image (jpg / png / webp)",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="visible", key="img_upload",
    )
    if img_file:
        col_img, col_right = st.columns([2, 4])
        with col_img:
            st.image(img_file, use_container_width=True)
        with col_right:
            img_prompt = st.text_input(
                "prompt", placeholder="Ask something about this image…",
                label_visibility="collapsed", key="img_prompt",
            )
            st.markdown('<div class="send-btn">', unsafe_allow_html=True)
            if st.button("🖼️ Analyze & Send", use_container_width=True):
                prompt = img_prompt.strip() or "Describe this image in detail."
                with st.spinner("Analyzing with Qwen VL…"):
                    vision_desc = analyze_image(img_file, prompt)
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"🖼️ <em>{prompt}</em>",
                })
                with st.spinner("Thinking…"):
                    reply = route_input(f"[Image analysis]: {vision_desc}", input_type="image")
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ── Disclaimer ────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="disclaimer">✦ MultiModal AI · Groq LLaMA‑3 · Whisper · Qwen VL</div>',
    unsafe_allow_html=True,
)