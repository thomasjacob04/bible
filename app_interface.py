from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_from_directory, flash
from flask_session import Session
from app import step5_process_bible_reference, translate_biblical_text
from app_ko import step5_process_bible_reference_ko
from app_ne import step5_process_bible_reference_ne, step3_fetch_bible_verses, BibleReference
from app_mal import step3_fetch_bible_verses_mal, step5_process_bible_reference_mal, step2_parse_bible_reference
from dotenv import load_dotenv
import os
import requests
import json
import csv
import fcntl
from query_kjv import query_kjv_db, get_books, get_chapters  # Import get_chapters
from query_korrv import query_korrv_db, get_books as get_books_ko, get_chapters as get_chapters_ko  # Import Korean functions
from query_NE_bible import query_ne_bible_json, get_books as get_books_ne, get_chapters as get_chapters_ne  # Import Nepali functions
from query_mal1920 import query_mal_bible_json, get_books as get_books_mal, get_chapters as get_chapters_mal # Import Malayalam functions
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from KoBART import mbart
from groq_devotionals import get_bible_verse
from groq_devotionals_ko import get_bible_verse_ko

load_dotenv()  # Load environment variables from a .env file

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  # Set a secret key for session management

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/query/<reference>')
def query(reference):
    language = session.get('lang', 'en')  # Get the language from the session, default to 'en'
    response = search_csv(reference, language)
    if not response:
        flash('Query not found in the database.', 'error')
        return redirect(url_for('home'))

    # Store the response in the session
    session['response'] = response
    session['user_input'] = reference  # Store user input in session for retry

    return redirect(url_for('home'))

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    bible_api_key = os.getenv("BIBLE_API_KEY")
    language = session.get('lang', 'en')  # Get the language from the session, default to 'en'
    recent_queries = get_recent_queries_from_session()
    if request.method == 'POST':
        user_input = request.form['reference']
        print(f"Received user input: {user_input}")  # Debugging statement
        
        # Search the CSV file for the response
        response = search_csv(user_input, language)
        print(f"CSV search response from app_interface: {response}")  # Debugging statement
        if not response:
            # Process the Bible reference if not found in CSV
            response = step5_process_bible_reference(user_input, bible_api_key)
            print(f"Processed response: {response}")  # Debugging statement

            # # Write the query and results to a CSV file
            # if response['analysis'] and response['explanation'] and response['related_verses']:
            #     with open('database/queries.csv', mode='a', newline='') as file:
            #         writer = csv.writer(file)
            #         writer.writerow([response['requested_reference'], language, json.dumps(response['retrieved_passages']), response['analysis'], response['explanation'], response['related_verses']])
            #         print(f"Wrote to CSV: {response['requested_reference']}")  # Debugging statement
        
        # Store the response in the session
        session['response'] = response
        session['user_input'] = user_input  # Store user input in session for retry

        # Add the requested reference to the session
        requested_reference = response.get('requested_reference')
        if requested_reference:
            add_query_to_session(requested_reference)

        return redirect(url_for('home'))

    reference = request.args.get('reference')
    if reference:
        session['user_input'] = reference
        return redirect(url_for('home'))

    response = session.get('response', None)
    user_input = session.get('user_input', '')  # Get user input from session for retry

    # Handle language redirection
    if 'lang' in session:
        if session['lang'] == 'ko':
            return redirect(url_for('home_ko'))
        elif session['lang'] == 'ne':
            return redirect(url_for('home_ne'))
        elif session['lang'] == 'mal':
            return redirect(url_for('home_mal'))

    return render_template('home.html', response=response, bible_api_key=bible_api_key, user_input=user_input, recent_queries=recent_queries)

