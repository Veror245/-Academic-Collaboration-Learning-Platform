import getpass
import os
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import random
import re

load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")


# 2. Configuration
CHROMA_PATH = "chroma_db"  # Folder where vector data will be saved locally

# Initialize the Gemini Model (The "Brain")
llm = ChatGoogleGenerativeAI(
    model="gemma-3-27b-it",  
    temperature=0.3
)

# Initialize Embeddings (The "Translator" - Text to Numbers)
# We use FastEmbed (runs locally, no API cost, very fast)
embedding_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def process_document(file_path: str, resource_id: int):
    """
    Reads a PDF, stores it in Vector DB (for chat), and returns a summary.
    """
    print(f"🧠 AI Processing started for: {file_path}")

    # A. Load PDF Text
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    # We take a subset of text to avoid token limits for the summary
    clean_text = []
    pages_read_count = 0
    
    # Iterate through the first 20 pages
    for page in docs[:20]:
        text = page.page_content.strip()
        
        # FILTER: If page has less than 200 characters, it's likely a Map, Title, or Chapter Header.
        # Skip it!
        if len(text) < 200:
            continue
            
        clean_text.append(text)
        pages_read_count += 1
        
        # Stop once we have 5 solid pages of text
        if pages_read_count >= 5:
            break
            
    summary_text = " ".join(clean_text)
    
    summary_prompt = f"""
    You are a strict academic summarizer. 
    Summarize the following document in exactly 3 concise sentences.
    Focus on the main topic, key concepts, and the intended audience.
    
    CRITICAL INSTRUCTIONS:
    1. Return ONLY the 3 sentences. 
    2. Do NOT start with "Here is a summary" or "This document..."
    3. Do NOT end with "Would you like more help?"
    4. Provide raw text only.
    
    Document Text:
    {summary_text[:20000]} 
    """
    
    # Invoke Gemini
    ai_response = llm.invoke(summary_prompt)
    summary = ai_response.content

    # C. Prepare for Chat (RAG)
    # 1. Split text into chunks (AI can't read whole books at once)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)

    # 2. Add metadata (Critical: This tags every chunk with the Resource ID)
    # So when we search later, we only search THIS file.
    for chunk in chunks:
        chunk.metadata["resource_id"] = resource_id

    # 3. Store in ChromaDB (The Vector Database)
    # This creates a persistent database folder on your disk
    vector_store = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_model
    )
    vector_store.add_documents(chunks)
    
    print(f"✅ AI Processing complete. Summary: {summary}")
    return summary



def chat_with_document(resource_id: int, question: str, history: list = []):
    print(f"💬 Chatting with Resource {resource_id}: {question}")
    
    # 1. Connect to the existing Vector Database
    vector_store = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_model
    )
    
    history_text = ""
    for msg in history:
        role = "User" if msg['role'] == 'user' else "AI"
        history_text += f"{role}: {msg['content']}\n"
    
    # 2. Search for relevant context
    # We use a filter to ensure we ONLY search within the specific file the user is asking about
    results = vector_store.similarity_search(
        question, 
        k=10, # Retrieve top 3 matching chunks
        filter={"resource_id": resource_id} # type: ignore
    )
    
    # 3. Combine the retrieved chunks into one block of text
    context_text = "\n\n".join([doc.page_content for doc in results])
    
    if not context_text:
        return "I couldn't find any relevant information in this document."

    # 4. Construct the Prompt for Gemma
    chat_prompt = f"""
    You are a helpful teaching assistant.
    
    Instructions:
    1. Answer the user's question using the 'Context from Document' below.
    2. If the user refers to previous messages (like "what did you just say?", "elaborate on that"), use the 'Chat History'.
    3. If the answer is nowhere to be found, say "I don't know."
    
    Chat History:
    {history_text}
    
    Context from Document:
    {context_text}
    
    User Question: {question}
    
    Answer:
    """
    
    print("---------------- PROMPT DEBUG START ----------------")
    print(chat_prompt)
    print("---------------- PROMPT DEBUG END ----------------")
    # ---------------------
    
    # 5. Get Answer
    response = llm.invoke(chat_prompt)
    return response.content

