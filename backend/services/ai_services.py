import getpass
import os
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


    
