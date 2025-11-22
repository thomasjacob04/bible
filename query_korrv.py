import sqlite3
from typing import List, Dict, Optional

def list_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for table in tables:
        print(table[0])

def query_korrv_db(book_name: str, chapter: int, start_verse: Optional[int] = None, end_verse: Optional[int] = None) -> List[Dict[str, str]]:
    """
    Fetches verses from the KorRV.db SQLite database.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect('database/KorRV.db')
    
    # List all tables in the database
    list_tables(conn)
    
    # Build the query based on the provided parameters
    query = """
    SELECT KorRV_books.name, KorRV_verses.chapter, KorRV_verses.verse, KorRV_verses.text
    FROM KorRV_verses
    JOIN KorRV_books ON KorRV_verses.book_id = KorRV_books.id
    WHERE KorRV_books.name = ? AND KorRV_verses.chapter = ?
    """
    params = [book_name, chapter]
    
    if start_verse is not None:
        query += " AND KorRV_verses.verse >= ?"
        params.append(start_verse)
    
    if end_verse is not None:
        query += " AND KorRV_verses.verse <= ?"
        params.append(end_verse)
    
    query += " ORDER BY KorRV_verses.verse"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)

        # Fetch and return the results
        results = cursor.fetchall()
        verses = [{'verse_num': row[2], 'text': row[3]} for row in results]
        return verses
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        return []
    finally:
        # Close the connection
        conn.close()

def get_books() -> Dict[str, List[str]]:
    """
    Displays Old Testament and New Testament books without fetching from the KorRV.db SQLite database.
    """
    old_testament_books = [
        "창세기", "출애굽기", "레위기", "민수기", "신명기", "여호수아", "사사기", "룻기",
        "사무엘상", "사무엘하", "열왕기상", "열왕기하", "역대상", "역대하", "에스라", "느헤미야",
        "에스더", "욥기", "시편", "잠언", "전도서", "아가", "이사야", "예레미야",
        "예레미야 애가", "에스겔", "다니엘", "호세아", "요엘", "아모스", "오바댜", "요나", "미가",
        "나훔", "하박국", "스바냐", "학개", "스가랴", "말라기"
    ]
    
    new_testament_books = [
        "마태복음", "마가복음", "누가복음", "요한복음", "사도행전", "로마서", "고린도전서", "고린도후서",
        "갈라디아서", "에베소서", "빌립보서", "골로새서", "데살로니가전서", "데살로니가후서",
        "디모데전서", "디모데후서", "디도서", "빌레몬서", "히브리서", "야고보서", "베드로전서", "베드로후서",
        "요한일서", "요한이서", "요한삼서", "유다서", "요한계시록"
    ]
    
    books = {'Old Testament': old_testament_books, 'New Testament': new_testament_books}
    print(f"Books: {books}")  # Debugging statement
    return books

def get_chapters(book_name: str) -> Dict[int, List[str]]:
    """
    Fetches all chapters and their verses for a given book from the KorRV.db SQLite database.
    """

    conn = sqlite3.connect('database/KorRV.db')
    query = """
    SELECT chapter, verse, text
    FROM KorRV_verses
    JOIN KorRV_books ON KorRV_verses.book_id = KorRV_books.id
    WHERE KorRV_books.name = ?
    ORDER BY chapter, verse
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (book_name,))
        results = cursor.fetchall()
        chapters = {}
        for row in results:
            chapter = row[0]
            verse_text = f'<span class="verse-num">{row[1]}</span> {row[2]}'
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(verse_text)
        return chapters
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        return {}
    finally:
        conn.close()

if __name__ == "__main__":
    # Sample query to test the function
    verses = query_korrv_db('요한복음', 3, 1, 10)
    for verse in verses:
        print(f"Verse {verse['verse_num']}: {verse['text']}")