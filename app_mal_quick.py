import os
import re
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from typing import Optional, List, Dict
from dataclasses import dataclass
from query_mal1920 import query_mal_bible_json  # Import the query_mal_bible_json function
from flask import Flask, session, request, redirect, url_for, render_template, jsonify

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@dataclass
class BibleReference:
    book: str
    chapter: int
    start_verse: Optional[int] = None
    end_verse: Optional[int] = None

def step1_create_reference_parser_chain():
    print("STEP 1")
    """
    1. Creates the first chain that takes natural language input and returns structured Bible references.
    """
    prompt_template = PromptTemplate(
        input_variables=["user_input"],
        template="""Parse the following Bible reference into a structured format.
If a chapter is mentioned without verses, assume the entire chapter is requested.
If a verse range is given (e.g., verses 5-9), include both start and end verses.
There may be misspelled book names or the user may be unaware of the exact book name, so please suggest the closest match from this list:
        "ഉല്പത്തി", "പുറപ്പാട്", "ലേവ്യപുസ്തകം", "സംഖ്യകൾ", "ആവർത്തനം", "യോശുവ", "ന്യായാധിപന്മാർ", "റൂത്ത്",
        "1 ശമൂവേൽ", "2 ശമൂവേൽ", "1 രാജാക്കന്മാർ", "2 രാജാക്കന്മാർ", "1 ദിനവൃത്താന്തം", "2 ദിനവൃത്താന്തം", "എസ്രാ", "നെഹെമ്യാവു",
        "എസ്ഥേർ", "ഇയ്യോബ്", "സങ്കീർത്തനങ്ങൾ", "സദൃശ്യവാക്യങ്ങൾ", "സഭാപ്രസംഗി", "ഉത്തമഗീതം", "യേശയ്യാവു", "യിരെമ്യാവു",
        "വിലാപങ്ങൾ", "യേഹേസ്കേൽ", "ദാനിയേൽ", "ഹോശേയ", "യോവേൽ", "ആമോസ്", "ഓബദ്യാവു", "യോനാ", "മീഖാ",
        "നാഹൂം", "ഹബക്കൂക്ക്", "സെഫന്യാവു", "ഹഗ്ഗായി", "സെഖർയ്യാവു", "മലാഖി", "മത്തായി", "മർക്കോസ്", "ലൂക്കാ", "യോഹന്നാൻ", "പ്രവൃത്തികൾ", "റോമർ", "1 കൊരിന്ത്യർ", "2 കൊരിന്ത്യർ",
        "ഗലാത്യർ", "എഫേസ്യർ", "ഫിലിപ്പിയർ", "കൊലോസ്യർ", "1 തെസ്സലോണിക്ക്യർ", "2 തെസ്സലോണിക്ക്യർ",
        "1 തിമോത്തെയൊസ്", "2 തിമോത്തെയൊസ്", "തീത്തൊസ്", "ഫിലേമോൻ", "എബ്രായർ", "യാക്കോബ്", "1 പത്രൊസ്", "2 പത്രൊസ്",
        "1 യോഹന്നാൻ", "2 യോഹന്നാൻ", "3 യോഹന്നാൻ", "യൂദാ", "വെളിപ്പാട്".

User's reference: {user_input}

Respond in this exact format, in English script:
BOOK: [only the book name in the English version]
CHAPTER: [number or 'None' if not specified]
START_VERSE: [number or 'None' if entire chapter]
END_VERSE: [number or 'None' if single verse or entire chapter]
"""
    )
    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="mixtral-8x7b-32768")
    chain = prompt_template | llm
    return chain

