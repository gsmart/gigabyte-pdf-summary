import requests
import re
import nltk
from collections import Counter
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

# Download NLTK tokenization model
nltk.download('punkt')

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:1.5b"
CHUNK_SIZE = 10000

class SummaryGenerator:
    def __init__(self, extracted_text):
        """Initialize the summary generator with extracted text."""
        self.text = extracted_text
        self.section_titles = self.extract_section_titles()
    
    def extract_section_titles(self):
        """Extracts section titles from the 'CONTENTS' page."""
        section_pattern = r'(\d+)\.\s*(.+?)\s+(\d+)'
        matches = re.findall(section_pattern, self.text)
        return {int(match[2]): match[1].strip() for match in matches}
    
    def chunk_text(self, text, chunk_size=CHUNK_SIZE):
        """Splits text into smaller chunks for processing."""
        words = text.split()
        return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

    
    def allocate_summary_proportionally(self):
        """Determines space allocation based on section coverage in extracted text."""
        section_word_count = {title: 0 for title in self.section_titles.values()}
        current_section = None

        for line in self.text.split("\n"):
            for title in self.section_titles.values():
                if title.lower() in line.lower():
                    current_section = title  # Track current section
            if current_section:
                section_word_count[current_section] += len(line.split())

        # Normalize proportions
        total_words = sum(section_word_count.values())
        return {title: round((count / total_words) * 100, 2) for title, count in section_word_count.items()} if total_words else {}

    def generate_summary_old(self):
        """Generates structured summary covering all major sections proportionally."""

        # Allocate space proportionally
        proportions = self.allocate_summary_proportionally()

        # Ensure we have meaningful sections; if not, fallback to TF-IDF based topics
        if not self.section_titles:
            self.section_titles = {i+1: topic for i, topic in enumerate(self.extract_key_topics(8))}

        # Construct summary prompt dynamically
        section_headers = "\n".join(
            [f"- **{section}** ({proportions.get(section, 5)}% of summary)\n    - [Bullet points covering key insights]"
             for section in self.section_titles.values()]
        )

        prompt = f"""
        Generate a **structured summary** covering all major sections in the document.

        **Document Summary**  
        {section_headers}

        **Conclusion**  
        - Summarize key takeaways in 2-3 lines.

        Ensure:  
        - **Every major section is covered** proportionally.  
        - The output is **concise yet complete**.  
        - No **hallucinations or missing sections**.  
        - Use **bullet points for readability**.  

        **Document Content:**  
        {self.text}

        Return only the structured summary.
        """

        response = requests.post(OLLAMA_API_URL, json={"model": MODEL_NAME,"prompt": prompt,"stream": False,"max_tokens": 2048 }).json()

        raw_summary = response.get("response", "⚠️ No summary generated.").strip()

        return self.clean_summary(raw_summary)

    def clean_summary_old(self, summary):
        """Removes AI-generated messages, reasoning, and unnecessary filler text."""
        
        # Remove AI reasoning/thought markers
        summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.DOTALL).strip()
        
        # Remove common AI-generated introduction lines
        summary = re.sub(
            r"(Certainly! Here is a structured summary of the key points covered in the provided content:|"
            r"Sure! Here's a structured summary:|"
            r"Below is a structured overview of the document:|"
            r"Here's an organized summary:|"
            r"Here's a concise breakdown:|"
            r"Here's what I found:|"
            r"Based on the provided content, here is a summary:|"
            r"Let's break this down into key sections:|"
            r"Here’s an overview of the document's key points:|"
            r"This is a high-level overview of the provided content:)", 
            "", summary, flags=re.IGNORECASE
        ).strip()

        # Remove AI-generated conclusion/filler statements
        summary = re.sub(
            r"(This summary captures the main points from each relevant section, highlighting key initiatives, challenges, and goals for .*?\.|"
            r"This structured summary provides an overview of the key topics covered in the document\.|"
            r"This concludes the summary of the key insights presented in the content\.|"
            r"The above summary provides an outline of the document's primary sections and themes\.)",
            "", summary, flags=re.IGNORECASE
        ).strip()
        
        # Remove any excessive newlines or spaces
        summary = re.sub(r"\n\s*\n", "\n\n", summary).strip()
        
        return summary

    def generate_summary(self):
        """Generates structured summary covering all sections proportionally."""
        text_chunks = self.chunk_text(self.text)
        chunk_summaries = []

        for i, chunk in enumerate(text_chunks):
            print(f"⏳ Processing Chunk {i+1}/{len(text_chunks)}...")

            prompt = f"""
            Generate a **detailed summary** of this section.

            **Summary Requirements:**
            - Maintain all key insights from the text.
            - Use **bullet points** and **headings** for readability.
            - Ensure the summary is **complete and well-structured**.

            **Section Content:**  
            {chunk}

            **Return only the structured summary.**
            """

            response = requests.post(OLLAMA_API_URL, json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "max_tokens": 8192
            }).json()

            chunk_summaries.append(response.get("response", "⚠️ No summary generated.").strip())

        # 🔹 Merge chunk summaries
        final_summary = "\n\n".join(chunk_summaries)
        return self.clean_summary(final_summary)
    
    def clean_summary(self, summary):
        """Removes AI-generated messages and unnecessary filler text."""
        summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.DOTALL).strip()
        summary = re.sub(r"\n\s*\n", "\n\n", summary).strip()
        return summary

    def extract_key_topics(self, top_n=5):
        """Extracts key topics dynamically using TF-IDF."""
        sentences = sent_tokenize(self.text)
        if len(sentences) < 3:
            return ["General Overview"]

        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        X = vectorizer.fit_transform(sentences)

        feature_array = vectorizer.get_feature_names_out()
        tfidf_scores = X.toarray().sum(axis=0)
        sorted_indices = tfidf_scores.argsort()[::-1]
        top_terms = [feature_array[idx] for idx in sorted_indices[:top_n]]

        return [term.title() for term in top_terms]
