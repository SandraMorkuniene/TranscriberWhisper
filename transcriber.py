import streamlit as st
import openai
from pydub import AudioSegment
from io import BytesIO
from docx import Document
import math
import tempfile

st.title("Transkribuotojas (.m4a, .mp3, .wav)")

audio_file = st.file_uploader(
    "Įkelkite garso įrašą",
    type=["mp3","wav","m4a"]
)

if audio_file is not None:
    st.info("Konvertuojama ir segmentuojama į 5 min. dalis...")

    # Sukuriame laikina faila, kad pydub galėtų pasiekti
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.name.split('.')[-1]}") as tmp:
        tmp.write(audio_file.read())
        tmp_path = tmp.name

    # Atidarome per pydub
    ext = tmp_path.split(".")[-1]
    audio = AudioSegment.from_file(tmp_path, format=ext)

    # Konvertuojame į mp3
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
        audio.export(tmp_mp3.name, format="mp3")
        audio = AudioSegment.from_file(tmp_mp3.name, format="mp3")

    segment_length_ms = 5 * 60 * 1000  # 5 min
    num_segments = math.ceil(len(audio) / segment_length_ms)

    doc = Document()
    doc.add_heading("Transkribuotas tekstas", level=1)

    progress_text = st.empty()
    progress_bar = st.progress(0)

    for i in range(num_segments):
        start_ms = i * segment_length_ms
        end_ms = min((i+1)*segment_length_ms, len(audio))
        chunk = audio[start_ms:end_ms]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as chunk_file:
            chunk.export(chunk_file.name, format="mp3")
            # Transkribuojame per OpenAI API
            with open(chunk_file.name, "rb") as f:
                transcript = openai.Audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
            text = transcript["text"]

        doc.add_heading(f"Segmentas {i+1}", level=2)
        doc.add_paragraph(text)

        progress_text.text(f"Transkribuojama segmentas {i+1}/{num_segments}...")
        progress_bar.progress((i+1)/num_segments)

    st.success("Transkripcija baigta!")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    st.download_button(
        label="Parsisiųsti Word dokumentą",
        data=buffer,
        file_name="transkripcija.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
