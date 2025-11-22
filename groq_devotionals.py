# FILE: groq_integration.py

import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

load_dotenv()  # Load environment variables from .env file

def get_bible_verse(name, connected_theme):
    prompt = PromptTemplate(
        input_variables=["name", "connected_theme"],
        template="""
        Find an appropriate Bible verse for the following devotional:
        Name: {name}
        Connected Theme: {connected_theme}
        Provide the verse text, verse reference, short passage of 300 words from the bible illustrating how the following context {name} was overcome and a short prayer inspired by the verse.
        Respond in this exact format, in English script:
        Verse Text: [only the verse text, without the verse reference]
        Verse Reference: [only the verse reference]
        Short Story: [only the short story]
        Short Prayer: [a short prayer inspired by the verse]
        """
    )
    # print(name, connected_theme)
    # print("inside groq devotional")
    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")
    chain = prompt | llm
    response = chain.invoke({"name": name, "connected_theme": connected_theme})
    # print(response)

     # Parse the response to extract the verse text, reference, and context
    lines = str(response.content if hasattr(response, 'content') else response).split('\n')
    verse_data = {}
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            verse_data[key.strip().lower().replace(' ', '_')] = value.strip()

    verse_text = verse_data.get('verse_text', 'Refresh and seek again please')
    verse_reference = verse_data.get('verse_reference', 'No verse reference found')
    short_story = verse_data.get('short_story', 'Seek again for the story')
    short_prayer = verse_data.get('short_prayer', 'Seek again for the prayer')
    # print("short story extracted is:", short_story)
    return {
        'text': verse_text,
        'reference': verse_reference,
        'short_story': short_story,
        'prayer': short_prayer
    }
    
 