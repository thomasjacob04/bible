import requests

API_URL = "https://api-inference.huggingface.co/models/facebook/mbart-large-50-many-to-many-mmt"
headers = {"Authorization": "Bearer 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"}

def mbart(text: str, src_lang: str, tgt_lang: str) -> str:
    payload = {
        "inputs": text,
        "parameters": {
            "src_lang": src_lang,
            "tgt_lang": tgt_lang
        }
    }
    print("\n *** MBART START for input ", text)
    response = requests.post(API_URL, headers=headers, json=payload)
    response_data = response.json()
    if isinstance(response_data, list) and len(response_data) > 0:
        print("\n *** MBART RESPONSE from KoBART.py ******* for input ", text, "output is", response_data[0])
        return response_data[0].get("translation_text", "")
    else:
        return ""

# def test_mbart():
#     text = "Hello, how are you?"
#     src_lang = "en_XX"
#     tgt_lang = "ko_KR"
#     translated_text = mbart(text, src_lang, tgt_lang)
#     print(f"Original text: {text}")
#     print(f"Translated text: {translated_text}")

# if __name__ == "__main__":
#     test_mbart()