@app.route('/home_ko', methods=['GET', 'POST'])
def home_ko():
    bible_api_key = os.getenv("BIBLE_API_KEY")
    language = session.get('lang', 'ko')  # Get the language from the session, default to 'en'
    recent_queries = get_recent_queries_from_session()
    if request.method == 'POST':
        user_input = request.form['reference']
        print(f"Received user input: {user_input}")  # Debugging statement

        # Search the CSV file for the response
        response = search_csv(user_input, language)
        if not response:
            # Process the Bible reference if not found in CSV
            response = step5_process_bible_reference_ko(user_input, bible_api_key)

            # # Write the query and results to a CSV file
            # if response['analysis'] and response['explanation'] and response['related_verses']:
            #     with open('database/queries.csv', mode='a', newline='') as file:
            #         writer = csv.writer(file)
            #         writer.writerow([response['requested_reference'], language, response['analysis'], response['explanation'], response['related_verses']])
        
        add_query_to_session(user_input)
        # Store the response in the session
        session['response'] = response
        session['user_input'] = user_input  # Store user input in session for retry

        return redirect(url_for('home_ko'))

    reference = request.args.get('reference')
    if reference:
        session['user_input'] = reference
        return redirect(url_for('home_ko'))

    response = session.get('response', None)
    user_input = session.get('user_input', '')  # Get user input from session for retry

    # Handle language redirection
    if 'lang' in session:
        if session['lang'] == 'en':
            return redirect(url_for('home'))
        elif session['lang'] == 'ne':
            return redirect(url_for('home_ne'))
        elif session['lang'] == 'mal':
            return redirect(url_for('home_mal'))

    return render_template('home_ko.html', response=response, bible_api_key=bible_api_key, user_input=user_input, recent_queries=recent_queries)

@app.route('/home_ne', methods=['GET', 'POST'])
def home_ne():
    bible_api_key = os.getenv("BIBLE_API_KEY")
    language = session.get('lang', 'ne')  # Get the language from the session, default to 'en'
    recent_queries = get_recent_queries_from_session()
    if request.method == 'POST':
        user_input = request.form['reference']
        print(f"Received user input: {user_input}")  # Debugging statement

        # Search the CSV file for the response
        response = search_csv(user_input, language)
        if not response:
            # Process the Bible reference if not found in CSV
            response = step5_process_bible_reference_ne(user_input, bible_api_key)

            # # Write the query and results to a CSV file
            # if response and response.get('analysis') and response.get('explanation') and response.get('related_verses'):
            #     with open('database/queries.csv', mode='a', newline='') as file:
            #         writer = csv.writer(file)
            #         writer.writerow([response['requested_reference'], language, json.dumps(response['retrieved_passages']), response['analysis'], response['explanation'], response['related_verses']])
            #         print(f"Wrote to CSV: {response['requested_reference']}")  # Debugging statement

        add_query_to_session(user_input)
                
        # Store the response in the session
        session['response'] = response
        session['user_input'] = user_input  # Store user input in session for retry

        return redirect(url_for('home_ne'))

    reference = request.args.get('reference')
    if reference:
        session['user_input'] = reference
        return redirect(url_for('home_ne'))

    response = session.get('response', None)
    user_input = session.get('user_input', '')  # Get user input from session for retry

    # Handle language redirection
    if 'lang' in session:
        if session['lang'] == 'en':
            return redirect(url_for('home'))
        elif session['lang'] == 'ko':
            return redirect(url_for('home_ko'))
        elif session['lang'] == 'mal':
            return redirect(url_for('home_mal'))

    return render_template('home_ne.html', response=response, bible_api_key=bible_api_key, user_input=user_input, recent_queries=recent_queries)

