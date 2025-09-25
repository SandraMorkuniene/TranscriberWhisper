import streamlit as st
import openai
from io import BytesIO
from docx import Document
from pydub import AudioSegment
import tempfile
import math

st.set_page_config(page_title="Transkribuotojas su segmentacija")

st.title("Lietuvių kalbos transkribuotojas su segmentacija")
st.markdown("""
Įkelkite garso įrašą (.m4a, .mp3 arba .wav). 
Dideli failai automatiškai padalijami į 2 min. segmentus, transkribuojami per OpenAI Whisper API, o rezultatas pateikiamas Word dokumente.
""")

audio_file = st.file_uploader(
    "Įkelkite garso įrašą",
    type=["mp3","wav","m4a"]
)

if audio_file is not None:
    st.info("Konvertuojama ir segmentuojama į 2 min. dalis...")

    # Sukuriame laikina faila, kad pydub galėtų pasiekti
    ext = audio_file.name.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(audio_file.read())
        tmp_path = tmp.name

    # Atidarome audio per pydub
    audio = AudioSegment.from_file(tmp_path, format=ext)

    segment_length_ms = 2 * 60 * 1000  # 2 minutės
    num_segments = math.ceil(len(audio) / segment_length_ms)

    doc = Document()
    doc.add_heading("Transkribuotas tekstas", level=1)

    progress_text = st.empty()
    progress_bar = st.progress(0)

    for i in range(num_segments):
        start_ms = i * segment_length_ms
        end_ms = min((i + 1) * segment_length_ms, len(audio))
        chunk = audio[start_ms:end_ms]

        # Laikinas mp3 failas segmentui
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_chunk:
            chunk.export(tmp_chunk.name, format="mp3")
            chunk_path = tmp_chunk.name

        progress_text.text(f"Transkribuojama segmentas {i+1}/{num_segments}...")

        # Transkripcija per OpenAI API
        with open(chunk_path, "rb") as f:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )

        segment_text = transcript.text
        doc.add_heading(f"Segmentas {i+1}", level=2)
        doc.add_paragraph(segment_text)

        progress_bar.progress((i+1)/num_segments)

    st.success("Transkripcija baigta!")

    # Parsisiuntimo Word dokumentas
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    st.download_button(
        label="Parsisiųsti Word dokumentą",
        data=buffer,
        file_name="transkripcija.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
