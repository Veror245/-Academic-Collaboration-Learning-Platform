# 🧠 Unimind - AI-Powered Collaborative Learning Platform

**Unimind** is a Retrieval-Augmented Generation (RAG) educational platform designed to revolutionize how students interact with study materials. It transforms static PDF notes into interactive knowledge bases, allowing students to generate quizzes, summaries, and have context-aware conversations with their textbooks.


## 🚀 Key Features

### 📚 1. Smart Document Repository
* **Room-Based Organization:** Files are sorted by subject (e.g., CS, Physics) for easy access.
* **AI Summarization:** Instantly generates a concise 3-sentence summary upon upload using **Google Gemini**.
* **Vector Embeddings:** Every uploaded PDF is chunked and embedded into **ChromaDB** for semantic search.

### 🤖 2. RAG-Powered AI Chat
* **Context-Aware:** Chat with specific documents. The AI answers strictly based on the provided notes, eliminating hallucinations.
* **"I Don't Know" Protocol:** If the answer isn't in the notes, the AI admits it rather than making things up—perfect for academic accuracy.

### 📝 3. Dynamic Quiz Generator
* **On-Demand MCQs:** Generates 5-question quizzes from random sections of the text.
* **Shuffled Context:** Uses random chunk sampling so no two quizzes are the same.
* **Self-Healing JSON:** Robust backend parsing ensures quizzes always render correctly, even if the AI formats output poorly.

### 🗳️ 4. Community Collaboration
* **Voting System:** Stack Overflow-style Upvote/Downvote system to highlight high-quality notes.
* **Duplicate Detection:** (Planned) Prevents redundant uploads.

---

## 🛠️ Tech Stack

### Backend
* **Framework:** Python (FastAPI)
* **Database:** SQLite (Metadata) + SQLAlchemy ORM
* **Vector Store:** ChromaDB (for RAG context)
* **Authentication:** JWT (JSON Web Tokens) + Passlib (Bcrypt)

### AI & ML
* **LLM:** Google Gemini (via LangChain Google GenAI)
* **Processing:** PyPDFLoader, RecursiveCharacterTextSplitter
* **Embedding Model:** Google Generative AI Embeddings

### Frontend
* **Core:** Vanilla JavaScript (ES6+), HTML5, CSS3
* **Design:** Glassmorphism UI
* **Communication:** Fetch API (REST)

---

## ⚙️ Architecture

The application follows a decoupled client-server architecture:

1.  **Ingestion:** PDF -> Text Extraction -> Cleaning -> Vector Embedding -> ChromaDB.
2.  **Retrieval:** User Query -> Similarity Search -> Context Retrieval -> LLM Generation -> Answer.

---

## 🔧 Installation & Setup

### Prerequisites
* Python 3.9+
* Google Gemini API Key

### 1. Backend Setup
```bash
# Clone the repository
git clone [https://github.com/Veror245/-Academic-Collaboration-Learning-Platform](https://github.com/Veror245/-Academic-Collaboration-Learning-Platform)
cd Academic-Collaboration-Learning-Platform/backend

# Create virtual environment
python -m venv myenv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt


# Set up Environment Variables
# Create a .env file and add:
# GOOGLE_API_KEY=your_key_here
# SECRET_KEY=your_jwt_secret

# Run the Server
fastapi dev main.py
```

### 2. Frontend Setup
The frontend is pure static HTML/JS. You can serve it using VS Code Live Server or Python:

```bash
cd ../frontend
python -m http.server 5500
```

## 📖 Usage Guide

Follow this flow to master your study materials:

1.  **🔐 Authenticate**
    * Create an account or log in to receive your secure **JWT Session Token**.
2.  **🏫 Enter a Room**
    * Select your subject domain (e.g., *Computer Science, Physics*).
3.  **📂 Knowledge Ingestion**
    * Upload any PDF lecture note.
    * *Watch the magic:* The AI instantly generates a concise summary in real-time.
4.  **🧠 Active Recall**
    * Click **"Take Quiz"** on any file to generate a unique 5-question MCQ test based strictly on that document.
5.  **💬 Socratic Chat**
    * Use the **Chat Interface** to ask specific questions (e.g., *"What is the definition of Entropy?"*).
    * *Result:* The AI provides answers cited directly from the text.

---

## 🛡️ Security Architecture

We prioritize data integrity and user safety:

* **🔑 Bcrypt Hashing:** Passwords are salted and hashed using `bcrypt` before ever touching the database.
* **🎫 Stateless Authentication:** All protected API endpoints require valid `HTTP Bearer` tokens.
* **🛡️ Injection Defense:** Rigorous **Regex sanitization** cleans all inputs to prevent prompt injection attacks and ensure clean text processing.