@app.route('/home_mal', methods=['GET', 'POST'])
def home_mal():
    bible_api_key = os.getenv("BIBLE_API_KEY")
    language = session.get('lang', 'mal')  # Get the language from the session, default to 'en'
    recent_queries = get_recent_queries_from_session()
    # user input from the home input form.
    if request.method == 'POST':
        user_input = request.form['reference']
        language = 'mal'
        print(f"Received user input: {user_input}")  # Debugging statement

        # Search the CSV file for the response
        response = search_csv(user_input, language)
        if not response:
            # Process the Bible reference if not found in CSV
            response = step5_process_bible_reference_mal(user_input, bible_api_key)

            # # Write the query and results to a CSV file
            # if response['analysis'] and response['explanation'] and response['related_verses']:
            #     with open('database/queries.csv', mode='a', newline='') as file:
            #         # Lock the file
            #         fcntl.flock(file, fcntl.LOCK_EX)
            #         try:
            #             writer = csv.writer(file)
            #             writer.writerow([response['requested_reference'], language, response['analysis'], response['explanation'], response['related_verses']])
            #         finally:
            #             # Unlock the file
            #             fcntl.flock(file, fcntl.LOCK_UN)
        
        add_query_to_session(user_input)
           
        # Store the response in the session
        session['response'] = response
        session['user_input'] = user_input  # Store user input in session for retry

        return redirect(url_for('home_mal'))

    reference = request.args.get('reference')
    if reference:
        session['user_input'] = reference
        return redirect(url_for('home_mal'))

    response = session.get('response', None)
    user_input = session.get('user_input', '')  # Get user input from session for retry

    if 'lang' in session:
        if session['lang'] == 'en':
            return redirect(url_for('home'))
        elif session['lang'] == 'ko':
            return redirect(url_for('home_ko'))
        elif session['lang'] == 'ne':
            return redirect(url_for('home_ne'))

    return render_template('home_mal.html', response=response, bible_api_key=bible_api_key, user_input=user_input, recent_queries=recent_queries)



@app.route('/set_language')
def set_language():
    lang = request.args.get('lang')
    session['lang'] = lang
    return jsonify(success=True)

@app.route('/books')
def books():
    books = get_books()
    first_visit = False
    return render_template('books.html', books=books, selected_book=None, chapters={}, total_chapters=0, first_visit=first_visit)

@app.route('/books_ko')
def books_ko():
    books = get_books_ko()
    print(f"Fetched Korean books: {books}")  # Debugging statement
    return render_template('books_ko.html', books=books, selected_book=None, chapters={}, total_chapters=0)

@app.route('/books/<book_name>')
def book_chapters(book_name):
    chapters = get_chapters(book_name)
    total_chapters = len(chapters) if chapters else 0
    if 'visited' not in session:
        session['visited'] = True
        first_visit = True
        print("First visit to the books.", first_visit)  # Debugging statement
    else:
        first_visit = False
        print("Returning visit to the books.", first_visit)
    return render_template('books.html', selected_book=book_name, chapters=chapters, total_chapters=total_chapters, books={}, first_visit = first_visit)

@app.route('/books_ko/<book_name>')
def book_chapters_ko(book_name):
    chapters = get_chapters_ko(book_name)
    total_chapters = len(chapters) if chapters else 0
    if 'visited' not in session:
        session['visited'] = True
        first_visit = True
        print("First visit to the books.", first_visit)  # Debugging statement
    else:
        first_visit = False
        print("Returning visit to the books.", first_visit)
    return render_template('books_ko.html', selected_book=book_name, chapters=chapters, total_chapters=total_chapters, books={}, first_visit = first_visit)

@app.route('/books_ne')
def books_ne():
    books = get_books_ne()
    return render_template('books_ne.html', books=books, selected_book=None, chapters={}, total_chapters=0)

@app.route('/books_mal')
def books_mal():
    books = get_books_mal()
    return render_template('books_mal.html', books=books, selected_book=None, chapters={}, total_chapters=0)

@app.route('/books_mal/<book_name>')
def book_chapters_mal(book_name):
    chapters = get_chapters_mal(book_name)
    total_chapters = len(chapters) if chapters else 0
    if 'visited' not in session:
        session['visited'] = True
        first_visit = True
        print("First visit to the books.", first_visit)  # Debugging statement
    else:
        first_visit = False
        print("Returning visit to the books.", first_visit)
    return render_template('books_mal.html', selected_book=book_name, chapters=chapters, total_chapters=total_chapters, books={}, first_visit = first_visit)

@app.route('/books_ne/<book_name>')
def book_chapters_ne(book_name):
    chapters = get_chapters_ne(book_name)
    total_chapters = len(chapters) if chapters else 0
    if 'visited' not in session:
        session['visited'] = True
        first_visit = True
        print("First visit to the books.", first_visit)  # Debugging statement
    else:
        first_visit = False
        print("Returning visit to the books.", first_visit)
    return render_template('books_ne.html', selected_book=book_name, chapters=chapters, total_chapters=total_chapters, books={}, first_visit = first_visit)