def step2_parse_bible_reference(user_input: str) -> BibleReference:
    print("STEP 2")
    """
    2. Uses LLM to parse natural language input into structured format.
    This is where we first use Groq to interpret the user's request.
    """
    chain = step1_create_reference_parser_chain()
    response = chain.invoke({"user_input": user_input})

    # Print the LLM's interpretation
    # print("\nYou searched in Malayalam:")
    # print(response.content if hasattr(response, 'content') else response)
    # print("\n" + "-"*50 + "\n")

    # Extract the structured data from the response
    lines = str(response.content if hasattr(response, 'content') else response).split('\n')
    ref_data = {}
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            ref_data[key] = value

    # Handle the case where CHAPTER is 'None'
    chapter_str = ref_data.get('CHAPTER', '0').strip()
    if chapter_str == 'None':
        raise ValueError("Chapter not specified in the reference.")

    parsed_reference = BibleReference(
        book=ref_data.get('BOOK', '').strip(),
        chapter=int(chapter_str),
        start_verse=int(ref_data.get('START_VERSE', '0')) if ref_data.get('START_VERSE') != 'None' else None,
        end_verse=int(ref_data.get('END_VERSE', '0')) if ref_data.get('END_VERSE') != 'None' else None
    )

    #print(f"Parsed reference: {parsed_reference}")
    return parsed_reference

def clean_html(raw_html: str) -> str:
    """
    Removes HTML tags from the given raw HTML string.
    """
    clean_re = re.compile('<.*?>')
    return re.sub(clean_re, '', raw_html)

def parse_bible_verses(raw_html: str) -> List[Dict[str, str]]:
    """
    Parses the HTML content of Bible verses and returns a list of dictionaries with verse number and text.
    """
    clean_re = re.compile('<.*?>')
    verses = []
    for match in re.finditer(r'<span data-number="(\d+)"[^>]*>(.*?)</span>(.*?)(?=<span data-number|$)', raw_html):
        verse_num = match.group(1)
        verse_text = re.sub(clean_re, '', match.group(3)).strip()
        print(f"Captured verse: {verse_num} - {verse_text}")  # Debugging statement
        verses.append({'verse_num': verse_num, 'text': verse_text})
    return verses

def fetch_verses_from_db(ref: BibleReference) -> List[Dict[str, str]]:
    """
    Fetches verses from the Mal1910.json file.
    """
    verses = query_mal_bible_json(ref.book, ref.chapter, ref.start_verse, ref.end_verse)
    return verses

def step3_fetch_bible_verses_mal(ref: BibleReference, api_key: str) -> List[Dict[str, str]]:
    print("STEP 3")
    """
    3. Fetches the actual Bible verses from the Mal1910.json using the structured reference.
    """
    verses = fetch_verses_from_db(ref)
    return verses

def step5_process_bible_reference_mal_quick(user_input: str, bible_api_key: str) -> Dict[str, str]:
    print("STEP 5")
    """
    5. Main function that orchestrates the entire process:
       - First uses Groq to interpret the reference
       - Then fetches the verses
    """
    try:
        # Step 1: Parse the natural language reference
        print("STEP 1")
        reference = step2_parse_bible_reference(user_input)
    except ValueError as e:
        return {"error": str(e)}

    # Step 2: Fetch the verse(s)
    print("STEP 2")
    verses = step3_fetch_bible_verses_mal(reference, bible_api_key)
    if not verses:
        return {"error": f"Failed to fetch chapter {reference.chapter} of {reference.book}. It may not exist."}

    # Print fetched verses for debugging
    print(f"Fetched verses: {verses}")

    # Step 3: Display verses and get explanation
    print("STEP 3")
    all_text = ""
    for verse in verses:
        all_text += f"{verse['text']}\n"  # Only append the verse text, not the verse number
    print(f"all_text from step 3 in app_mal_quick is: {all_text}")

    requested_reference = f"{reference.book} {reference.chapter}"
    if reference.start_verse is not None:
        requested_reference += f":{reference.start_verse}"
        if reference.end_verse is not None and reference.end_verse != reference.start_verse:
            requested_reference += f"-{reference.end_verse}"

    return {
        "interpretation": f"You searched for: {user_input}",
        "requested_reference": requested_reference,
        "retrieved_passages": verses,
        "all_text": all_text,
    }

# This is the entry point of the script when run directly
if __name__ == "__main__":
    # Set up our API key for the Bible API
    bible_api_key = "your_bible_api_key"

    # Get user input
    print("Enter a Bible reference (e.g., 'John chapter 3 verse 16' or 'John 3:16-18' or 'Genesis 1'):")
    user_input = input("> ")

    # Process the reference
    step5_process_bible_reference_mal_quick(user_input, bible_api_key)