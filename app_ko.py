import requests
import os
import re
import csv
import json
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from typing import Optional, List, Dict
from dataclasses import dataclass
from query_korrv import query_korrv_db  # Import the query_korrv_db function
from flask import Flask, session, request, redirect, url_for, render_template, jsonify
from KoBART import mbart
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

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
        "창세기", "출애굽기", "레위기", "민수기", "신명기", "여호수아", "사사기", "룻기",
        "사무엘상", "사무엘하", "열왕기상", "열왕기하", "역대상", "역대하", "에스라", "느헤미야",
        "에스더", "욥기", "시편", "잠언", "전도서", "아가", "이사야", "예레미야",
        "예레미야 애가", "에스겔", "다니엘", "호세아", "요엘", "아모스", "오바댜", "요나", "미가",
        "나훔", "하박국", "스바냐", "학개", "스가랴", "말라기",     "마태복음", "마가복음", "누가복음", "요한복음", "사도행전", "로마서", "고린도전서", "고린도후서",
        "갈라디아서", "에베소서", "빌립보서", "골로새서", "데살로니가전서", "데살로니가후서",
        "디모데전서", "디모데후서", "디도서", "빌레몬서", "히브리서", "야고보서", "베드로전서", "베드로후서",
        "요한일서", "요한이서", "요한삼서", "유다서", "요한계시록".
if you see 요한, make it 요한복음.

User's reference: {user_input}

Respond in this exact format, in korean hangul script:
BOOK: [only the book name]
CHAPTER: [number or 'None' if not specified]
START_VERSE: [number or 'None' if entire chapter]
END_VERSE: [number or 'None' if single verse or entire chapter]
"""
    )
    # print(prompt_template)
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
    # print("\nYou searched in korean:")
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
    Fetches verses from the KorRV.db SQLite database.
    """
    verses = query_korrv_db(ref.book, ref.chapter, ref.start_verse, ref.end_verse)
    return verses

def step3_fetch_bible_verses(ref: BibleReference, api_key: str) -> List[Dict[str, str]]:
    print("STEP 3")
    """
    3. Fetches the actual Bible verses from the KorRV.db using the structured reference.
    """
    verses = fetch_verses_from_db(ref)
    return verses

def step4_create_explanation_chain():
    print("inside STEP 4")
    """
    4. Creates the second chain that explains verses and suggests related passages.
    """
    prompt_template = PromptTemplate(
        input_variables=["verse_reference", "verse_text"],
        template="""Analyze this Bible passage in korean:
Reference: {verse_reference}
Text: {verse_text}

Please provide in korean language, in hangul script only:
1. The main theme or themes of this passage
2. A detailed explanation of the meaning and significance
3. 2-3 related Bible verses that share similar themes or messages (include brief explanations of why they're related)

If you are going to reference any specific verses from the bible, use these book names:
     "창세기", "출애굽기", "레위기", "민수기", "신명기", "여호수아", "사사기", "룻기",
        "사무엘상", "사무엘하", "열왕기상", "열왕기하", "역대상", "역대하", "에스라", "느헤미야",
        "에스더", "욥기", "시편", "잠언", "전도서", "아가", "이사야", "예레미야",
        "예레미야 애가", "에스겔", "다니엘", "호세아", "요엘", "아모스", "오바댜", "요나", "미가",
        "나훔", "하박국", "스바냐", "학개", "스가랴", "말라기",     "마태복음", "마가복음", "누가복음", "요한복음", "사도행전", "로마서", "고린도전서", "고린도후서",
        "갈라디아서", "에베소서", "빌립보서", "골로새서", "데살로니가전서", "데살로니가후서",
        "디모데전서", "디모데후서", "디도서", "빌레몬서", "히브리서", "야고보서", "베드로전서", "베드로후서",
        "요한일서", "요한이서", "요한삼서", "유다서", "요한계시록".
for 요한, make it 요한복음.

Response:"""
    )

    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="mixtral-8x7b-32768")
    chain = prompt_template | llm
    return chain

def step5_process_bible_reference_ko(user_input: str, bible_api_key: str) -> Dict[str, str]:
    print("STEP 5")
    """
    5. Main function that orchestrates the entire process:
       - First uses Groq to interpret the reference
       - Then fetches the verses
       - Finally uses Groq again to analyze and explain
    """
    try:
        # Step 1: Parse the natural language reference
        print("STEP 1")
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
    response = search_csv(requested_reference, 'ko')
    if response:
        return response

    # Step 2: Fetch the verse(s)
    print("STEP 2")
    verses = step3_fetch_bible_verses(reference, bible_api_key)
    if not verses:
        return {"error": f"Failed to fetch chapter {reference.chapter} of {reference.book}. It may not exist."}

    # Print fetched verses for debugging
    print(f"Fetched verses: {verses}")

    # Step 3: Display verses and get explanation
    print("STEP 3")
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
    print("STEP 4 started")
    chain = step4_create_explanation_chain()
    explanation = chain.invoke({
        "verse_reference": verse_reference,
        "verse_text": all_text
    })

    # Extract the related Bible verses section
    explanation_text = explanation.content if hasattr(explanation, 'content') else explanation
    print(f"\nExplanation text after step 4 has processed: {explanation_text}")  # Debugging statement
    related_verses_start = explanation_text.find("3. ")
    related_verses = explanation_text[related_verses_start:] if related_verses_start != -1 else ""

    if "2. " not in explanation_text:
        explanation_text = "2. " + explanation_text
    explanation_start = explanation_text.find("2. ")
    explanation = explanation_text[explanation_start:related_verses_start].strip() if explanation_start != -1 and related_verses_start != -1 else ""

    print(f"Explanation: {explanation}")  # Debugging statement
    print(f"Related verses: {related_verses}")  # Debugging statement

    requested_reference = f"{reference.book} {reference.chapter}"
    if reference.start_verse is not None:
        requested_reference += f":{reference.start_verse}"
        if reference.end_verse is not None and reference.end_verse != reference.start_verse:
            requested_reference += f"-{reference.end_verse}"


    # Write the query and results to a CSV file
    if explanation:
        with open('database/queries.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([requested_reference, "ko", json.dumps(verses), explanation_text[:explanation_start].strip() if explanation_start != -1 else explanation_text, explanation, related_verses])
            print(f"Wrote to CSV: {requested_reference}")  # Debugging statement
 

    return {
        "interpretation": f"You searched for: {user_input}",
        "requested_reference": requested_reference,
        "retrieved_passages": verses,
        "analysis": explanation_text[:explanation_start].strip() if explanation_start != -1 else explanation_text,
        "related_verses": related_verses.strip(),
        "explanation": explanation,
    }

# This is the entry point of the script when run directly
if __name__ == "__main__":
    # Set up our API key for the Bible API
    bible_api_key = os.getenv("BIBLE_API_KEY")

    # Get user input
    print("Enter a Bible reference (e.g., 'John chapter 3 verse 16' or 'John 3:16-18' or 'Genesis 1'):")
    user_input = input("> ")

    # Process the reference
    step5_process_bible_reference_ko(user_input, bible_api_key)
