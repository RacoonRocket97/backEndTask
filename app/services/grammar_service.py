import language_tool_python
from typing import List, Dict


class GrammarService:
    _instance = None
    _tool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GrammarService, cls).__new__(cls)
            # Use the public API (no Java required)
            cls._tool = language_tool_python.LanguageToolPublicAPI('en-US')
        return cls._instance

    def check_grammar(self, text: str) -> Dict:
        """
        Check grammar and return corrections using the public LanguageTool API.
        """
        if not text or not text.strip():
            return {'original': text, 'corrected': text, 'errors': []}

        matches = self._tool.check(text)

        corrected_text = language_tool_python.utils.correct(text, matches)

        errors = []
        for match in matches:
            errors.append({
                'message': match.message,
                'context': match.context,
                'offset': match.offset,
                'length': match.errorLength,
                'suggestions': match.replacements[:3]
            })

        return {
            'original': text,
            'corrected': corrected_text,
            'errors': errors,
            'has_errors': len(errors) > 0
        }

    def __del__(self):
        if self._tool:
            self._tool.close()
