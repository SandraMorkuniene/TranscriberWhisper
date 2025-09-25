import streamlit as st
import openai
from io import BytesIO
from docx import Document

st.set_page_config(page_title="Transkribuotojas (.m4a/.mp3/.wav)")

st.title("Lietuvių kalbos transkribuotojas su Word parsisiuntimu")

st.markdown("""
Įkelkite garso įrašą (.m4a, .mp3 arba .wav). 
Transkripcija atliekama tiesiai per OpenAI Whisper API, o rezultatas pateikiamas Word dokumente.
""")

# Failo įkėlimas
audio_file = st.file_uploader(
    "Įkelkite garso įrašą",
    type=["mp3", "wav", "m4a"]
)

if audio_file is not None:
    st.info("Transkribuojama su OpenAI Whisper API. Tai gali užtrukti kelias minutes...")

    try:
        # Tiesiogiai siunčiame st.file_uploader objektą
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    except Exception as e:
        st.error(f"Klaida transkribuojant: {e}")
    else:
        text = transcript.text
        st.success("Transkripcija baigta!")

        # Sukuriame Word dokumentą
        doc = Document()
        doc.add_heading("Transkribuotas tekstas", level=1)
        doc.add_paragraph(text)

        # Parsisiuntimo bufferis
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.download_button(
            label="Parsisiųsti Word dokumentą",
            data=buffer,
            file_name="transkripcija.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
