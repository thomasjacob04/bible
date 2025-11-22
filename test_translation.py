import requests


def translate_text_nllb(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translates the given text using the NLLB API.
    
    Args:
        text (str): The input text to translate.
        source_lang (str): The source language code.
        target_lang (str): The target language code.
    
    Returns:
        str: The translated text.
    """
    url = 'https://winstxnhdw-nllb-api.hf.space/api/v4/translator'
    params = {
        'text': text,
        'source': source_lang,
        'target': target_lang
    }
    response = requests.get(url, params=params)
    response_data = response.json()
    
    # Print the response data for debugging
    print("Response Data:", response_data)
    
    if 'result' in response_data:
        return response_data['result']
    else:
        raise KeyError(f"'result' not found in response: {response_data}")

def test_translation():
    english_text = """2. 설명: - 여호와 (주) 가 여호수아 (주) 에게 "나는 여리고 (주) 와 그 왕과 그 용병들을 네 손에 주었느니라".라고 하신 것. - 여리고는 시 우트 왕국의 도시이며, 이 도시는 이스라엘 땅을 빼앗은 적국이었다. - 여호와 (주) 는 여호수아 (주) 에게 이 도시와 그 왕과 그 용병들을 승리하게 해 줄 것을 알려 주면서, 그분의 능력과 지혜를 나타내고 있다. - 여호수아는 하나님의 말씀을 믿고 순종하고, 이기는 성공한다."""
    source_lang = "kor_Hang"
    target_lang = "eng_Latn"


    translated_text = translate_text_nllb(english_text, source_lang, target_lang)
    print(f"Original text: {english_text}")
    print(f"Translated text: {translated_text}")


if __name__ == "__main__":
    test_translation()