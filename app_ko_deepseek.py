import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import time

load_dotenv()

def test_deepseek_bible_reference_1theme(api_key: str, user_input: str) -> str:
    # Initialize the DeepSeek client
    client = ChatOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat"  # Replace with the correct model name
    )
    # Define the prompt for parsing the Bible reference
    prompt = f"""
    Parse the following Bible reference into a structured format.
    Please provide in korean language, in hangul script only:
    The main theme or themes of this passage

    User's reference: {user_input}

    """

    # Generate the response using the chat model
    response = client.invoke(prompt)

    # Extract the content from the response
    content = response.content

    # Return the cleaned response
    return content

def test_groq_bible_ref_1theme():
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
The main theme or themes of this passage

Response:"""
    )

    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")
    chain = prompt_template | llm
    return chain

def test_deepseek_bible_reference_2explanation(api_key: str, user_input: str) -> str:
    # Initialize the DeepSeek client
    client = ChatOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat"  # Replace with the correct model name
    )
    # Define the prompt for parsing the Bible reference
    prompt = f"""
    Parse the following Bible reference into a structured format.
    Please provide in korean language, in hangul script only:
    A detailed explanation of the meaning and significance

    User's reference: {user_input}

    """

    # Generate the response using the chat model
    response = client.invoke(prompt)

    # Extract the content from the response
    content = response.content

    # Return the cleaned response
    return content

def test_deepseek_bible_reference_3related(api_key: str, user_input: str) -> str:
    # Initialize the DeepSeek client
    client = ChatOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat"  # Replace with the correct model name
    )
    # Define the prompt for parsing the Bible reference
    prompt = f"""
    Parse the following Bible reference into a structured format.
    Please provide in korean language, in hangul script only:
    2-3 related Bible verses that share similar themes or messages (include brief explanations of why they're related).
    There may be misspelled book names or the user may be unaware of the exact book name, so please suggest the closest match from this list:
    "창세기", "출애굽기", "레위기", "민수기", "신명기", "여호수아", "사사기", "룻기",
    "사무엘상", "사무엘하", "열왕기상", "열왕기하", "역대상", "역대하", "에스라", "느헤미야",
    "에스더", "욥기", "시편", "잠언", "전도서", "아가", "이사야", "예레미야",
    "예레미야 애가", "에스겔", "다니엘", "호세아", "요엘", "아모스", "오바댜", "요나", "미가",
    "나훔", "하박국", "스바냐", "학개", "스가랴", "말라기", "마태복음", "마가복음", "누가복음", "요한복음", "사도행전", "로마서", "고린도전서", "고린도후서",
    "갈라디아서", "에베소서", "빌립보서", "골로새서", "데살로니가전서", "데살로니가후서",
    "디모데전서", "디모데후서", "디도서", "빌레몬서", "히브리서", "야고보서", "베드로전서", "베드로후서",
    "요한일서", "요한이서", "요한삼서", "유다서", "요한계시록".
    For 요한, make it 요한복음.

    User's reference: {user_input}

    """

    # Generate the response using the chat model
    response = client.invoke(prompt)

    # Extract the content from the response
    content = response.content

    # Return the cleaned response
    return content

if __name__ == "__main__":
    # Replace with your actual DeepSeek API key
    api_key = "sk-aa8bd243f87a40fca06fc6db5bca2ee9"
    
    # Get user input
    print("Enter a Bible reference (e.g., 'John 3:16'):")
    user_input = input("> ")

    # Fetch and print the Bible reference using DeepSeek
    
    # Print the Bible reference
    print("Theme from deepseek:")
    start_time = time.time()
    bible_theme = test_deepseek_bible_reference_1theme(api_key, user_input)
    end_time = time.time()
    time_taken = end_time - start_time 
    print(bible_theme)
    print(f"\nTime taken for theme deepseek: {time_taken:.2f} seconds\n")

    print("Theme from groq:")
    start_time = time.time()
    bible_theme_groq = test_groq_bible_ref_1theme()
    end_time = time.time()
    time_taken = end_time - start_time 
    print(bible_theme_groq)
    print(f"\nTime taken for theme groq: {time_taken:.2f} seconds\n")

    print("Deepseek Bible explanation:") 
    bible_explanation = test_deepseek_bible_reference_2explanation(api_key, user_input)
    print(bible_explanation)
    print("Deepseek Bible related:")
    bible_related = test_deepseek_bible_reference_3related(api_key, user_input)
    print(bible_related)