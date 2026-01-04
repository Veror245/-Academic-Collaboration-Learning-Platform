import getpass
import os
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")


# 2. Configuration
CHROMA_PATH = "chroma_db"  # Folder where vector data will be saved locally

# Initialize the Gemini Model (The "Brain")
llm = ChatGoogleGenerativeAI(
    model="gemma-3-1b-it",  # Fast and cheap model
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
    
    # B. Generate Summary (using the first 3 pages context)
    # We take a subset of text to avoid token limits for the summary
    summary_text = " ".join([d.page_content for d in docs[:3]])
    
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
    {summary_text[:5000]} 
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
        k=3, # Retrieve top 3 matching chunks
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
        "key concepts definitions", 
        k=4, 
        filter={"resource_id": resource_id} # type: ignore
    )
    
    context_text = "\n\n".join([doc.page_content for doc in results])
    
    # 2. Strict JSON Prompt
    quiz_prompt = f"""
    You are a quiz generator. Create 5 multiple-choice questions based on the text.
    
    STRICT OUTPUT FORMAT:
    Return ONLY a raw JSON array. Do not use Markdown.
    
    [
        {{
            "question": "Question text?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A"
        }}
    ]
    
    Rules:
    1. Ensure there is a comma between every item in the "options" list.
    2. Do not include explanations.
    
    Context:
    {context_text}
    """
    
    # 3. Retry Loop (The Safety Net)
    # If the AI messes up the JSON, we try again (up to 3 times)
    for attempt in range(3):
        try:
            print(f"🔄 Attempt {attempt+1} to generate quiz...")
            response = llm.invoke(quiz_prompt)
            content = response.content.strip() # type: ignore
            
            # Clean Markdown wrappers
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            
            # Try to parse
            quiz_data = json.loads(content)
            print("✅ Quiz generated successfully!")
            return quiz_data
            
        except json.JSONDecodeError:
            print(f"❌ JSON Error on attempt {attempt+1}. Retrying...")
            continue # Try again
            
    # If all 3 fail, return an empty list so the app doesn't crash
    print("🚨 All attempts failed.")
    return []