@app.route('/devotionals')
def devotionals():
    return render_template('devotionals.html')

@app.route('/devotionals/<devotional_id>')
def devotional_detail(devotional_id):
    devotionals = [
           {
            'id': 'anxiety',
            'name': 'Anxiety & Fear',
            'description': 'Feeling overwhelmed or fearful about life',
            'icon': '😰',
            'connectedTheme': 'Peace & Rest'
            },
            {
                'id': 'loneliness',
                'name': 'Depression & Loneliness',
                'description': 'Feeling isolated or experiencing deep sadness',
                'icon': '😔',
                'connectedTheme': 'Hope & Perseverance'
            },
            {
                'id': 'purpose',
                'name': 'Purpose & Calling',
                'description': 'Seeking meaning and direction in life',
                'icon': '🌟',
                'connectedTheme': 'Wisdom & Knowledge'
            },
            {
                'id': 'anger',
                'name': 'Anger & Hurt',
                'description': 'Dealing with anger and past hurts',
                'icon': '😠',
                'connectedTheme': 'Forgiveness & Healing'
            },
            {
                'id': 'worry',
                'name': 'Worry & Stress',
                'description': 'Managing daily stress and worries',
                'icon': '😓',
                'connectedTheme': 'Trust & Peace'
            },
            {
                'id': 'grief',
                'name': 'Grief & Loss',
                'description': 'Coping with loss and sadness',
                'icon': '💔',
                'connectedTheme': 'Comfort & Hope'
            },
            {
                'id': 'doubt',
                'name': 'Doubt & Faith',
                'description': 'Strengthening faith in difficult times',
                'icon': '🤔',
                'connectedTheme': 'Faith & Trust'
            },
            {
                'id': 'gratitude',
                'name': 'Gratitude',
                'description': 'Finding joy in all circumstances',
                'icon': '🙏',
                'connectedTheme': 'Joy & Thanksgiving'
            },
            {
                'id': 'guidance',
                'name': 'Guidance',
                'description': 'Seeking direction and wisdom',
                'icon': '🧭',
                'connectedTheme': 'Wisdom & Direction'
            },
            {
                'id': 'peace',
                'name': 'Peace',
                'description': 'Finding tranquility in chaos',
                'icon': '🕊️',
                'connectedTheme': 'Peace & Serenity'
            }
    ]

    devotional = next((d for d in devotionals if d['id'] == devotional_id), None)
    if not devotional:
        return "Devotional not found", 404

    print(f"Devotional: {devotional}")  # Debugging statement
    bible_verse = get_bible_verse(devotional['name'], devotional['connectedTheme'])
    return render_template('devotional_detail.html', devotional=devotional, bible_verse=bible_verse)

@app.route('/devotionals_ko')
def devotionals_ko():
    return render_template('devotionals_ko.html')

