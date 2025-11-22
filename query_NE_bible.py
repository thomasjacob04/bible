import json
from typing import List, Dict, Optional

def load_json_data(file_path: str) -> Dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def query_ne_bible_json(book_name: str, chapter: int, start_verse: Optional[int] = None, end_verse: Optional[int] = None) -> List[Dict[str, str]]:
    """
    Fetches verses from the ERV-NE-SimpleJSON file.
    """
    data = load_json_data('database/ERV-NE-SimpleJSON')
    verses = []
    
    for book in data['osis'][0]['osisText'][0]['div']:
        if book['name']['_value'] == book_name:
            for chap in book['chapter']:
                if chap['cnumber'] == chapter:
                    for verse in chap['verse']:
                        verse_num = int(verse['vnumber'])
                        if (start_verse is None or verse_num >= start_verse) and (end_verse is None or verse_num <= end_verse):
                            verses.append({'verse_num': verse_num, 'text': verse['_text']})
    return verses

def get_books() -> Dict[str, List[str]]:
    """
    Displays Old Testament and New Testament books without fetching from the ERV-NE-SimpleJSON file.
    """
    old_testament_books = [
        "उत्पत्तिको पुस्तक", "प्रस्थानको पुस्तक", "लेवीहरूको पुस्तक", "गन्तीको पुस्तक", "व्यवस्थाको पुस्तक", "यहोशूको पुस्तक", "न्यायकर्त्ताहरूको पुस्तक", "रूथको पुस्तक",
        "1 शमूएलको पुस्तक", "2 शमूएलको पुस्तक", "1 राजाहरूको पुस्तक", "2 राजाहरूको पुस्तक", "1 इतिहासको पुस्तक", "2 इतिहासको पुस्तक", "एज्राको", "नहेम्याहको पुस्तक",
        "एस्तरको पुस्तक", "अय्यूबको पुस्तक", "भजनसंग्रह", "हितोपदेशको पुस्तक", "उपदेशकको पुस्तक", "सुलेमानको श्रेष्ठगीत", "यशैयाको पुस्तक", "यर्मियाको पुस्तक",
        "यर्मियाको विलाप", "इजकिएलको पुस्तक", "दानियलको पुस्तक", "होशे", "योएल", "आमोस", "ओबदिया", "योना", "मीका",
        "नहूम", "हबकूक", "सपन्याह", "हाग्गै", "जकरिया", "मलाकी"
    ]
    
    new_testament_books = [
        "मत्तीले लेखेको सुसमाचार", "मर्कूसले लेखेको सुसमाचार", "लूकाले लेखेको सुसमाचार", "यूहन्नाले लेखेको सुसमाचार", "प्रेरितहरूका काम", "रोमीहरूलाई पत्र", "कोरिन्थीहरूलाई पहिलो पत्र", "कोरिन्थीहरूलाई दोस्त्रो पत्र",
        "गलातीहरूलाई पत्र", "एफिसीहरूलाई पत्र", "फिलिप्पीहरूलाई पत्र", "कलस्सीहरूलाई पत्र", "थिस्सलोनिकीहरूलाई पहिलो पत्र", "थिस्सलोनिकीहरूलाई दोस्त्रो पत्र",
        "तिमोथीलाई पहिलो पत्र", "तिमोथीलाई दोस्त्रो पत्र", "तीतसलाई पत्र", "फिलेमोनलाई पत्र", "हिब्रूहरूको निम्ति पत्र", "याकूबको पत्र", "पत्रुसको पहिलो पत्र", "पत्रुसको दोस्त्रो पत्र",
        "यूहन्नाको पहिलो पत्र", "यूहन्नाको दोस्त्रो पत्र", "यूहन्नाको तेस्त्रो पत्र", "यहूदाको पत्र", "यूहन्नालाई भएको प्रकाश"
    ]
    
    books = {'Old Testament': old_testament_books, 'New Testament': new_testament_books}
    return books

def get_chapters(book_name: str) -> Dict[int, List[str]]:
    """
    Fetches all chapters and their verses for a given book from the ERV-NE-SimpleJSON file.
    """
    data = load_json_data('database/ERV-NE-SimpleJSON')
    chapters = {}
    
    for book in data['osis'][0]['osisText'][0]['div']:
        if book['name']['_value'] == book_name:
            for chap in book['chapter']:
                chapter_num = chap['cnumber']
                verses = []
                for verse in chap['verse']:
                    verse_text = f'<span class="verse-num">{verse["vnumber"]}</span> {verse["_text"]}'
                    verses.append(verse_text)
                chapters[chapter_num] = verses
    return chapters

if __name__ == "__main__":
    # Sample query to test the function
    verses = query_ne_bible_json('उत्पत्तिको पुस्तक', 1, 1, 10)
    for verse in verses:
        print(f"Verse {verse['verse_num']}: {verse['text']}")