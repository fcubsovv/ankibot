import os
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

CHINESE_SYSTEM_PROMPT = """You are a Chinese language flashcard generator. When given a Chinese word, respond EXACTLY in this format with no extra text:

FRONT: <the Chinese word>
Pinyin: <full pinyin with tone marks, e.g. nǐ hǎo>
Sentence: <a natural example sentence in Chinese using this word>
Translation: <English translation of the word>
SentenceTranslation: <English translation of the example sentence>
RelatedWords: <2-3 words that share at least one character with the given word, in format: 汉字 (pīnyīn) — English meaning, separated by semicolons>
IMAGE_PROMPT: <a short English phrase (3-5 words) describing a visual scene for this word, suitable for image search>

Rules:
- Pinyin must use proper tone diacritics (ā á ǎ à, ē é ě è, etc.)
- Sentence must be natural, intermediate level Chinese
- RelatedWords: if the input is a 2-character word, each related word must share exactly one of its characters; if 1 character, share that character
- Do not add any commentary outside this format"""

class GroqClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("api key required for groq")
        self.client = Groq(api_key=self.api_key)
        try:
            with open("system_prompt.txt", "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        except:
            self.system_prompt = "You are a helpful assistant"

    def _is_chinese(self, text: str) -> bool:
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    def ask(self, prompt: str) -> str:
        if self._is_chinese(prompt):
            system = CHINESE_SYSTEM_PROMPT
        else:
            system = self.system_prompt

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.4,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def is_chinese(self, text: str) -> bool:
        return self._is_chinese(text)

groq = GroqClient()