@app.route('/devotionals_ko/<devotional_id>')
def devotional_detail_ko(devotional_id):
    devotionals = [
           {
            'id': 'anxiety',
            'name': 'Anxiety & Fear',
            'description': 'Feeling overwhelmed or fearful about life',
            'icon': '😰',
            'connectedTheme': 'Peace & Rest'
            },
            {
                'id': 'loneliness',
                'name': 'Depression & Loneliness',
                'description': 'Feeling isolated or experiencing deep sadness',
                'icon': '😔',
                'connectedTheme': 'Hope & Perseverance'
            },
            {
                'id': 'purpose',
                'name': 'Purpose & Calling',
                'description': 'Seeking meaning and direction in life',
                'icon': '🌟',
                'connectedTheme': 'Wisdom & Knowledge'
            },
            {
                'id': 'anger',
                'name': 'Anger & Hurt',
                'description': 'Dealing with anger and past hurts',
                'icon': '😠',
                'connectedTheme': 'Forgiveness & Healing'
            },
            {
                'id': 'worry',
                'name': 'Worry & Stress',
                'description': 'Managing daily stress and worries',
                'icon': '😓',
                'connectedTheme': 'Trust & Peace'
            },
            {
                'id': 'grief',
                'name': 'Grief & Loss',
                'description': 'Coping with loss and sadness',
                'icon': '💔',
                'connectedTheme': 'Comfort & Hope'
            },
            {
                'id': 'doubt',
                'name': 'Doubt & Faith',
                'description': 'Strengthening faith in difficult times',
                'icon': '🤔',
                'connectedTheme': 'Faith & Trust'
            },
            {
                'id': 'gratitude',
                'name': 'Gratitude',
                'description': 'Finding joy in all circumstances',
                'icon': '🙏',
                'connectedTheme': 'Joy & Thanksgiving'
            },
            {
                'id': 'guidance',
                'name': 'Guidance',
                'description': 'Seeking direction and wisdom',
                'icon': '🧭',
                'connectedTheme': 'Wisdom & Direction'
            },
            {
                'id': 'peace',
                'name': 'Peace',
                'description': 'Finding tranquility in chaos',
                'icon': '🕊️',
                'connectedTheme': 'Peace & Serenity'
            }
    ]

    devotional = next((d for d in devotionals if d['id'] == devotional_id), None)
    if not devotional:
        return "Devotional not found", 404

    print(f"Devotional: {devotional}")  # Debugging statement
    bible_verse = get_bible_verse_ko(devotional['name'], devotional['connectedTheme'])
    return render_template('devotional_detail_ko.html', devotional=devotional, bible_verse=bible_verse)


@app.route('/fetch_verse_ne')
def fetch_verse_ne():
    book = request.args.get('book')
    chapter = int(request.args.get('chapter'))
    verse = request.args.get('verse')

    # Handle verse ranges
    if '-' in verse:
        start_verse, end_verse = map(int, verse.split('-'))
    else:
        start_verse = end_verse = int(verse)

    verses = query_ne_bible_json(book, chapter, start_verse, end_verse)
    if verses:
        return jsonify({'text': ' '.join([v['text'] for v in verses])})
    else:
        return jsonify({'text': 'Verse not found.'})

@app.route('/fetch_verse_mal')
def fetch_verse_mal():
    book = request.args.get('book')
    chapter = int(request.args.get('chapter'))
    verse = request.args.get('verse')

    # Handle verse ranges
    if '-' in verse:
        start_verse, end_verse = map(int, verse.split('-'))
    else:
        start_verse = end_verse = int(verse)

    verses = query_mal_bible_json(book, chapter, start_verse, end_verse)
    if verses:
        return jsonify({'text': ' '.join([v['text'] for v in verses])})
    else:
        return jsonify({'text': 'Verse not found.'})



@app.route('/fetch_verses_ne', methods=['GET'])
def fetch_verses_ne():
    book = request.args.get('book')
    chapter = int(request.args.get('chapter'))
    start_verse = int(request.args.get('start_verse', 1))
    end_verse = int(request.args.get('end_verse', start_verse))

    reference = BibleReference(book=book, chapter=chapter, start_verse=start_verse, end_verse=end_verse)
    bible_api_key = os.getenv("BIBLE_API_KEY")
    verses = step3_fetch_bible_verses(reference, bible_api_key)

    return jsonify(verses)


@app.route('/fetch_verse')
def fetch_verse():
    book = request.args.get('book')
    chapter = int(request.args.get('chapter'))
    verse = request.args.get('verse')

    # Handle verse ranges
    if '-' in verse:
        start_verse, end_verse = map(int, verse.split('-'))
    else:
        start_verse = end_verse = int(verse)

    # Check if the book is Revelation and change the name
    if book.lower() == 'revelation':
        book = 'Revelation of John'

    verses = query_kjv_db(book, chapter, start_verse, end_verse)
    if verses:
        return jsonify({'text': ' '.join([v['text'] for v in verses])})
    else:
        return jsonify({'text': 'Verse not found.'})

