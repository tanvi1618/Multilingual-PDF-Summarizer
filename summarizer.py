import os
import nltk
import pytesseract
import re
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.snowball import SnowballStemmer
from PIL import Image
nltk.download("stopwords")
nltk.download("punkt")
nltk.download("punkt_tab")

def extractText(file):
    pdf_document = fitz.open(file)
    text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text

def extractOCR(file):
    pages = convert_from_path(file, 500)

    image_counter = 1
    for page in pages:
        filename = "page_" + str(image_counter) + ".jpg"
        page.save(filename, "JPEG")
        image_counter = image_counter + 1

    limit = image_counter-1
    text = ""
    for i in range(1, limit + 1):
        filename = "page_" + str(i) + ".jpg"
        page = str(((pytesseract.image_to_string(Image.open(filename)))))
        page = page.replace("-\n", "")
        text += page
        os.remove(filename)
    return text

def summarize(text):
    processedText = re.sub("’", "'", text)
    processedText = re.sub("[^a-zA-Z' ]+", " ", processedText)
    stopWords = set(stopwords.words("english"))
    words = word_tokenize(processedText)

    stemmer = SnowballStemmer("english", ignore_stopwords=True)
    freqTable = dict()
    for word in words:
        word = word.lower()
        if word in stopWords:
            continue
        elif stemmer.stem(word) in freqTable:
            freqTable[stemmer.stem(word)] += 1
        else:
            freqTable[stemmer.stem(word)] = 1

    sentences = sent_tokenize(text)
    stemmedSentences = []
    sentenceValue = dict()
    for sentence in sentences:
        stemmedSentence = []
        for word in sentence.lower().split():
            stemmedSentence.append(stemmer.stem(word))
        stemmedSentences.append(stemmedSentence)

    for num in range(len(stemmedSentences)):
        for wordValue in freqTable:
            if wordValue in stemmedSentences[num]:
                if sentences[num][:12] in sentenceValue:
                    sentenceValue[sentences[num][:12]] += freqTable.get(wordValue)
                else:
                    sentenceValue[sentences[num][:12]] = freqTable.get(wordValue)

    sumValues = 0
    for sentence in sentenceValue:
        sumValues += sentenceValue.get(sentence)

    average = int(sumValues / len(sentenceValue))

    summary = ""
    for sentence in sentences:
            if sentence[:12] in sentenceValue and sentenceValue[sentence[:12]] > (3.0 * average):
                summary += " " + " ".join(sentence.split())

    summary = re.sub("’", "'", summary)
    summary = re.sub("[^a-zA-Z0-9'\"():;,.!?— ]+", " ", summary)
    summaryText = open(fileName + "Summary.txt", "w")
    summaryText.write(summary)
    summaryText.close()

print("What is the name of the PDF?")
fileName = input("(Without .pdf file extension)\n")
pdfFileName = fileName + ".pdf"
option = input("Direct text extraction or OCR extraction? (text / OCR)\n")

if option == "text":
    text = extractText(pdfFileName)
    summarize(text)
elif option == "OCR":
    text = extractOCR(pdfFileName)
    summarize(text)
else:
    print("Not a valid option!")