from pypdf import PdfReader
import streamlit as st
import spacy
import nltk
from together import Together
import os
from dotenv import load_dotenv
from googletrans import Translator

load_dotenv()

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('en_core_web_sm')

nlp = spacy.load('en_core_web_sm')

translator = Translator()
selected_language = 'en'

languages = {
    'English': 'en',
    'Hindi': 'hi',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Italian': 'it',
    'Sanskrit': 'sa',
}

prompt = """
You are a text refiner. Your task is to analyse text, improve its grammar and give it structure. 
Make sure your text is accurate and concise. Do not include any unnecessary information or change the meaning of the text. 
Return only the refined text.
The following is the text you need to refine:

"""
model_id="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"

client = Together(api_key=os.getenv('TOGETHER_KEY'))

def parse_pdf(file_path):
    reader = PdfReader(file_path)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text


def get_summary(text):
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    entity_freq = {}
    for ent in doc.ents:
        if ent.text not in entity_freq:
            entity_freq[ent.text] = 1
        else:
            entity_freq[ent.text] += 1
    
    ranked_sentences = sorted(sentences, key=lambda sent: sum(entity_freq.get(word, 0) for word in sent.split()), reverse=True)
    summary = ' '.join(ranked_sentences[:5])
    return summary

def refine_summary(summary):
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "user",
                "content": [
                        {
                                "type": "text",
                                "text": prompt + summary
                        }
                ]
        }],
        max_tokens=512,
        temperature=0.3,
        top_p=0.95,
        top_k=50,
        repetition_penalty=1,
        stop=["<|eot_id|>","<|eom_id|>"],
    )
    return response.choices[0].message.content.strip()

def main():
    st.set_page_config(page_title='Text Summarizer', initial_sidebar_state='collapsed', layout='wide')
    st.title('Text Summarizer')
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader('Upload a PDF file', type=['pdf'])
    with col2:
        language = st.selectbox('Select language', list(languages.keys()))
        selected_language = languages[language]

    summarize_button = st.button('Summarize')
    if summarize_button:
        if uploaded_file is None:
            st.error('Please upload a file.')
            return
        with st.spinner('Parsing PDF...'):
            text = parse_pdf(uploaded_file)
        with st.spinner('Summarizing...'):
            summary = get_summary(text)
            summary = refine_summary(summary)
            
        st.subheader('Summary')
        if selected_language != 'en':
            summary = translator.translate(summary, src='en', dest=selected_language).text
        st.write(summary)
                        
if __name__ == '__main__':
    main()