@app.route('/fetch_verse_ko')
def fetch_verse_ko():
    book = request.args.get('book')
    chapter = int(request.args.get('chapter'))
    verse = request.args.get('verse')

    # Handle verse ranges
    if '-' in verse:
        start_verse, end_verse = map(int, verse.split('-'))
    else:
        start_verse = end_verse = int(verse)

    # Check if the book is Revelation and change the name
    if book.lower() == 'revelation':
        book = 'Revelation of John'

    verses = query_korrv_db(book, chapter, start_verse, end_verse)
    if verses:
        return jsonify({'text': ' '.join([v['text'] for v in verses])})
    else:
        return jsonify({'text': 'Verse not found.'})


@app.route('/enhance_ko', methods=['POST'])
def enhance_ko():
    data = request.json
    text = data.get('text', '')
    if text:
        translated_text = mbart(text, src_lang="en_XX", tgt_lang="ko_KR")
        return jsonify({ 'translated_text': translated_text })
    return jsonify({ 'translated_text': text }), 400


@app.route('/enhance_ne', methods=['POST'])
def enhance_ne():
    data = request.json
    text = data.get('text', '')
    if text:
        translated_text = mbart(text, src_lang="en_XX", tgt_lang="ne_NP")
        return jsonify({ 'translated_text': translated_text })
    return jsonify({ 'translated_text': text }), 400

@app.route('/fetch_chapter')
def fetch_chapter():
    book = request.args.get('book')
    chapter = int(request.args.get('chapter'))
    chapters = get_chapters(book)
    verses = chapters.get(chapter, [])
    return jsonify({'verses': verses})

@app.route('/support_en')
def support_en():
    return render_template('support_en.html')

@app.route('/support_ko')
def support_ko():
    return render_template('support_ko.html')

@app.route('/support_ne')
def support_ne():
    return render_template('support_ne.html')

def format_phone_number(phone_number: str) -> str:
    """
    Formats the phone number to include the country code.

    Args:
        phone_number (str): The input phone number.

    Returns:
        str: The formatted phone number with country code.
    """
    if phone_number.startswith('0'):
        phone_number = phone_number.lstrip('0')
    if not phone_number.startswith('+'):
        phone_number = '+61' + phone_number
    return phone_number


