



PROMPTS =[
    {
        "type": "english-easy",
        "front": {
            "prompt": "exactly what the user sent — word, phrase, or full sentence",
            "rules": "- If the user sends a single word: follow the standard flashcard format, - If the user sends a phrase or full sentence: put the entire input on FRONT as-is, synonyms should be similar expressions or paraphrases, and Sentence should use ____ to replace the key word or the entire phrase"
                  },
        "back": {
            "synonyms": {
            "prompt": "2-3 synonyms or similar phrases",
            "rules": "- Synonyms must closely match the word's core meaning, - If the word has multiple meanings, use all of them"
                  },
            "sentence" : {
            "prompt": "sentence with ____ replacing the key word or phrase",
            "rules": "- Sentence must be 4–6 words total (including prepositions) - Sentence must clearly reveal the word's meaning through context, - Replace the target word or phrase with ____"
                  },
            "translation" : {
            "prompt": "Russian translation, maximally close in meaning — including colloquial or vulgar equivalents if they convey the meaning more precisely",
            "rules": "- Translation must reflect the true meaning as closely as possible — do not sanitize or soften it; if the word is rude, vulgar or slang, the Russian translation must be equally rude, vulgar or slang"
                  },
            "explanation" : {
            "prompt" : "less than 2 sentences: register, nuance that distinguishes it from synonyms, in which context used",
            "rules":""
            },
            "image prompt" : {
            "prompt" : "short description of the scnene in english for image generation: 'a cool cat looking professional'",
            "rules":"- For the IMAGE_PROMPT line, provide 2-4 simple, concrete English keywords describing the word.  Do NOT write full sentences, do NOT use stop-words (a, the, in, on, with), and do NOT use quality words (4k, photorealistic).Examples:Word: "peach" -> IMAGE_PROMPT: ripe peach tableWord: "danger" -> IMAGE_PROMPT: danger warning signWord: "negotiate" -> IMAGE_PROMPT: business handshake meeting"
            },
            
        }

    },
{
        "type": "chinese-easy",
        "front": {
            "prompt": "exactly what the user sent — word, phrase, or full sentence in chinese language",
            "rules": "- If the user sends a single word: follow the standard flashcard format, - If the user sends a phrase or full sentence: put the entire input on FRONT as-is,"
                  },
        "back": {
            "synonyms": {
            "prompt": "2-3 synonyms or similar phrases in chinese language",
            "rules": "- Synonyms must closely match the word's core meaning, - If the word has multiple meanings, use all of them"
                  },
            "sentence" : {
            "prompt": "easy sentence with ____ replacing the key word or phrase in chinese language",
            "rules": "- Sentence must be 4–6 words total (including prepositions) - Sentence must clearly reveal the word's meaning through context, - Replace the target word or phrase with ____"
                  },
            "translation" : {
            "prompt": "English translation, maximally close in meaning — including colloquial or vulgar equivalents if they convey the meaning more precisely",
            "rules": "- Translation must reflect the true meaning as closely as possible — do not sanitize or soften it; if the word is rude, vulgar or slang, the Russian translation must be equally rude, vulgar or slang"
                  },
            "character explanation" : {
            "prompt" : "if user imput contains multiple characters provide translation for each of them, if contains only one give translation only for this one",
            "rules":"itranslation should be very short"
            },
            "similar characters" : {
            "prompt" : "give 2-3 words that use similar characters and provide translation for them",
            "rules":"in format word-english translation"
            },
            "image prompt" : {
            "prompt" : "short description of the scnene in english for image generation: 'a cool cat looking professional'",
            "rules":"- For the IMAGE_PROMPT line, provide 2-4 simple, concrete English keywords describing the word.  Do NOT write full sentences, do NOT use stop-words (a, the, in, on, with), and do NOT use quality words (4k, photorealistic).Examples:Word: "peach" -> IMAGE_PROMPT: ripe peach tableWord: "danger" -> IMAGE_PROMPT: danger warning signWord: "negotiate" -> IMAGE_PROMPT: business handshake meeting"
            },
            
        }

    },

]