def generate_quiz(resource_id: int):
    print(f"📝 Generating Quiz for Resource {resource_id}")
    
    # 1. Get Context
    vector_store = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_model
    )
    
    results = vector_store.similarity_search(
        "summary main concepts definitions core ideas facts importance syllabus", 
        k=20,  # <--- Grab a huge bucket of text
        filter={"resource_id": resource_id} # type: ignore
    )
    
    num_chunks_to_use = min(5, len(results)) # Safety check if PDF is small
    selected_docs = random.sample(results, num_chunks_to_use)
    
    raw_text = "\n\n".join([doc.page_content for doc in selected_docs])
    # Remove excessive newlines and multiple spaces
    context_text = re.sub(r'\s+', ' ', raw_text).strip()
    
    print(context_text)
    
    print(f"🎲 Selected {num_chunks_to_use} random chunks for context.")
    
    quiz_prompt = f"""
    You are an expert teacher creating a quiz. 
    Analyze the text below and create 5 multiple-choice questions.

    CRITICAL INSTRUCTIONS:
    1. IGNORE course codes (like "STAT-MD-CC1", "SEC2-2", etc.). Do NOT ask what a course code means.
    2. Focus ONLY on the *concepts*, *definitions*, and *topics* described in the text.
    3. You MUST provide 4 options for every question.
    4. You MUST provide the correct answer.
    5. Ensure there is a comma between every item in the "options" list.
    6. Do not include explanations.
    7. Return the quiz in the JSON FORMAT ONLY DO NOT RETURN IN MARKDOWN OR ANY OTHER FORMATTING.
    8. PROVIDE MAXIMUM 5 QUESTIONS.
    9. If you cannot generate 5 questions based on the text, generate as many as you can BUT NOT MORE THAN 5.
    10. STRICTLY FOLLOW THE FORMAT GIVEN BELOW.
    11. DO NOT RESPOND WITH ANYTHING OTHER THAN THE JSON.
    

    STRICT JSON STRUCTURE (Use this format, but replace the content):
    [
        {{
            "question": "Write the question here based on the text?",
            "options": [
                {{"id": "A", "text": "First option text"}},
                {{"id": "B", "text": "Second option text"}},
                {{"id": "C", "text": "Third option text"}},
                {{"id": "D", "text": "Fourth option text"}}
            ],
            "answer": "A"
        }}
    ]

    CONTEXT TO USE (The real content):
    {context_text}
    """

    
    # 3. Retry Loop (The Safety Net)
    # If the AI messes up the JSON, we try again (up to 3 times)
    for attempt in range(3):
        try:
            print(f"🔄 Attempt {attempt+1} to generate quiz...")
            response = llm.invoke(quiz_prompt)
            content = response.content.strip() # type: ignore
            
            print(f"🤖 RAW AI REPLY: {content[:200]}...")
            
            # Clean Markdown wrappers
            json_match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                quiz_data = json.loads(json_str)
                
                if not quiz_data or "options" not in quiz_data[0]:
                    raise ValueError("AI returned JSON missing 'options' field")
                
                # Handle edge case: If AI returned {"quiz": [...]}, extract the list
                if isinstance(quiz_data, dict):
                    # Look for any key that holds a list
                    for key, value in quiz_data.items():
                        if isinstance(value, list):
                            quiz_data = value
                            break
                            
                print("✅ Quiz generated successfully!")
                return quiz_data[:5]
            else:
                print(f"⚠️ No JSON found. Raw Content: {content}")
                continue
            
        except Exception as e:
            print(f"❌ Error on attempt {attempt+1}: {e}")
            continue
            
    # If all 3 fail, return an empty list so the app doesn't crash
    print("🚨 All attempts failed.")
    return []