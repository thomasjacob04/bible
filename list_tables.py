from query_NE_bible import query_ne_bible_db, get_books, get_chapters

class TestNEBibleDatabase(unittest.TestCase):

    def test_query_ne_bible_db(self):
        # Test querying a specific book, chapter, and verses
        book_name = '요한복음'
        chapter = 3
        start_verse = 1
        end_verse = 10
        verses = query_ne_bible_db(book_name, chapter, start_verse, end_verse)
        self.assertIsInstance(verses, list)
        self.assertGreater(len(verses), 0)
        for verse in verses:
            self.assertIn('verse_num', verse)
            self.assertIn('text', verse)
            print(f"Verse {verse['verse_num']}: {verse['text']}")


if __name__ == '__main__':
    unittest.main()