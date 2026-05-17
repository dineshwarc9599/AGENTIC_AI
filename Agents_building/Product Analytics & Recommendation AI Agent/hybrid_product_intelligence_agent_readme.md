# Hybrid Product Intelligence Agent

An enterprise-level AI-powered Product Question & Answer Agent built using:

- FastAPI
- Groq LLM
- ChromaDB Vector Database
- Sentence Transformers Embeddings
- Pandas DataFrame Intelligence
- Hybrid Retrieval Architecture
- HTML/CSS/JavaScript Frontend

This system combines:
- semantic product retrieval
- exact dataframe analytics
- hybrid recommendation intelligence
- natural language reasoning

to create a powerful AI product assistant.

---

# Features

## Hybrid AI Architecture

Supports:
- Structured analytical queries
- Semantic recommendation queries
- Hybrid filtering + recommendation queries

---

## Exact DataFrame Analytics

Supports:
- minimum / maximum price
- average calculations
- count operations
- filtering
- aggregations

using the FULL dataset.

---

## Semantic Product Retrieval

Uses:
- sentence-transformer embeddings
- ChromaDB vector similarity search
- Groq LLM reasoning

for intelligent recommendations.

---

## Dynamic Query Routing

Automatically detects:
- analytical queries
- semantic queries
- hybrid recommendation queries

and routes them to the correct AI pipeline.

---

## Human-Friendly Responses

The agent:
- removes internal laptop IDs
- formats clean summaries
- generates professional recommendations

---

# Project Architecture

```text
                User Question
                       ↓
               Query Classifier
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓

 Structured       Semantic        Hybrid
 Queries           Queries        Queries

    ↓                ↓               ↓

Pandas Engine    Vector Search   Filter + Retrieval

    ↓                ↓               ↓

Exact Result     Relevant Docs   Ranked Results

        └────────── Groq LLM ─────────┘
                       ↓
                Final Response
```

---

# Project Structure

```text
Product_QA_Agent/
│
├── backend/
│   │
│   ├── main.py
│   ├── rag.py
│   ├── vector_db.py
│   ├── embeddings.py
│   ├── groq_client.py
│   ├── dataframe_agent.py
│   ├── query_generator.py
│   ├── safe_executor.py
│   ├── query_classifier.py
│   ├── response_formatter.py
│   ├── prompts.py
│   ├── config.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── data/
│   └── laptop_price.csv
│
├── chroma_storage/
│
└── README.md
```

---

# Technology Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| LLM | Groq |
| Embeddings | Sentence Transformers |
| Vector Database | ChromaDB |
| Analytics | Pandas |
| Frontend | HTML/CSS/JavaScript |
| Query Intelligence | Hybrid AI Routing |

---

# Installation

## Clone Repository

```bash
git clone <repository_url>
```

```bash
cd Product_QA_Agent
```

---

# Create Virtual Environment

```bash
cd backend
```

```bash
python -m venv venv
```

---

# Activate Environment

## Windows

```bash
venv\Scripts\activate
```

## Linux / Mac

```bash
source venv/bin/activate
```

---

# Install Requirements

```bash
pip install -r requirements.txt
```

---

# Configure Environment Variables

Create:

```text
backend/.env
```

Add:

```env
GROQ_API_KEY=your_groq_api_key

MODEL_NAME=llama3-70b-8192
```

---

# Dataset

Place dataset inside:

```text
data/laptop_price.csv
```

---

# Run Backend

```bash
uvicorn main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Run Frontend

Open:

```text
frontend/index.html
```

using:
- VS Code Live Server

OR simply open in browser.

---

# Example Questions

## Structured Queries

```text
Which laptop has the minimum price?
```

```text
What is the average laptop price?
```

```text
How many HP laptops exist?
```

```text
Show gaming laptops under 1500 Euros
```

---

## Semantic Queries

```text
Suggest laptops for coding
```

```text
Recommend lightweight laptops
```

```text
Best laptops for students
```

---

## Hybrid Queries

```text
Best gaming laptop under 2000 Euros
```

```text
Recommend affordable laptops with SSD
```

```text
Suggest laptops for AI development under 3000 Euros
```

---

# API Endpoint

## POST `/ask`

### Request

```json
{
  "question": "Which laptop has the minimum price?"
}
```

---

### Response

```json
{
  "query_type": "structured",
  "answer": "The laptop with the minimum price is Acer C740-C9QX priced at 174 Euros."
}
```

---

# Key AI Components

| Component | Purpose |
|---|---|
| Query Classifier | Detects query type |
| DataFrame Agent | Exact analytical computation |
| Vector Retrieval | Semantic product search |
| Groq LLM | Natural language reasoning |
| Safe Executor | Secure pandas execution |
| Response Formatter | Human-friendly summaries |

---

# Enterprise AI Concepts Implemented

This project demonstrates:

- Retrieval-Augmented Generation (RAG)
- Hybrid AI Retrieval
- Semantic Search
- DataFrame Agents
- Query Routing
- Vector Databases
- LLM-Orchestrated Reasoning
- Context Engineering
- AI Recommendation Systems

---

# Security Features

The system includes:
- restricted code execution
- blocked dangerous operations
- safe pandas query evaluation
- hallucination reduction
- clean response formatting

---

# Frontend Features

- Modern AI dashboard UI
- Real-time chat interface
- Loading animations
- Sample question cards
- Responsive design
- Backend API integration

---

# Future Improvements

Potential upgrades:

- SQL Agent Integration
- Conversational Memory
- Multi-turn Chat
- Authentication
- Streamlit Dashboard
- Recommendation Ranking
- User Personalization
- Real-Time Product APIs
- Docker Deployment
- Cloud Hosting

---

# Notes

## Dataset Usage

The dataset used in this project is intended solely for educational and development purposes.

Internal identifiers such as:
- `laptop_ID`

are preserved in backend processing but hidden from user-facing responses.

---

## Disclaimer

The templates, deliverables, and supporting resources used in this project are synthetically generated for demonstration and development purposes only.

No confidential, proprietary, or real enterprise data has been used in this repository.

This project is intended to showcase the architecture, workflow, and capabilities of an AI-powered