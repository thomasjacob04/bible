from query_NE_bible import query_ne_bible_json
from query_mal1920 import query_mal_bible_json
from typing import Optional

# def test_query_ne_bible(book_name: str, chapter: int, start_verse: Optional[int] = None, end_verse: Optional[int] = None):
#     """
#     Tests the query_ne_bible_json function by passing parameters and printing the output.
#     """
#     verses = query_ne_bible_json(book_name, chapter, start_verse, end_verse)
#     if verses:
#         print(f"Verses from {book_name} Chapter {chapter}:")
#         for verse in verses:
#             print(f"Verse {verse['verse_num']}: {verse['text']}")
#     else:
#         print(f"No verses found for {book_name} Chapter {chapter}.")

def test_query_mal_bible(book_name: str, chapter: int, start_verse: Optional[int] = None, end_verse: Optional[int] = None):
    """
    Tests the query_mal_bible_json function by passing parameters and printing the output.
    
    Args:
        book_name (str): Name of the book (e.g., "Genesis").
        chapter (int): Chapter number.
        start_verse (Optional[int]): Starting verse number (inclusive). Defaults to None.
        end_verse (Optional[int]): Ending verse number (inclusive). Defaults to None.
    """
    # Call the query function
    verses = query_mal_bible_json(book_name, chapter, start_verse, end_verse)
    
    # Print the raw output for debugging
    print(verses)
    
    # Print formatted output
    if verses:
        print(f"Verses from {book_name} Chapter {chapter}:")
        for verse in verses:
            print(f"Verse {verse['verse']}: {verse['text']}")  # Use 'verse' instead of 'verse_num'
    else:
        print(f"No verses found for {book_name} Chapter {chapter}.")

        
if __name__ == "__main__":
    # Example query to test the Nepali Bible function
    #  test_query_ne_bible('उत्पत्तिको पुस्तक', 1, 1, 10)
    
    # Example query to test the Malayalam Bible function
    test_query_mal_bible('Genesis', 1, 1, 10)