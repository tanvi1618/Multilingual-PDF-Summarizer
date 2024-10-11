from pypdf import PdfReader
import streamlit as st
from together import Together
import os
from dotenv import load_dotenv
from googletrans import Translator
from gtts import gTTS

load_dotenv()

summary_prompt = """
You are a text summarizer. Your task is to analyze text and provide a summary of the text.
Make sure your summaries are accurate and concise. Do not include any unnecessary information.
The following is the text you need to summarize:
"""

model_id = "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"

client = Together(api_key=os.getenv('TOGETHER_KEY'))

translator = Translator()
languages = {
    'English': 'en',
    'Hindi': 'hi',
    'Gujarati': 'gu',
    'Kannada': 'kn',
    'Sindhi': 'sd',
    'Marathi': 'mr',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Italian': 'it',
}

def parse_pdf(file_path):
    reader = PdfReader(file_path)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

def synthesize_speech(content, language):
    speech = gTTS(text=content, lang=language, slow=False)
    audio_file_path = "voice.mp3"
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)
    speech.save(audio_file_path)
    return audio_file_path

def get_summary(text):
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": summary_prompt + text}]
            }
        ],
        max_tokens=512,
        temperature=0.3,
        top_p=0.95,
        top_k=50,
        repetition_penalty=1,
        stop=["<|eot_id|>", "<|eom_id|>"],
    )
    return response.choices[0].message.content.strip()

def main():
    st.set_page_config(page_title='Text Summarizer', 
                       initial_sidebar_state='collapsed', 
                       layout='wide',
                       page_icon='📄')
    st.title('Text Summarizer')
    
    cols = st.columns(2)
    uploaded_file = cols[0].file_uploader('Upload a PDF file', type=['pdf'])
    language = cols[1].selectbox('Select language', list(languages.keys()))
    selected_language = languages[language]
    
    if 'summary' not in st.session_state:
        st.session_state.summary = ''
    
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    
    if st.button('Summarize'):
        if uploaded_file is None:
            st.error('Please upload a file.')
            return

        with st.spinner('Parsing PDF...'):
            text = parse_pdf(uploaded_file)
        with st.spinner('Summarizing...'):
            summary = get_summary(text)
            
        st.session_state.summary = summary
    
    st.subheader('Summary')
    summary = st.session_state.summary
    if summary:
        if selected_language != 'en':
            summary = translator.translate(summary, src='en', dest=selected_language).text
        st.write(summary)
        
        if st.button("🔊 Generate Audio"):
            try:
                audio_file_path = synthesize_speech(summary, selected_language)
                st.session_state.audio_file = audio_file_path
            except ValueError:
                st.error("Audio generation not supported for this language.")
    
    if st.session_state.audio_file:
        st.audio(st.session_state.audio_file)

if __name__ == '__main__':
    main()
