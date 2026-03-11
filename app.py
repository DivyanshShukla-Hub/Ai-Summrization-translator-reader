import streamlit as st
import requests
import os
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import azure.cognitiveservices.speech as speechsdk 

# 1. PAGE SETUP & METALLIC CSS THEME
st.set_page_config(page_title="AI Article Assistant", page_icon="🌐", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d0d0d; color: #e0e0e0; }
    .stButton > button {
        background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
        color: #00C853; 
        border: 1px solid #333;
        border-radius: 8px;
        box-shadow: 3px 3px 6px #050505, -3px -3px 6px #2f2f2f;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(145deg, #1a1a1a, #2a2a2a);
        color: #00E676;
        border: 1px solid #00C853;
        box-shadow: 0 0 12px rgba(0, 200, 83, 0.5);
    }
    .stTextArea textarea {
        background-color: #121212 !important;
        color: #00C853 !important;
        border: 1px solid #333 !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 2. LOAD CREDENTIALS
load_dotenv()

language_key = os.getenv("LANGUAGE_KEY")
language_endpoint = os.getenv("LANGUAGE_ENDPOINT")
translator_key = os.getenv("TRANSLATOR_KEY")
translator_region = os.getenv("TRANSLATOR_REGION")
speech_key = os.getenv("SPEECH_KEY")
speech_region = os.getenv("SPEECH_REGION")

credential = AzureKeyCredential(language_key)
text_client = TextAnalyticsClient(endpoint=language_endpoint, credential=credential)

LANGUAGES = {
    "Hindi": {"code": "hi", "voice": "hi-IN-SwaraNeural"},
    "French": {"code": "fr", "voice": "fr-FR-DeniseNeural"},
    "Spanish": {"code": "es", "voice": "es-ES-ElviraNeural"},
    "German": {"code": "de", "voice": "de-DE-KatjaNeural"}
}

# 3. SESSION STATE
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "translated" not in st.session_state:
    st.session_state.translated = ""
if "audio_ready" not in st.session_state:
    st.session_state.audio_ready = False

# 4. UI: SIDEBAR
with st.sidebar:
    st.title("⚙️ System Config")
    selected_lang_name = st.selectbox("Output Language:", list(LANGUAGES.keys()))
    st.divider()
    st.info("System Status: Online\n\nModules: Text Analytics, Translator, Speech Studio")

# 5. UI: MAIN DASHBOARD
st.markdown("<h1 style='text-align: center; color: #00C853;'>NEURAL TEXT PROCESSOR</h1>", unsafe_allow_html=True)
st.divider()

col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("📥 Data Input")
    article = st.text_area("Initialize source text here:", height=300)
    
    if st.button("EXECUTE SUMMARIZATION", use_container_width=True):
        if article.strip() != "":
            with st.spinner("Processing neural summary..."):
                poller = text_client.begin_extract_summary([article])
                response = poller.result()
                summary = " ".join([sentence.text for doc in response if not doc.is_error for sentence in doc.sentences])
                st.session_state.summary = summary
                st.session_state.translated = ""
                st.session_state.audio_ready = False

with col2:
    st.subheader("📤 Processed Output")
    if st.session_state.summary:
        st.success(st.session_state.summary)
        
        with st.expander("🌍 TRANSLATION & AUDIO PROTOCOLS", expanded=True):
            if st.button("RUN TRANSLATION", use_container_width=True):
                with st.spinner("Translating matrix..."):
                    target_code = LANGUAGES[selected_lang_name]["code"]
                    url = "https://api.cognitive.microsofttranslator.com/translate"
                    params = {"api-version": "3.0", "to": target_code}
                    headers = {
                        "Ocp-Apim-Subscription-Key": translator_key,
                        "Ocp-Apim-Subscription-Region": translator_region,
                        "Content-Type": "application/json"
                    }
                    body = [{"text": st.session_state.summary}]
                    
                    response = requests.post(url, params=params, headers=headers, json=body)
                    if response.status_code == 200:
                        st.session_state.translated = response.json()[0]["translations"][0]["text"]
                        st.session_state.audio_ready = False

            if st.session_state.translated:
                st.write(st.session_state.translated)
                
                if st.button("INITIATE AUDIO", use_container_width=True):
                    with st.spinner("Synthesizing vocals..."):
                        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
                        speech_config.speech_synthesis_voice_name = LANGUAGES[selected_lang_name]["voice"]
                        
                        # Save audio to a file instead of playing on server speakers
                        audio_config = speechsdk.audio.AudioOutputConfig(filename="output_audio.wav")
                        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                        
                        result = synthesizer.speak_text_async(st.session_state.translated).get()
                        
                        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                            st.session_state.audio_ready = True
                
                # If audio is generated, show the web audio player
                if st.session_state.audio_ready:

                    st.audio("output_audio.wav", format="audio/wav")




