# FILE: groq_devotionals_ko.py

import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

load_dotenv()  # Load environment variables from .env file

def get_bible_verse_ko(name, connected_theme):
    prompt = PromptTemplate(
        input_variables=["name", "connected_theme"],
        template="""
        다음 묵상을 위한 적절한 성경 구절을 찾으세요:
        이름: {name}
        연결된 주제: {connected_theme}
        {name}이(가) 어떻게 극복되었는지를 설명하는 300단어의 짧은 성경 구절과 그 구절에서 영감을 받은 짧은 기도를 제공하세요.
        정확히 이 형식으로 응답하세요, 한글 스크립트로:
        구절 텍스트: [구절 참조 없이 구절 텍스트만]
        구절 참조: [구절 참조만]
        짧은 이야기: [짧은 이야기만]
        짧은 기도: [구절에서 영감을 받은 짧은 기도]
        """
    )
    # print(name, connected_theme)
    # print("inside groq devotional")
    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="mixtral-8x7b-32768")
    chain = prompt | llm
    response = chain.invoke({"name": name, "connected_theme": connected_theme})
    print(response)

     # Parse the response to extract the verse text, reference, and context
    lines = str(response.content if hasattr(response, 'content') else response).split('\n')
    verse_data = {}
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            verse_data[key.strip().lower().replace(' ', '_')] = value.strip()

    verse_text = verse_data.get('구절_텍스트', '구절 텍스트를 다시 시도하세요')
    verse_reference = verse_data.get('구절_참조', '구절 참조를 찾을 수 없습니다')
    short_story = verse_data.get('짧은_이야기', '이야기를 다시 시도하세요')
    short_prayer = verse_data.get('짧은_기도', '기도를 다시 시도하세요')
    print("short story extracted is:", short_story)
    return {
        'text': verse_text,
        'reference': verse_reference,
        'short_story': short_story,
        'prayer': short_prayer
    }
    
 