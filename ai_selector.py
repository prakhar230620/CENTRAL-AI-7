import json
from collections import Counter
from typing import List, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)


class AISelector:
    def __init__(self):
        self.ai_keywords = {}
        self.model_file = 'ai_selector_data.json'
        self._load_model()

    def _initialize_model(self):
        if not os.path.exists(self.model_file):
            with open(self.model_file, 'w') as f:
                json.dump({}, f)
            logger.info("Initialized empty AI selector data file")

    def _load_model(self):
        self._initialize_model()
        with open(self.model_file, 'r') as f:
            self.ai_keywords = json.load(f)
        logger.info("Loaded AI selector data")

    def train(self, training_data: List[Dict[str, Any]]):
        for item in training_data:
            ai_id = item['selected_ai']
            keywords = item['input'].lower().split() + [item['intent']] + item['entities']
            if ai_id not in self.ai_keywords:
                self.ai_keywords[ai_id] = Counter()
            self.ai_keywords[ai_id].update(keywords)

        self._save_model()
        logger.info("AI selector data updated and saved")

    def select_best_ai(self, analyzed_input: Dict[str, Any], available_ai: List[Dict[str, Any]]) -> str:
        if not available_ai:
            return "No AI connected to the program"

        input_keywords = analyzed_input['cleaned_input'].lower().split() + [analyzed_input['intent']] + list(
            analyzed_input['entities'].keys())

        ai_scores = {}
        for ai in available_ai:
            ai_id = ai['id']
            if ai_id in self.ai_keywords:
                score = sum(self.ai_keywords[ai_id].get(keyword, 0) for keyword in input_keywords)
                ai_scores[ai_id] = score
            else:
                ai_scores[ai_id] = 0

        if not ai_scores:
            return available_ai[0]['id']  # Return the first available AI if no scores

        best_ai_id = max(ai_scores, key=ai_scores.get)
        return best_ai_id

    def update_model(self, new_data: List[Dict[str, Any]]):
        self.train(new_data)

    def _save_model(self):
        with open(self.model_file, 'w') as f:
            json.dump(self.ai_keywords, f)
        logger.info("AI selector data saved")

    def load_model(self):
        self._load_model()