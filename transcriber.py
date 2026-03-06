import streamlit as st
from streamlit_mic_recorder import mic_recorder
from openai import OpenAI
from docx import Document
from io import BytesIO
import tempfile
from pydub import AudioSegment

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("Lithuanian AI Interview Recorder")

if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""

audio = mic_recorder(
    start_prompt="🎙 Start recording",
    stop_prompt="⏹ Stop recording",
    just_once=False
)


with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
    tmp.write(audio["bytes"])
    webm_path = tmp.name



with open(wav_path, "rb") as f:
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=f
        )

    st.session_state["transcript"] += transcript.text + " "

st.subheader("Transcript")
st.write(st.session_state["transcript"])

if st.button("Finalize Transcript"):

    prompt = f"""
    Clean this Lithuanian interview transcript.

    Fix grammar.
    Separate speakers as:

    INTERVIUOTOJAS:
    INTERVIUOJAMAS:

    Extract:
    1. Short summary
    2. 5 strongest quotes

    Transcript:
    {st.session_state["transcript"]}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    final_text = response.choices[0].message.content

    st.session_state["final_text"] = final_text

if "final_text" in st.session_state:

    st.subheader("Final Interview")
    st.write(st.session_state["final_text"])

    doc = Document()
    doc.add_paragraph(st.session_state["final_text"])

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    st.download_button(
        "Download Word file",
        buffer,
        file_name="interview.docx"
    )




