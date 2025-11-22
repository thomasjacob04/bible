import requests
import os
import re
import csv
import json
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from typing import Optional, List, Dict
from dataclasses import dataclass
from query_kjv import query_kjv_db  # Import the query_kjv_db function
from flask import session  # Add this import at the top of the file if using Flask
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

@dataclass
class BibleReference:
    book: str
    chapter: int
    start_verse: Optional[int] = None
    end_verse: Optional[int] = None

def step1_create_reference_parser_chain():
    """
    1. Creates the first chain that takes natural language input and returns structured Bible references.
    """
    prompt_template = PromptTemplate(
        input_variables=["user_input"],
        template="""Parse the following Bible reference into a structured format.
If a chapter is mentioned without verses, assume the entire chapter is requested.
If a verse range is given (e.g., verses 5-9), include both start and end verses.
There may be misspelled book names or the user may be unaware of the exact book name, so please suggest the closest match. 
Convert numeric prefixes to Roman numerals:
- '1' or 'First' or 'I' -> 'I'
- '2' or 'Second' or 'II' -> 'II'
- '3' or 'Third' or 'III' -> 'III'
For example:
- "2 Corinthians" should be converted to "II Corinthians"
- "1 John" should be converted to "I John"
- "3 John" should be converted to "III John"
if revelations book is mentioned, consider it as 'Revelation of John'.
if psalm is mentioned, consider it as 'Psalms'.
If you are going to reference any specific verses from the bible, use these exact book names only as a single word:
       "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
        "I Samuel", "II Samuel", "I Kings", "II Kings", "I Chronicles", "II Chronicles", "Ezra", "Nehemiah",
        "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
        "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
        "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "I Corinthians", "II Corinthians",
        "Galatians", "Ephesians", "Philippians", "Colossians", "I Thessalonians", "II Thessalonians",
        "I Timothy", "II Timothy", "Titus", "Philemon", "Hebrews", "James", "I Peter", "II Peter",
        "I John", "II John", "III John", "Jude", "Revelation of John"
User's reference: {user_input}

Respond in this exact format strictly:
BOOK: [only the book name]
CHAPTER: [number or 'None' if not specified]
START_VERSE: [number or 'None' if entire chapter]
END_VERSE: [number or 'None' if single verse or entire chapter]
EXPLANATION: [explain in natural language what was requested]"""
    )
    
    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")
    chain = prompt_template | llm
    return chain

def step2_parse_bible_reference(user_input: str) -> BibleReference:
    """
    2. Uses LLM to parse natural language input into structured format.
    This is where we first use Groq to interpret the user's request.
    """
    chain = step1_create_reference_parser_chain()
    response = chain.invoke({"user_input": user_input})
    
    # Print the LLM's interpretation
    print("\nYou searched:")
    print(response.content if hasattr(response, 'content') else response)
    print("\n" + "-"*50 + "\n")
    
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

    return BibleReference(
        book=ref_data.get('BOOK', '').strip(),
        chapter=int(chapter_str),
        start_verse=int(ref_data.get('START_VERSE', '0')) if ref_data.get('START_VERSE') != 'None' else None,
        end_verse=int(ref_data.get('END_VERSE', '0')) if ref_data.get('END_VERSE') != 'None' else None
    )

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
    Fetches verses from the KJV.db SQLite database.
    """
    verses = query_kjv_db(ref.book, ref.chapter, ref.start_verse, ref.end_verse)
    return verses

def step3_fetch_bible_verses(ref: BibleReference, api_key: str) -> List[Dict[str, str]]:
    """
    3. Fetches the actual Bible verses from the KJV.db using the structured reference.
    """
    verses = fetch_verses_from_db(ref)
    print(f"Retrieved verses: {verses}")
    return verses

def step4_create_explanation_chain():
    """
    4. Creates the second chain that explains verses and suggests related passages.
    """
    prompt_template = PromptTemplate(
        input_variables=["verse_reference", "verse_text"],
        template="""Analyze this Bible passage:
Reference: {verse_reference}
Text: {verse_text}

