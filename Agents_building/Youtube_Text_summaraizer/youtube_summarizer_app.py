import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from groq import Groq
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi

client = Groq(api_key=os.getenv("GROQ_API_KEY")) 

prompt = """
You are a YouTube video summarizer.

Summarize the transcript into clear bullet points.

- Keep it under 250 words
- Highlight key insights
- Make it easy to understand

Transcript:
"""

def get_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if match:
        return match.group(1)
    return None

def extract_transcript_details(youtube_video_url):
    try:
        video_id = get_video_id(youtube_video_url)
        if not video_id:
            return None

        ytt_api = YouTubeTranscriptApi()
        transcript_data = ytt_api.fetch(video_id)

        transcript = " ".join([t["text"] for t in transcript_data.to_raw_data()]) 
        return transcript

    except Exception as e:
        st.error(f"Transcript error: {e}")
        return None

def generate_gemini_content(transcript_text, prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt + transcript_text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Groq error: {e}")
        return None

st.set_page_config(page_title="YouTube Summarizer", page_icon="🎥")
st.title("Youtube Video Summarizer")
youtube_video_url = st.text_input("Enter the Youtube Video URL")

if youtube_video_url:
    video_id = get_video_id(youtube_video_url)
    if video_id:
        st.image(f"https://img.youtube.com/vi/{video_id}/0.jpg")

if st.button('Get Detailed Notes'):
    if not youtube_video_url:
        st.warning("Please enter a YouTube URL")
    else:
        with st.spinner("⏳ Fetching transcript and generating summary..."):
            transcript_text = extract_transcript_details(youtube_video_url)

            if not transcript_text:
                st.error("No transcript found for this video.")
            else:
                summary = generate_gemini_content(transcript_text, prompt)
                if summary:
                    st.subheader("Summary of the Video")
                    st.write(summary)