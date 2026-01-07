"""
Text analysis for custom Pimsleur lessons.
Extracts vocabulary and statistics WITHOUT using LLM.
"""

import re
from collections import Counter
from typing import Optional


# Icelandic stopwords (common words to exclude from vocabulary extraction)
ICELANDIC_STOPWORDS = {
    # Articles and determiners
    "a", "i", "til", "fra", "af", "um", "vid", "med", "yfir", "undir",
    "fyrir", "eftir", "gegnum", "an", "hja",
    # Pronouns
    "eg", "thu", "hann", "hun", "thad", "vid", "thid", "their", "thau",
    "mig", "thig", "hana", "honum", "henni", "okkur", "ykkur", "theim",
    "mer", "ther", "ser", "min", "thinn", "sinn", "vor", "okkar", "ykkar",
    "theirra", "thetta", "thessi", "thessu", "thessum",
    # Common verbs (conjugated forms)
    "er", "var", "veri", "eru", "voru", "vera", "verid", "hefur", "hef",
    "hafa", "hafdi", "hofdu", "gera", "gerir", "gerdi", "fara", "fer",
    "for", "koma", "kemur", "kom", "segja", "segir", "sagdi", "vita",
    "veit", "vissi", "vilja", "vill", "vildi", "geta", "get", "gat",
    "tharf", "thurfa", "thurfti", "ma", "mega", "matti", "skal", "skulu",
    "skyldi", "mun", "munu", "myndi", "ae", "aetti",
    # Conjunctions and connectors
    "og", "eda", "en", "sem", "ad", "ef", "thegar", "thvi", "svo",
    "hvort", "baedi", "annadhvort", "hvorki", "ne", "held", "heldur",
    # Adverbs
    "ekki", "aldrei", "alltaf", "oft", "sjaldan", "stundum", "nu",
    "tha", "her", "thar", "hvar", "hvert", "hvadan", "hvenær",
    "hvernig", "af hverju", "hvers vegna", "mjog", "vel", "illa",
    "bara", "einungis", "nærri", "naerri", "fjærri", "fyrst", "sidast",
    "samt", "tho", "reyndar", "eiginlega", "samt sem adur",
    # Numbers (written)
    "einn", "tveir", "thrir", "fjorir", "fimm", "sex", "sjo", "atta",
    "niu", "tiu", "ellefu", "tolf", "tuttugu", "thratiu", "fjortiu",
    "fimmtiu", "sextiu", "sjotiu", "attatiu", "niutiu", "hundrad", "thusund",
    # Question words (exclude from vocabulary)
    "hvad", "hver", "hvar", "hvert", "hvadan",
    # Other common words
    "ja", "nei", "kannski", "takk", "bless", "hallo",
}

# German stopwords
GERMAN_STOPWORDS = {
    # Articles and determiners
    "der", "die", "das", "ein", "eine", "einer", "einem", "einen",
    "des", "dem", "den",
    # Pronouns
    "ich", "du", "er", "sie", "es", "wir", "ihr", "mich", "dich",
    "sich", "uns", "euch", "mir", "dir", "ihm", "ihr", "ihnen",
    "mein", "dein", "sein", "unser", "euer", "dieser", "jener",
    "welcher", "was", "wer", "wen", "wem", "wessen",
    # Common verbs
    "ist", "sind", "war", "waren", "sein", "bin", "bist", "seid",
    "haben", "hat", "hatte", "hatten", "habe", "hast", "werden",
    "wird", "wurde", "wurden", "werde", "wirst", "können", "kann",
    "konnte", "konnten", "müssen", "muss", "musste", "sollen", "soll",
    "sollte", "wollen", "will", "wollte", "dürfen", "darf", "durfte",
    "mögen", "mag", "mochte", "gehen", "geht", "ging", "kommen",
    "kommt", "kam", "machen", "macht", "machte", "tun", "tut", "tat",
    # Prepositions
    "in", "an", "auf", "mit", "bei", "nach", "zu", "von", "aus",
    "für", "über", "unter", "vor", "hinter", "neben", "zwischen",
    "durch", "gegen", "ohne", "um", "bis", "seit", "während",
    # Conjunctions
    "und", "oder", "aber", "denn", "weil", "dass", "wenn", "als",
    "ob", "obwohl", "damit", "sondern", "jedoch", "trotzdem",
    # Adverbs
    "nicht", "auch", "nur", "noch", "schon", "sehr", "mehr", "immer",
    "wieder", "hier", "da", "dort", "jetzt", "dann", "nun", "so",
    "wie", "warum", "wo", "wann", "heute", "gestern", "morgen",
    # Other common words
    "ja", "nein", "vielleicht", "bitte", "danke",
}

# Map language codes to stopwords
STOPWORDS_BY_LANGUAGE = {
    "is": ICELANDIC_STOPWORDS,
    "de": GERMAN_STOPWORDS,
}