Please provide in this format:
1. Key themes: short tags of 1-3 words per tag in csv format, respond exactly in this format: "Injustice, Loss of Inheritance, Captivity of the Israelites, Destruction".
2. Explanation: Explain the meaning of the passage in its original historical and cultural context, focusing on how its audience (Israel/Judah/Roman-era Christians) would have understood it. Highlight any political, religious, or social tensions at play, and connect it to broader biblical themes like covenant, exile, or Messiah. Keep it concise but insightful.
3. Related Bible verses include: 2-3 related Bible verses that share similar themes or messages (include brief explanations of why they're related).
4. Background: Year, location and cultural context of the event, include the modern names too. 
5. Locations: Identify the specific place(s) mentioned in the passage, and provide the full name(s) of the place in a comma separated format without any extra text.
Response:"""
    )
    
    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")
    chain = prompt_template | llm
    return chain

def step5_process_bible_reference(user_input: str, bible_api_key: str) -> Dict[str, str]:
    """
    5. Main function that orchestrates the entire process:
       - First uses Groq to interpret the reference
       - Then fetches the verses
       - Finally uses Groq again to analyze and explain
    """
    try:
        # Step 1: Parse the natural language reference
        reference = step2_parse_bible_reference(user_input)
    except ValueError as e:
        return {"error": str(e)}
    
    def search_csv(reference, language):
        print(f"Searching CSV for reference whtin app py : {reference}")  # Debugging statement
        with open('database/queries.csv', mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == reference and row[1] == language:
                    try:
                        retrieved_passages = json.loads(row[2])
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
                        continue
                    print(f"Found reference in CSV: {row[0]}")  # Debugging statement
                    return {
                        "requested_reference": row[0],
                        "language": row[1],
                        "retrieved_passages": retrieved_passages,
                        "analysis": row[3],
                        "explanation": row[4],
                        "related_verses": row[5]
                    }
        print("Reference not found in CSV")  # Debugging statement
        return None

    requested_reference = f"{reference.book} {reference.chapter}"
    if reference.start_verse is not None:
        requested_reference += f":{reference.start_verse}"
        if reference.end_verse is not None and reference.end_verse != reference.start_verse:
            requested_reference += f"-{reference.end_verse}"

    # Search the CSV file for the reference
    response = search_csv(requested_reference, 'en')
    if response:
        return response

    # Step 2: Fetch the verse(s)
    verses = step3_fetch_bible_verses(reference, bible_api_key)
    if not verses:
        return {"error": f"Failed to fetch chapter {reference.chapter} of {reference.book}. It may not exist."}
    
    # Step 3: Display verses and get explanation
    all_text = ""
    for verse in verses:
        all_text += f"{verse['text']}\n"  # Only append the verse text, not the verse number
    print(all_text)
    
    # Determine the verse reference for the explanation
    verse_reference = f"{reference.book} {reference.chapter}"
    if reference.start_verse is not None:
        verse_reference += f":{reference.start_verse}"
        if reference.end_verse is not None and reference.end_verse != reference.start_verse:
            verse_reference += f"-{reference.end_verse}"
    
    # Step 4: Get the explanation and related verses
    chain = step4_create_explanation_chain()
    explanation = chain.invoke({
        "verse_reference": verse_reference,
        "verse_text": all_text
    })
    
    # Extract the related Bible verses section
    explanation_text = explanation.content if hasattr(explanation, 'content') else explanation
    related_verses_start = explanation_text.find("Related Bible verses include:")
    related_verses = explanation_text[related_verses_start:] if related_verses_start != -1 else ""

    explanation_start = explanation_text.find("explanation")
    explanation = explanation_text[explanation_start:related_verses_start].strip() if explanation_start != -1 and related_verses_start != -1 else ""

    requested_reference = f"{reference.book} {reference.chapter}"
    if reference.start_verse is not None:
        requested_reference += f":{reference.start_verse}"
        if reference.end_verse is not None and reference.end_verse != reference.start_verse:
            requested_reference += f"-{reference.end_verse}"

    print(f"Requested reference: {requested_reference}")
    # Write the query and results to a CSV file
    if explanation:
        with open('database/queries.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([requested_reference, "en", json.dumps(verses), explanation_text[:explanation_start].strip() if explanation_start != -1 else explanation_text, explanation, related_verses])
            # print(f"Wrote to CSV: {requested_reference}")  # Debugging statement

    # Translate analysis, explanation, and related verses to Korean and Malayalam if the session language is set to Korean or Malayalam
    analysis_ko = ""
    explanation_ko = ""
    related_verses_ko = ""
    analysis_ml = ""
    explanation_ml = ""
    related_verses_ml = ""

    if session.get('lang') == 'ko':
        analysis_ko = translate_text_excluding_verses(explanation_text[:explanation_start].strip() if explanation_start != -1 else explanation_text, "Korean")
        print(f"Analysis (Korean): {analysis_ko}")

        explanation_ko = translate_text_excluding_verses(explanation, "Korean")
        print(f"Explanation (Korean): {explanation_ko}")
        related_verses_ko = translate_text_excluding_verses(related_verses.strip(), "Korean")
    elif session.get('lang') == 'ml':
        analysis_ml = translate_text_excluding_verses(explanation_text[:explanation_start].strip() if explanation_start != -1 else explanation_text, "Malayalam")
        explanation_ml = translate_text_excluding_verses(explanation[:related_verses_start].strip() if related_verses_start != -1 else explanation, "Malayalam")
        related_verses_ml = translate_text_excluding_verses(related_verses.strip(), "Malayalam")

    return {
        "interpretation": f"You searched for: {user_input}",
        "requested_reference": requested_reference,
        "retrieved_passages": verses,
        "analysis": explanation_text[:explanation_start].strip() if explanation_start != -1 else explanation_text,
        "related_verses": related_verses.strip(),
        "explanation": explanation,
        "analysis_ko": analysis_ko,
        "explanation_ko": explanation_ko,
        "related_verses_ko": related_verses_ko,
        "analysis_ml": analysis_ml,
        "explanation_ml": explanation_ml,
        "related_verses_ml": related_verses_ml
    }

def create_translation_chain():
    """
    Creates a chain to translate text from English to Korean or Malayalam, excluding Bible verses.
    """
    prompt_template = PromptTemplate(
        input_variables=["text", "target_language"],
        template="""
Translate the following text from English to {target_language} in the actual target script,
so if the target language is Korean, provide the text in Hangul script.
If a biblical verse including book name, chapter AND verse or verses is found, keep it unchanged in the translated text.

Text: {text}

Translated Text: [translated text with Bible verses unchanged]"""
    )
    
    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")
    chain = prompt_template | llm
    return chain

def translate_text_excluding_verses(text: str, target_language: str) -> str:
    """
    Translates the given text from English to the target language, excluding Bible verses.
    
    Args:
        text (str): The input text to translate.
        target_language (str): The target language for translation.
    
    Returns:
        str: The translated text with Bible verses excluded from translation.
    """
    # Regular expression to match Bible verses (e.g., "John 3:16", "Genesis 1:1-5")
    verse_pattern = re.compile(r'\b([1-3]?[A-Za-z]+) (\d+):(\d+(-\d+)?)\b')
    
    # Find all Bible verses in the text
    verses = verse_pattern.findall(text)
    
    # Replace Bible verses with placeholders
    placeholder_text = text
    for i, verse in enumerate(verses):
        placeholder = f"__VERSE_{i}__"
        placeholder_text = placeholder_text.replace(f"{verse[0]} {verse[1]}:{verse[2]}", placeholder)
    
    # Translate the text with placeholders using Groq
    chain = create_translation_chain()
    response = chain.invoke({"text": placeholder_text, "target_language": target_language})
    translated_text = response.content if hasattr(response, 'content') else response
    
    # Replace placeholders with original Bible verses
    for i, verse in enumerate(verses):
        placeholder = f"__VERSE_{i}__"
        original_verse = f"{verse[0]} {verse[1]}:{verse[2]}"
        translated_text = translated_text.replace(placeholder, original_verse)
    
    return translated_text


def translate_biblical_text(text: str, target_language: str) -> str:
    """
    Translates the given biblical text from English to the target language, considering that book names from the Bible will be used often.
    
    Args:
        text (str): The input text to translate.
        target_language (str): The target language for translation.
    
    Returns:
        str: The translated text.
    """
    prompt_template = PromptTemplate(
        input_variables=["text", "target_language"],
        template="""
Translate the given biblical text to {target_language} in the actual target script, considering that book names from the Bible will be used often
so if the target language is Korean, provide the text in Hangul script.
Return only the translated text, with no additional explanations or formatting.

Text: {text}

Translated Text: [translated text with no additional information]"""
    )
    
    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")
    translated_text = prompt_template | llm
    return translated_text


# This is the entry point of the script when run directly
if __name__ == "__main__":
    # Set up our API key for the Bible API
    bible_api_key = os.getenv("BIBLE_API_KEY")

    # Get user input
    print("Enter a Bible reference (e.g., 'John chapter 3 verse 16' or 'John 3:16-18' or 'Genesis 1'):")
    user_input = input("> ")

    # Process the reference
    step5_process_bible_reference(user_input, bible_api_key)

