import json
from typing import List, Dict, Optional

def load_json_data(file_path: str) -> Dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def query_mal_bible_json(book_name: str, chapter: int, start_verse: Optional[int] = None, end_verse: Optional[int] = None) -> List[Dict[str, str]]:
    """
    Fetches verses from the Mal1910.json file based on the book name, chapter, and optional verse range.
    
    Args:
        book_name (str): Name of the book (e.g., "Genesis").
        chapter (int): Chapter number.
        start_verse (Optional[int]): Starting verse number (inclusive). Defaults to None.
        end_verse (Optional[int]): Ending verse number (inclusive). Defaults to None.
    
    Returns:
        List[Dict[str, str]]: A list of dictionaries containing 'verse' and 'text' for each verse.
    """
    # Load the JSON data
    data = load_json_data('database/Mal1910.json')
    verses = []
    
    # Debug: Print the structure of the loaded data
    print("Loaded JSON data structure:", type(data))
    if isinstance(data, dict):
        print("Keys in the dictionary:", data.keys())
    
    # Dictionary to map Malayalam book names to their English equivalents
    malayalam_to_english = {
        "ഉല്പത്തി": "Genesis", "പുറപ്പാട്": "Exodus", "ലേവ്യപുസ്തകം": "Leviticus", "സംಖ್ಯാപുസ്തകം": "Numbers", 
        "ആവർത്തനം": "Deuteronomy", "യോശുവ": "Joshua", "ന്യായാധിപന്മാർ": "Judges", "രൂത്ത്": "Ruth",
        "1 ശമൂവേൽ": "I Samuel", "2 ശമൂവേൽ": "II Samuel", "1 രാജാക്കന്മാർ": "I Kings", "2 രാജാക്കന്മാർ": "II Kings",
        "1 ദിനവൃത്താന്തം": "I Chronicles", "2 ദിനവൃത്താന്തം": "II Chronicles", "എസ്രാ": "Ezra", "നെഹെമ്യാവു": "Nehemiah",
        "എസ്ഥേർ": "Esther", "ഇയ്യോബ്": "Job", "സങ്കീർത്തനങ്ങൾ": "Psalms", "സദൃശ്യവാക്യങ്ങൾ": "Proverbs",
        "സഭാപ്രസംഗി": "Ecclesiastes", "ഉത്തമഗീതം": "Song of Solomon", "യേശയ്യാവു": "Isaiah", "യിരെമ്യാവു": "Jeremiah",
        "വിലാപങ്ങൾ": "Lamentations", "യേഹേസ്കേൽ": "Ezekiel", "ദാനിയേൽ": "Daniel", "ഹോശേയ": "Hosea", "യോവേൽ": "Joel",
        "ആമോസ്": "Amos", "ഓബദ്യാവു": "Obadiah", "യോനാ": "Jonah", "മീഖാ": "Micah", "നാഹൂം": "Nahum",
        "ഹബക്കൂക്ക്": "Habakkuk", "സെഫന്യാവു": "Zephaniah", "ഹഗ്ഗായി": "Haggai", "സെഖർയ്യാവു": "Zechariah",
        "മലാഖി": "Malachi", "മത്തായി": "Matthew", "മർക്കോസ്": "Mark", "ലൂക്കോസ്": "Luke", "യോഹന്നാൻ": "John",
        "പ്രവൃത്തികൾ": "Acts", "റോമർ": "Romans", "1 കൊരിന്ത്യർ": "I Corinthians", "2 കൊരിന്ത്യർ": "II Corinthians",
        "ഗലാത്യർ": "Galatians", "എഫേസ്യർ": "Ephesians", "ഫിലിപ്പിയർ": "Philippians", "കൊലോസ്യർ": "Colossians",
        "1 തെസ്സലോനിക്ക്യർ": "I Thessalonians", "2 തെസ്സലോനിക്ക്യർ": "II Thessalonians", "1 തിമോത്തെയോസ്": "I Timothy",
        "2 തിമോത്തെയോസ്": "II Timothy", "തീത്തൊസ്": "Titus", "ഫിലേമോൻ": "Philemon", "എബ്രായർ": "Hebrews",
        "യാക്കോബ്": "James", "1 പത്രോസ്": "I Peter", "2 പത്രോസ്": "II Peter", "1 യോഹന്നാൻ": "I John",
        "2 യോഹന്നാൻ": "II John", "3 യോഹന്നാൻ": "III John", "യൂദാ": "Jude", "വെളിപ്പാട്": "Revelation of John"
    }

    # Check if the book name is in Malayalam and find its English equivalent
    if book_name in malayalam_to_english:
        book_name = malayalam_to_english[book_name]

    # Access the 'books' key
    if 'books' not in data:
        print("Error: 'books' key not found in JSON data.")
        return verses
    
    # Iterate through the books
    for book in data['books']:
        if book['name'] == book_name:
            print(f"Book found: {book['name']}")  # Debug print
            # Iterate through the chapters
            for chap in book.get('chapters', []):
                if chap['chapter'] == chapter:
                    # print(f"Chapter found: {chap['chapter']}")  # Debug print
                    # Iterate through the verses
                    for verse in chap.get('verses', []):
                        verse_num = verse['verse']
                        # Check if the verse is within the specified range
                        if (start_verse is None or verse_num >= start_verse) and (end_verse is None or verse_num <= end_verse):
                            verses.append({'verse': verse_num, 'text': verse['text']})
                            # print(f"Added verse: {verse_num} - {verse['text']}")  # Debug print
                    break  # Exit after finding the correct chapter
            break  # Exit after finding the correct book
    
    # Debugging output
    if not verses:
        print(f"No verses found for {book_name} Chapter {chapter}.")
    else:
        print(f"Found {len(verses)} verses for {book_name} Chapter {chapter}.")
    
    return verses

def get_books() -> Dict[str, List[str]]:
    """
    Displays Old Testament and New Testament books without fetching from the Mal1910.json file.
    """
    old_testament_books = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
        "I Samuel", "II Samuel", "I Kings", "II Kings", "I Chronicles", "II Chronicles", "Ezra", "Nehemiah",
        "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
        "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
        "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"
    ]
    
    new_testament_books = [
        "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "I Corinthians", "II Corinthians",
        "Galatians", "Ephesians", "Philippians", "Colossians", "I Thessalonians", "II Thessalonians",
        "I Timothy", "II Timothy", "Titus", "Philemon", "Hebrews", "James", "I Peter", "II Peter",
        "I John", "II John", "III John", "Jude", "Revelation of John"
    ]
    
    books = {'Old Testament': old_testament_books, 'New Testament': new_testament_books}
    return books

def get_chapters(book_name: str) -> Dict[int, List[str]]:
    """
    Fetches all chapters and their verses for a given book from the Mal1910.json file.
    """
    data = load_json_data('database/Mal1910.json')
    chapters = {}
    
    for book in data['books']:
        if book['name'] == book_name:
            for chap in book['chapters']:
                chapter_num = chap['chapter']
                verses = []
                for verse in chap['verses']:
                    verse_text = f'<span class="verse-num">{verse["verse"]}</span> {verse["text"]}'
                    verses.append(verse_text)
                chapters[chapter_num] = verses
    return chapters

if __name__ == "__main__":
    # Sample query to test the function
    verses = query_mal_bible_json('Genesis', 1, 1, 10)
    for verse in verses:
        print(f"Verse {verse['verse_num']}: {verse['text']}")