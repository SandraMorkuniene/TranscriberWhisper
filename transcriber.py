from io import BytesIO
import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import numpy as np
import tempfile
import os
from pydub import AudioSegment
from openai import OpenAI
from docx import Document
import time

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []
        self.start_time = time.time()
        self.chunk_duration = 10  # seconds
        self.last_processed = time.time()

    def recv(self, frame: av.AudioFrame):
        audio = frame.to_ndarray()
        self.frames.append(audio)

        now = time.time()

        if now - self.last_processed >= self.chunk_duration:
            self.process_chunk()
            self.last_processed = now

        return frame

    def process_chunk(self):
        if len(self.frames) == 0:
            return

        audio_data = np.concatenate(self.frames, axis=0)
        self.frames = []

        # Save temp WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            sound = AudioSegment(
                audio_data.tobytes(),
                frame_rate=48000,
                sample_width=2,
                channels=1
            )
            sound = sound.set_frame_rate(16000).set_channels(1)
            sound.export(tmp.name, format="wav")

            transcript = transcribe_audio(tmp.name)

            st.session_state["live_transcript"] += transcript + " "


client = OpenAI()

def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="lt"
        )
    return response.text

st.title("Lithuanian AI Interview Recorder")

if "live_transcript" not in st.session_state:
    st.session_state["live_transcript"] = ""

webrtc_ctx = webrtc_streamer(
    key="example",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

st.subheader("Live Transcript")
st.write(st.session_state["live_transcript"])

if webrtc_ctx.state.playing:
    elapsed = int(time.time() - webrtc_ctx.audio_processor.start_time)
    st.write(f"Recording time: {elapsed} seconds")

if st.button("Finalize Transcript"):

    raw_text = st.session_state["live_transcript"]

    prompt = f"""
    Clean this Lithuanian interview transcript.
    Fix grammar mistakes.
    Separate speakers as:

    INTERVIUOTOJAS:
    INTERVIUOJAMAS:

    Extract:
    1. Short summary
    2. 5 strongest quotes

    Transcript:
    {raw_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    final_text = response.choices[0].message.content
    st.session_state["final_text"] = final_text

def generate_doc(text):
    doc = Document()
    doc.add_paragraph(text)
    file_path = "interview.docx"
    doc.save(file_path)
    return file_path

if "final_text" in st.session_state:
    file_path = generate_doc(st.session_state["final_text"])

    with open(file_path, "rb") as f:
        st.download_button(
            "Download Word File",
            f,
            file_name="interview.docx"
        )