@app.route('/book_summary')
def book_summary():
    book = request.args.get('book')
    
    try:
        with open('database/book_summaries.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['book'] == book:
                    return jsonify({'summary': row['summary']})
        return jsonify({'summary': 'Summary not available for this book.'})
    except Exception as e:
        return jsonify({'summary': f'Error loading summary: {str(e)}'})

@app.route('/section_summary')
def section_summary():
    book = request.args.get('book')
    chapter = int(request.args.get('chapter'))
    
    try:
        with open('database/section_summaries.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['book'] == book:
                    # Check if the row has a section range
                    if '-' in str(row.get('section', '')):
                        start, end = map(int, row['section'].split('-'))
                        if start <= chapter <= end:
                            return jsonify({
                                'summary': row['summary'],
                                'title': row['title']
                            })
                    # If no section range, check exact match
                    elif row.get('section') == str(chapter):
                        return jsonify({
                            'summary': row['summary'],
                            'title': row['title']
                        })
                        
        return jsonify({'summary': 'Summary not available for this section.',
            'title': ''
        })
    except Exception as e:
        return jsonify({'summary': f'Error loading summary: {str(e)}',
            'title': ''
        })
    


@app.route('/send_sms', methods=['POST'])
def send_sms():
    access_token = 'o.POWDZhilsui4k70JovGkO345zn7UtiPV'
    device_iden = 'ujzagZjWM6SsjE0zFWjvs4'  # Correct device ID
    fixed_phone_number = '0415824465'  # Fixed phone number

    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    # Format phone number
    phoneNumber = format_phone_number(fixed_phone_number)
    print(f"Formatted phone number: {phoneNumber}")  # Debugging statement

    print(f"Sending SMS to {phoneNumber} with message: {message}")  # Debugging statement

    # Prepare the Pushbullet API request for SMS using new endpoint
    requestData = {
        'data': {
            'target_device_iden': device_iden,
            'addresses': [phoneNumber],
            'message': name + ' from ' + email + ' said ' + message,
            'guid': 'sms_' + str(uuid.uuid4())  # Prefix with 'sms_' for better tracking
        }
    }

    headers = {
        'Access-Token': access_token,
        'Content-Type': 'application/json'
    }

    # Send SMS request
    response = requests.post('https://api.pushbullet.com/v2/texts', headers=headers, data=json.dumps(requestData))
    responseData = response.json()

        # Check if the SMS was sent successfully
    if response.status_code == 200 and responseData.get('active'):
        flash('Thank you for your feedback!', 'success')
    else:
        flash('Failed to send feedback, can you text 0415824465 directly? Thanks!', 'error')

    return redirect(url_for('support_en'))


@app.route('/send_sms_ko', methods=['POST'])
def send_sms_ko():
    access_token = 'o.POWDZhilsui4k70JovGkO345zn7UtiPV'
    device_iden = 'ujzagZjWM6SsjE0zFWjvs4'  # Correct device ID
    fixed_phone_number = '0415824465'  # Fixed phone number

    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    # Format phone number
    phoneNumber = format_phone_number(fixed_phone_number)
    print(f"Formatted phone number: {phoneNumber}")  # Debugging statement

    print(f"Sending SMS to {phoneNumber} with message: {message}")  # Debugging statement

    # Prepare the Pushbullet API request for SMS using new endpoint
    requestData = {
        'data': {
            'target_device_iden': device_iden,
            'addresses': [phoneNumber],
            'message': name + ' from ' + email + ' said ' + message,
            'guid': 'sms_' + str(uuid.uuid4())  # Prefix with 'sms_' for better tracking
        }
    }

    headers = {
        'Access-Token': access_token,
        'Content-Type': 'application/json'
    }

    # Send SMS request
    response = requests.post('https://api.pushbullet.com/v2/texts', headers=headers, data=json.dumps(requestData))
    responseData = response.json()

        # Check if the SMS was sent successfully
    if response.status_code == 200 and responseData.get('active'):
        flash('소중한 의견 감사합니다!', 'success')
    else:
        flash('피드백 전송에 실패했습니다. 0415824465로 직접 문자 보내주시겠어요? 감사합니다!', 'error')

    return redirect(url_for('support_ko'))

def search_csv(user_input, language):
    print(f"Searching CSV for user input: {user_input}, language: {language}")  # Debugging statement
    with open('database/queries.csv', mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == user_input and row[1] == language:
                try:
                    retrieved_passages = json.loads(row[2])
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    continue
                print(f"Found in CSV: {row[0]}")  # Debugging statement
                return {
                    "requested_reference": row[0],
                    "retrieved_passages": retrieved_passages,
                    "analysis": row[3],
                    "explanation": row[4],
                    "related_verses": row[5]
                }
    print("Not found in CSV")  # Debugging statement
    return None

def get_recent_queries(language):
    recent_queries = []
    with open('database/queries.csv', mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[1] == language:
                recent_queries.append(row)
    return recent_queries[-8:]  # Return the last 5 items

def get_recent_queries_from_session():
    return session.get('recent_queries', [])

def add_query_to_session(requested_reference):
    recent_queries = session.get('recent_queries', [])
    if requested_reference not in recent_queries:
        recent_queries.append(requested_reference)
        print(f"Added query to session: {requested_reference}")  # Debugging statement
        if len(recent_queries) > 5:
            recent_queries.pop(0)  # Keep only the last 5 queries
        session['recent_queries'] = recent_queries


def is_english(text: str) -> bool:
    """
    Checks if the given text is in English.

    Args:
        text (str): The input text to check.

    Returns:
        bool: True if the text is in English, False otherwise.
    """
    try:
        text.encode('ascii')
    except UnicodeEncodeError:
        return False
    else:
        return True

import re
import uuid

def is_korean(text: str) -> bool:
    """
    Checks if the given text is in Korean.

    Args:
        text (str): The input text to check.

    Returns:
        bool: True if the text is in Korean, False otherwise.
    """
    korean_pattern = re.compile(r'[\uAC00-\uD7AF\u1100-\u11FF]')
    return bool(korean_pattern.search(text))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)