class TextAnalyzer:
    """Analyzes text for vocabulary extraction without LLM."""

    def __init__(self, language_code: str = "is"):
        """
        Initialize the text analyzer.

        Args:
            language_code: ISO language code ('is' for Icelandic, 'de' for German)
        """
        self.language_code = language_code
        self.stopwords = STOPWORDS_BY_LANGUAGE.get(language_code, set())

    def analyze(self, text: str) -> dict:
        """
        Analyze text and extract statistics and vocabulary.

        Args:
            text: Source text in target language

        Returns:
            Dictionary with analysis results:
            - word_count: Total words in text
            - unique_words: Count of unique words
            - char_count: Total characters
            - sentence_count: Number of sentences
            - avg_word_length: Average word length
            - avg_sentence_length: Average words per sentence
            - estimated_lesson_words: Expected vocabulary items in lesson
            - vocabulary_preview: List of vocabulary items with counts
            - detected_difficulty: Estimated CEFR level (A1/A2/B1)
        """
        # Normalize text
        text = self._normalize_text(text)

        # Basic stats
        words = self._tokenize(text)
        word_count = len(words)
        unique_words_set = set(w.lower() for w in words)
        unique_words = len(unique_words_set)
        sentences = self._split_sentences(text)
        sentence_count = len(sentences)

        # Word frequency (excluding stopwords)
        content_words = [
            w.lower() for w in words
            if w.lower() not in self.stopwords and len(w) > 1
        ]
        word_freq = Counter(content_words)

        # Top vocabulary (most frequent content words)
        vocabulary_preview = [
            {
                "word": word,
                "count": count,
                "is_frequent": count > 2,
            }
            for word, count in word_freq.most_common(25)
        ]

        # Estimate how many words will be in the lesson (10-20)
        estimated_lesson_words = min(20, max(10, len(vocabulary_preview)))

        # Calculate averages
        avg_word_length = sum(len(w) for w in words) / max(1, word_count)
        avg_sentence_length = word_count / max(1, sentence_count)

        # Detect difficulty based on text characteristics
        detected_difficulty = self._estimate_difficulty(
            avg_word_length, avg_sentence_length, unique_words
        )

        return {
            "word_count": word_count,
            "unique_words": unique_words,
            "char_count": len(text),
            "sentence_count": sentence_count,
            "avg_word_length": round(avg_word_length, 1),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "estimated_lesson_words": estimated_lesson_words,
            "vocabulary_preview": vocabulary_preview,
            "detected_difficulty": detected_difficulty,
        }

    def _normalize_text(self, text: str) -> str:
        """Normalize text for analysis."""
        # Replace common Unicode variants
        text = text.replace("'", "'").replace("'", "'")
        text = text.replace(""", '"').replace(""", '"')
        # Normalize whitespace
        text = " ".join(text.split())
        return text

    def _tokenize(self, text: str) -> list[str]:
        """Split text into words."""
        # Remove punctuation but keep Icelandic characters
        # Pattern keeps letters (including Icelandic: þ, ð, á, é, í, ó, ú, ý, æ, ö)
        pattern = r"[^\w\sþðáéíóúýæöÞÐÁÉÍÓÚÝÆÖäüßÄÜẞ]"
        cleaned = re.sub(pattern, " ", text, flags=re.UNICODE)
        return [w for w in cleaned.split() if w]

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Split on sentence-ending punctuation
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _estimate_difficulty(
        self,
        avg_word_length: float,
        avg_sentence_length: float,
        unique_words: int
    ) -> str:
        """
        Estimate CEFR difficulty level based on text characteristics.

        Uses heuristics based on:
        - Word length (longer words = more complex)
        - Sentence length (longer sentences = more complex)
        - Vocabulary diversity (more unique words = more complex)

        Returns: 'A1', 'A2', or 'B1'
        """
        score = 0

        # Word length scoring
        if avg_word_length > 5:
            score += 1
        if avg_word_length > 7:
            score += 1

        # Sentence length scoring
        if avg_sentence_length > 10:
            score += 1
        if avg_sentence_length > 15:
            score += 1

        # Vocabulary diversity scoring
        if unique_words > 80:
            score += 1
        if unique_words > 150:
            score += 1

        # Map score to CEFR level
        if score <= 1:
            return "A1"
        elif score <= 3:
            return "A2"
        else:
            return "B1"

    def generate_title(self, text: str, max_length: int = 50) -> str:
        """
        Generate a lesson title from the source text.

        Uses the first sentence if it's suitable, otherwise first few words.

        Args:
            text: Source text
            max_length: Maximum title length

        Returns:
            Generated title string
        """
        text = self._normalize_text(text)
        sentences = self._split_sentences(text)

        if sentences:
            first_sentence = sentences[0]
            if len(first_sentence) <= max_length:
                return first_sentence
            # Truncate at word boundary
            truncated = first_sentence[:max_length]
            if " " in truncated:
                truncated = truncated.rsplit(" ", 1)[0]
            return truncated + "..."

        # Fallback: first few words
        words = text.split()[:7]
        title = " ".join(words)
        if len(title) > max_length:
            title = title[:max_length].rsplit(" ", 1)[0] + "..."
        return title

    def get_vocabulary_summary(self, text: str, limit: int = 15) -> list[dict]:
        """
        Get a simple vocabulary summary for display.

        Args:
            text: Source text
            limit: Maximum number of words to return

        Returns:
            List of vocabulary items with word and count
        """
        analysis = self.analyze(text)
        return analysis["vocabulary_preview"][:limit]
