import io
import time
import requests

import speech_recognition as sr
import streamlit as st


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Speech to Text",
    page_icon="🎤",
    layout="centered"
)


# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.title("🎤 Speech-to-Text Application")

st.write(
    "Record your voice, convert it into text, "
    "and translate it to English."
)


# ---------------------------------------------------------
# SUPPORTED LANGUAGES
# ---------------------------------------------------------

LANGUAGES = {
    "Arabic (UAE)": "ar-AE",
    "Arabic (Saudi Arabia)": "ar-SA",
    "Arabic (Egypt)": "ar-EG",
    "English (US)": "en-US",
}


language_name = st.selectbox(
    "Select Language",
    list(LANGUAGES.keys())
)

language = LANGUAGES[language_name]

is_english = language.startswith("en")


# ---------------------------------------------------------
# TRANSLATION OPTION
# ---------------------------------------------------------

translate_enabled = st.checkbox(
    "Translate to English",
    value=not is_english,
    disabled=is_english
)


# ---------------------------------------------------------
# SPEECH RECOGNITION
# ---------------------------------------------------------

def transcribe_audio(audio_data, language, retries=2):

    recognizer = sr.Recognizer()

    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    last_error = None

    for attempt in range(retries):

        try:

            text = recognizer.recognize_google(
                audio_data,
                language=language
            )

            return text.strip()

        except sr.UnknownValueError:

            raise

        except sr.RequestError as e:

            last_error = e

            if attempt < retries - 1:
                time.sleep(2)

    raise sr.RequestError(
        f"Speech recognition service is unavailable. "
        f"Details: {last_error}"
    )


# ---------------------------------------------------------
# TRANSLATION
# ---------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def translate_to_english(text, source_language):

    source = source_language.split("-")[0]

    url = "https://api.mymemory.translated.net/get"

    params = {
        "q": text,
        "langpair": f"{source}|en"
    }

    last_error = None

    for attempt in range(2):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=15
            )

            response.raise_for_status()

            data = response.json()

            # Get translated text
            translated_text = (
                data
                .get("responseData", {})
                .get("translatedText")
            )

            if translated_text:

                return translated_text.strip()

            raise RuntimeError(
                "No translation was returned by the translation service."
            )

        except Exception as e:

            last_error = e

            if attempt < 1:
                time.sleep(2)

    raise RuntimeError(
        f"Translation failed: {last_error}"
    )


# ---------------------------------------------------------
# AUDIO RECORDING
# ---------------------------------------------------------

audio_value = st.audio_input(
    "🎙️ Record your voice"
)


# ---------------------------------------------------------
# PROCESS AUDIO
# ---------------------------------------------------------

if audio_value is not None:

    # Display recorded audio
    st.audio(audio_value)

    with st.spinner("Processing speech..."):

        try:

            # -------------------------------------------------
            # READ AUDIO
            # -------------------------------------------------

            audio_bytes = audio_value.getvalue()

            audio_file = io.BytesIO(audio_bytes)

            recognizer = sr.Recognizer()

            with sr.AudioFile(audio_file) as source:

                audio_data = recognizer.record(source)


            # -------------------------------------------------
            # SPEECH TO TEXT
            # -------------------------------------------------

            text = transcribe_audio(
                audio_data,
                language
            )


            # -------------------------------------------------
            # CHECK TRANSCRIPTION
            # -------------------------------------------------

            if not text:

                st.warning(
                    "No speech was detected. "
                    "Please record your voice again."
                )

            else:

                st.success(
                    "Speech converted successfully!"
                )


                # -------------------------------------------------
                # TRANSCRIBED TEXT
                # -------------------------------------------------

                st.subheader("📝 Transcribed Text")

                st.text_area(
                    "Recognized Speech",
                    text,
                    height=150
                )


                # -------------------------------------------------
                # TRANSLATION
                # -------------------------------------------------

                if translate_enabled and not is_english:

                    with st.spinner(
                        "Translating to English..."
                    ):

                        try:

                            translated = translate_to_english(
                                text,
                                language
                            )

                            st.success(
                                "Translation completed!"
                            )

                            st.subheader(
                                "🇬🇧 English Translation"
                            )

                            st.text_area(
                                "Translation",
                                translated,
                                height=150
                            )

                        except Exception as e:

                            st.error(
                                "Translation service is temporarily "
                                "unavailable."
                            )

                            st.info(
                                f"Translation error: {e}"
                            )


        # ---------------------------------------------------------
        # SPEECH NOT UNDERSTOOD
        # ---------------------------------------------------------

        except sr.UnknownValueError:

            st.warning(
                "Sorry, I could not understand the speech. "
                "Please speak clearly and try again."
            )


        # ---------------------------------------------------------
        # GOOGLE SPEECH CONNECTION ERROR
        # ---------------------------------------------------------

        except sr.RequestError as e:

            st.error(
                "Speech recognition service is temporarily "
                "unavailable."
            )

            st.info(
                "The audio was recorded successfully, but the "
                "speech recognition service could not be reached. "
                "Please check your network connection."
            )


        # ---------------------------------------------------------
        # GENERAL ERROR
        # ---------------------------------------------------------

        except Exception as e:

            st.error(
                f"Error while processing audio: {e}"
            )