import re
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict

# Download required NLTK resources
nltk.download('punkt')

class TopicExtractor:
    """
    Extracts key topics from a text using TF-IDF for structured summary generation.
    """

    def __init__(self, text, top_n=5):
        self.text = text
        self.top_n = top_n

def extract_key_topics(text, top_n=10):
    """
    Extracts key topics dynamically but ensures all major sections get equal weightage.
    """
    sections = defaultdict(str)
    sentences = sent_tokenize(text)
    
    # Divide the text into sections based on common headings
    current_section = "General Overview"
    
    for sent in sentences:
        if re.match(r"^\d+\.\s[A-Z]", sent):  # Matches headings like '1. State of the Economy'
            current_section = sent.strip()
        
        sections[current_section] += " " + sent.strip()
    
    # Apply TF-IDF only **within** each major section
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    
    extracted_topics = []
    
    for section, content in sections.items():
        X = vectorizer.fit_transform(sent_tokenize(content))
        feature_array = vectorizer.get_feature_names_out()
        tfidf_scores = X.toarray().sum(axis=0)
        sorted_indices = tfidf_scores.argsort()[::-1]
        
        top_terms = [feature_array[idx] for idx in sorted_indices[:top_n]]
        extracted_topics.append((section, top_terms))
    
    return extracted_topics