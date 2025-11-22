import sqlite3
from typing import List, Dict, Optional
from contextlib import contextmanager
import threading

# Thread-local storage for database connections
_thread_local = threading.local()

def get_connection():
    """
    Get a thread-local database connection.
    This ensures each thread has its own connection and reuses it.
    """
    if not hasattr(_thread_local, 'conn') or _thread_local.conn is None:
        _thread_local.conn = sqlite3.connect('database/KJV.db', check_same_thread=False)
        # Enable WAL mode for better concurrent read performance
        _thread_local.conn.execute('PRAGMA journal_mode=WAL')
        # Enable read-only mode for safety (optional)
        # _thread_local.conn.execute('PRAGMA query_only=ON')
    return _thread_local.conn

@contextmanager
def get_cursor():
    """
    Context manager for getting a database cursor.
    Automatically handles connection management.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()

def list_tables(conn):
    """
    Debug function to list all tables in the database.
    Only use this for debugging purposes.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for table in tables:
        print(table[0])

def query_kjv_db(book_name: str, chapter: int, start_verse: Optional[int] = None, end_verse: Optional[int] = None) -> List[Dict[str, str]]:
    """
    Fetches verses from the KJV.db SQLite database using a persistent connection.
    """
    # Build the query based on the provided parameters
    query = """
    SELECT KJV_books.name, KJV_verses.chapter, KJV_verses.verse, KJV_verses.text
    FROM KJV_verses
    JOIN KJV_books ON KJV_verses.book_id = KJV_books.id
    WHERE KJV_books.name = ? AND KJV_verses.chapter = ?
    """
    params = [book_name, chapter]

    if start_verse is not None:
        query += " AND KJV_verses.verse >= ?"
        params.append(start_verse)

    if end_verse is not None:
        query += " AND KJV_verses.verse <= ?"
        params.append(end_verse)

    query += " ORDER BY KJV_verses.verse"

    try:
        with get_cursor() as cursor:
            cursor.execute(query, params)
            # Fetch and return the results
            results = cursor.fetchall()
            verses = [{'verse_num': row[2], 'text': row[3]} for row in results]
            return verses
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        return []

# Cache for books list (since it never changes)
_books_cache = None

def get_books() -> Dict[str, List[str]]:
    """
    Fetches all books from the KJV.db SQLite database and categorizes them into Old Testament and New Testament.
    Uses caching since the book list never changes.
    """
    global _books_cache

    # Return cached result if available
    if _books_cache is not None:
        return _books_cache

    query = """
    SELECT name
    FROM KJV_books
    ORDER BY id
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

    try:
        with get_cursor() as cursor:
            cursor.execute(query)

            # Fetch and categorize the results
            results = cursor.fetchall()
            books = {'Old Testament': [], 'New Testament': []}
            for row in results:
                book_name = row[0]
                if book_name in old_testament_books:
                    books['Old Testament'].append(book_name)
                elif book_name in new_testament_books:
                    books['New Testament'].append(book_name)

            # Cache the result
            _books_cache = books
            return books
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        return {'Old Testament': [], 'New Testament': []}

# def get_all_books() -> List[str]:
#     """
#     Fetches all book names from the BBE.db SQLite database.
#     """
#     conn = sqlite3.connect('database/BBE.db')
#     query = "SELECT name FROM BBE_books ORDER BY name"
    
#     try:
#         cursor = conn.cursor()
#         cursor.execute(query)
#         results = cursor.fetchall()
#         books = [row[0] for row in results]
#         return books
#     except sqlite3.OperationalError as e:
#         print(f"Error: {e}")
#         return []
#     finally:
#         conn.close()
        
# Cache for chapters (since Bible content never changes)
_chapters_cache = {}

def get_chapters(book_name: str) -> Dict[int, List[str]]:
    """
    Fetches all chapters and their verses for a given book from the KJV.db SQLite database.
    Uses caching since Bible content never changes.
    """
    # Return cached result if available
    if book_name in _chapters_cache:
        return _chapters_cache[book_name]

    query = """
    SELECT chapter, verse, text
    FROM KJV_verses
    JOIN KJV_books ON KJV_verses.book_id = KJV_books.id
    WHERE KJV_books.name = ?
    ORDER BY chapter, verse
    """
    try:
        with get_cursor() as cursor:
            cursor.execute(query, (book_name,))
            results = cursor.fetchall()
            chapters = {}
            for row in results:
                chapter = row[0]
                verse_text = f'<span class="verse-num">{row[1]}</span> {row[2]}'
                if chapter not in chapters:
                    chapters[chapter] = []
                chapters[chapter].append(verse_text)

            # Cache the result
            _chapters_cache[book_name] = chapters
            return chapters
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        return {}

def close_connection():
    """
    Close the thread-local database connection.
    Call this when shutting down the application or at the end of a request.
    """
    if hasattr(_thread_local, 'conn') and _thread_local.conn is not None:
        _thread_local.conn.close()
        _thread_local.conn = None

def clear_cache():
    """
    Clear all cached data. Useful for testing or if the database is updated.
    """
    global _books_cache, _chapters_cache
    _books_cache = None
    _chapters_cache = {}

if __name__ == "__main__":
    # Sample query to test the function
    verses = query_kjv_db('John', 3, 1, 10)
    for verse in verses:
        print(f"Verse {verse['verse_num']}: {verse['text']}")

    # Test caching
    print("\nTesting caching...")
    books1 = get_books()
    books2 = get_books()  # Should use cache
    print(f"Books fetched (cached): {len(books1['Old Testament']) + len(books1['New Testament'])} books")

    # Clean up
    close_connection()