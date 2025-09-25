import streamlit as st
import openai
from pydub import AudioSegment
from io import BytesIO
from docx import Document
import math

st.title("Lietuvių kalbos transkribuotojas su Word parsisiuntimu (.m4a palaikymas)")

# Įkelti garso įrašą
audio_file = st.file_uploader(
    "Įkelkite garso įrašą (.mp3, .wav, .m4a)", 
    type=["mp3","wav","m4a"]
)

if audio_file is not None:
    # Išsaugome laikinu failu
    uploaded_filename = audio_file.name
    with open(uploaded_filename, "wb") as f:
        f.write(audio_file.read())

    st.info("Konvertuojama ir segmentuojama į 5 min. dalis...")

    # Nustatom formatą pagal failo plėtinį
    ext = uploaded_filename.split(".")[-1]
    audio = AudioSegment.from_file(uploaded_filename, format=ext)

    # Konvertuojam į mp3, Whisper labiau mėgsta mp3/wav
    audio.export("temp_audio.mp3", format="mp3")
    audio = AudioSegment.from_file("temp_audio.mp3", format="mp3")

    segment_length_ms = 5 * 60 * 1000  # 5 min segmentai
    num_segments = math.ceil(len(audio) / segment_length_ms)

    # Sukuriame Word dokumentą
    doc = Document()
    doc.add_heading("Transkribuotas tekstas", level=1)

    progress_text = st.empty()
    progress_bar = st.progress(0)

    for i in range(num_segments):
        start_ms = i * segment_length_ms
        end_ms = min((i+1)*segment_length_ms, len(audio))
        chunk = audio[start_ms:end_ms]
        chunk_file = f"chunk_{i}.mp3"
        chunk.export(chunk_file, format="mp3")

        progress_text.text(f"Transkribuojama segmentas {i+1}/{num_segments}...")

        # Transkripcija per OpenAI API
        with open(chunk_file, "rb") as f:
            transcript = openai.Audio.transcriptions.create(
                model="whisper-1",
                file=f
            )

        text = transcript["text"]
        doc.add_heading(f"Segmentas {i+1}", level=2)
        doc.add_paragraph(text)

        progress_bar.progress((i+1)/num_segments)

    st.success("Transkripcija baigta!")

    # Sukuriame bufferį Word parsisiuntimui
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    st.download_button(
        label="Parsisiųsti Word dokumentą",
        data=buffer,
        file_name="transkripcija.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
