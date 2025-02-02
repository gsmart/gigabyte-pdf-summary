import re
import nltk

# Ensure NLTK tokenizer data is available
nltk.download('punkt')


class TextRefiner:
    """Class to clean and refine extracted text by removing gibberish, statistical noise, and unwanted elements."""

    def __init__(self, text):
        self.text = text

    def remove_unwanted_patterns(self):
        """Removes common numerical/statistical anomalies and gibberish text."""
        # Remove excessive whitespace and line breaks
        self.text = re.sub(r'\n+', ' ', self.text)
        self.text = re.sub(r'\s+', ' ', self.text).strip()

        # Remove isolated numbers or gibberish characters
        self.text = re.sub(r'\b\d{3,}\b', '', self.text)  # Remove long isolated numbers
        self.text = re.sub(r'[^a-zA-Z0-9\s,.\-\'"()\[\]%]', '', self.text)  # Remove special characters except punctuation

        return self.text

    def refine_text(self):
        """Applies all text refinement methods and returns cleaned text."""
        self.text = self.remove_unwanted_patterns()
        return self.text
