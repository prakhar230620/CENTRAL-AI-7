import re
from typing import Dict, Any,List
from textblob import TextBlob

class InputAnalyzer:
    def __init__(self):
        pass

    def analyze(self, user_input: str, input_type: str) -> Dict[str, Any]:
        cleaned_input = self._clean_text(user_input)
        tokens = self._tokenize(cleaned_input)
        intent = self._determine_intent(tokens)
        entities = self._extract_entities(tokens, user_input)
        sentiment = self._analyze_sentiment(user_input)

        return {
            "original_input": user_input,
            "cleaned_input": cleaned_input,
            "tokens": tokens,
            "intent": intent,
            "entities": entities,
            "sentiment": sentiment
        }

    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()

    def _tokenize(self, text: str) -> List[str]:
        return text.split()

    def _determine_intent(self, tokens: List[str]) -> str:
        intent_keywords = {
            "search": ["find", "search", "look", "query", "where", "what"],
            "create": ["create", "make", "add", "new", "generate"],
            "delete": ["delete", "remove", "erase", "destroy", "eliminate"],
            "update": ["update", "change", "modify", "edit", "alter"],
            "help": ["help", "assist", "support", "guide", "explain"],
            "info": ["information", "details", "tell", "about", "describe"]
        }

        for intent, keywords in intent_keywords.items():
            if any(token in keywords for token in tokens):
                return intent
        return "unknown"

    def _extract_entities(self, tokens: List[str], original_text: str) -> Dict[str, Any]:
        entities = {}

        # Extract numbers
        numbers = re.findall(r'\d+', original_text)
        if numbers:
            entities["numbers"] = [int(num) for num in numbers]

        # Extract potential names (sequences of capitalized words)
        name_pattern = re.compile(r'\b(?:[A-Z][a-z]* )*[A-Z][a-z]*\b')
        names = name_pattern.findall(original_text)
        if names:
            entities["names"] = names

        # Extract dates
        date_pattern = re.compile(r'\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{2,4}')
        dates = date_pattern.findall(original_text)
        if dates:
            entities["dates"] = dates

        return entities

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        blob = TextBlob(text)
        sentiment_score = blob.sentiment.polarity
        subjectivity_score = blob.sentiment.subjectivity

        if sentiment_score > 0.1:
            sentiment = "positive"
        elif sentiment_score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        if subjectivity_score > 0.5:
            subjectivity = "subjective"
        else:
            subjectivity = "objective"

        return {
            "sentiment": sentiment,
            "subjectivity": subjectivity,
            "sentiment_score": sentiment_score,
            "subjectivity_score": subjectivity_score
        }