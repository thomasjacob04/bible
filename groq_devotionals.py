# FILE: groq_integration.py

import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

load_dotenv()  # Load environment variables from .env file

def get_bible_verse(name, connected_theme):
    """
    Generate a Bible verse and devotional content using Groq LLM.

    Args:
        name: The devotional topic name (e.g., "Depression & Loneliness")
        connected_theme: The connected spiritual theme (e.g., "Hope & Perseverance")

    Returns:
        dict: Contains 'text', 'reference', 'short_story', and 'prayer' keys
    """
    try:
        # Check if API key is available
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("ERROR: GROQ_API_KEY not found in environment variables")
            raise ValueError("GROQ_API_KEY is not configured")

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

        print(f"Generating devotional for: {name} with theme: {connected_theme}")

        llm = ChatGroq(api_key=api_key, model="llama-3.3-70b-versatile")
        chain = prompt | llm
        response = chain.invoke({"name": name, "connected_theme": connected_theme})

        print(f"Received response from LLM")

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

        print(f"Successfully parsed devotional content")

        return {
            'text': verse_text,
            'reference': verse_reference,
            'short_story': short_story,
            'prayer': short_prayer
        }

    except Exception as e:
        print(f"ERROR in get_bible_verse: {str(e)}")
        import traceback
        traceback.print_exc()

        # Return fallback content
        return {
            'text': 'The Lord is close to the brokenhearted and saves those who are crushed in spirit.',
            'reference': 'Psalm 34:18',
            'short_story': f'When facing {name}, remember that God is always near. He understands your struggles and offers comfort in times of need. Trust in His presence and lean on His strength.',
            'prayer': f'Dear Lord, in this time of {name.lower()}, I seek Your comfort and guidance. Help me to trust in Your plan and find peace in Your presence. Amen.'
        }
    
 