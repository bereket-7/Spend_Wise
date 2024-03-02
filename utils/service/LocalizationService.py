import json

class LocalizationService:
    def __init__(self, default_language='en'):
        self.default_language = default_language
        self.translations = {}

    def load_translations(self, language):
        try:
            with open(f'{language}.json', 'r', encoding='utf-8') as file:
                self.translations[language] = json.load(file)
        except FileNotFoundError:
            # Handle file not found error
            pass

    def translate(self, text, language):
        if language in self.translations:
            translations = self.translations[language]
            if text in translations:
                return translations[text]
        return text