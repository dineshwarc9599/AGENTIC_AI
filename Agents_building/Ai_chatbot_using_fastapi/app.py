from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from pathlib import Path
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, Sequence, TypedDict, Literal
from pathlib import Path
from fastapi.responses import FileResponse, JSONResponse
import os
import warnings
 
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import create_retriever_tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
 
warnings.filterwarnings('ignore')
 
load_dotenv(dotenv_path='.env')
if not os.getenv("GROQ_API_KEY"):
    load_dotenv(dotenv_path='_env')  
 
app = FastAPI()
 
@app.get("/favicon.ico")
async def favicon():
    if Path("favicon.ico").exists():
        return FileResponse("favicon.ico")
    return JSONResponse(content={}, status_code=204)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
groq_api_key = os.getenv("GROQ_API_KEY")
 
if not groq_api_key:
    raise RuntimeError(
        "GROQ_API_KEY not found! Make sure your .env or _env file is in the same folder as app.py"
    )
 
print(f"GROQ API Key loaded: {groq_api_key[:8]}...")
 
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
 
CACHE_FILE = 'cached_blog.txt'
 
if Path(CACHE_FILE).exists():
    print("Loading blog content from cache...")
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        raw_content = f.read()
else:
    print("Fetching blog content from web...")
    docs = WebBaseLoader(
        "https://medium.com/towards-artificial-intelligence/ai-agents-explained-theory-applications-and-python-implementation-5de81ce7cd92"
    ).load()
    raw_content = docs[0].page_content
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        f.write(raw_content)
    print("Blog content cached.")
 
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=1000, chunk_overlap=200
)
doc_splits = text_splitter.split_documents([Document(page_content=raw_content)])
 
VECTOR_DIR = 'chroma_db'
 
vectorstore = Chroma(
    collection_name="rag_collection",
    embedding_function=embeddings,
    persist_directory=VECTOR_DIR
)
 
if vectorstore._collection.count() == 0:
    print(" Adding documents to Chroma vector store...")
    vectorstore.add_documents(doc_splits)
    print("Documents added.")
else:
    print(f"Chroma already has {vectorstore._collection.count()} documents.")
 
retriever = vectorstore.as_retriever()
 
retriever_tool = create_retriever_tool(
    retriever,
    'retrieve_blog_posts',
    'Retrieves content from AI agents blog post. Use this for questions about AI agents, their theory, applications, and Python implementation.'
)
 
tools = [retriever_tool]
 
 
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
 
 
class GradeOutput(BaseModel):
    binary_score: str = Field(description="'yes' or 'no'")
 
 
def grade_documents(state) -> Literal["generate", "rewrite"]:
    print("=== [NODE: GRADE DOCUMENTS] ===")
    model = ChatGroq(
        temperature=0,
        model="llama-3.1-8b-instant",
        api_key=groq_api_key
    ).with_structured_output(GradeOutput)
 
    messages = state["messages"]
    question = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            question = msg.content
            break
 
    context = ""
    if messages:
        last = messages[-1]
        if hasattr(last, "content"):
            content = last.content
            if isinstance(content, list):
                context = " ".join(
                    c.get("text", "") if isinstance(c, dict) else str(c)
                    for c in content
                )
            else:
                context = str(content)
 
    prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user question.
Document:
{context}
 
Question: {question}
 
Is the document relevant to answering the question? Answer only 'yes' or 'no'.""",
        input_variables=["context", "question"]
    )
 
    try:
        result = (prompt | model).invoke({"context": context, "question": question})
        score = result.binary_score.strip().lower()
    except Exception as e:
        print(f"Grading error: {e} — defaulting to generate")
        score = "yes"
 
    if score == "yes":
        print("=== [DECISION: DOCS RELEVANT → generate] ===")
        return "generate"
    else:
        print("=== [DECISION: DOCS NOT RELEVANT → rewrite] ===")
        return "generate"
 
 
from langchain_core.messages import SystemMessage

def agent(state):
    print("=== [NODE: AGENT] ===")
    messages = state["messages"]

    system_msg = SystemMessage(
        content="""You are an AI assistant.

You can use tools when needed to retrieve information.

If the question requires external knowledge, call the appropriate tool.
Otherwise, answer directly."""
    )

    llm = ChatGroq(
        temperature=0,
        model="llama-3.1-8b-instant",
        api_key=groq_api_key
    )

    llm_with_tools = llm.bind_tools(tools)

    response = llm_with_tools.invoke([system_msg] + list(messages))

    return {"messages": [response]}
 
 
def rewrite(state):
    print("=== [NODE: REWRITE] ===")
    messages = state["messages"]
 
    question = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            question = msg.content
            break
 
    msg = [
        HumanMessage(
            content=f"""Rephrase the question ONLY for better retrieval.

IMPORTANT:
- Do NOT explain anything
- Do NOT answer the question
- Do NOT add extra sentences
- Just return a cleaner search-friendly version

Question:
{question}

 
Rewritten question:"""
        )
    ]
    model = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=groq_api_key)
    response = model.invoke(msg)
    return {"messages": [response]}
 
 
def generate(state):
    print("=== [NODE: GENERATE] ===")
    messages = state["messages"]
 
    question = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            question = msg.content
            break
 
    docs = ""
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            content = msg.content
            if isinstance(content, list):
                docs = " ".join(
                    c.get("text", "") if isinstance(c, dict) else str(c)
                    for c in content
               )
            else:
                docs = str(content)
            break
 
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are a helpful AI assistant.

Answer the user's question directly.

STRICT RULES:
- Do NOT rewrite the question
- Do NOT explain the question
- Do NOT rephrase anything
- ONLY give the final answer
- If context is empty, answer from your own knowledge
Context:
---------
{context}
---------
 
Question: {question}
 
Answer:"""
    )
 
    llm_gen = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=groq_api_key)
    response = (prompt | llm_gen | StrOutputParser()).invoke({
        "context": docs,
        "question": question
    })
    return {"messages": [AIMessage(content=response)]}
 
workflow = StateGraph(AgentState)
 
workflow.add_node("agent", agent)
workflow.add_node("tools", ToolNode([retriever_tool]))
workflow.add_node("rewrite", rewrite)
workflow.add_node("generate", generate)
 
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_conditional_edges("tools", grade_documents)
workflow.add_edge("generate", END)
workflow.add_edge("rewrite", "agent")
 
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
 
try:
    if not Path("visualization.png").exists():
        image_data = graph.get_graph().draw_mermaid_png()
        with open("visualization.png", "wb") as f:
            f.write(image_data)
        print("Graph visualization saved.")
except Exception as e:
    print(f"Could not generate graph visualization: {e}")
 
 
class Query(BaseModel):
    message: str
    session_id: str = "default_session"  
 
 
@app.get("/")
async def serve_html():
    html_path = Path(r"F:\LLMS\Agentic_Ai_chatbot\chatbot_ui_design.html")
    if not html_path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "chatbot_ui_design.html not found. Place it in the same folder as app.py."}
        )
    return FileResponse(r"F:\LLMS\Agentic_Ai_chatbot\chatbot_ui_design.html")
 
@app.post("/chat")
async def chat_endpoint(query: Query):
    try:
        print(f"\n=== USER QUERY === {query.message}")
        print(f"=== SESSION ID === {query.session_id}")
 
        # FIX 11: Pass thread_id config for memory to work properly
        config = {"configurable": {"thread_id": query.session_id}}
 
        events = graph.stream(
            {"messages": [HumanMessage(content=query.message)]},
            config=config,
            stream_mode="values"
        )
 
        response = ""
        for event in events:
            if "messages" in event:
                last_msg = event["messages"][-1]
                if hasattr(last_msg, "content"):
                    content = last_msg.content
                    # Only capture non-empty string responses (not tool calls)
                    if isinstance(content, str) and content.strip():
                        response = content
 
        print(f"FINAL RESPONSE: {response[:200]}...")
 
        if not response:
            response = "I'm sorry, I couldn't find a relevant answer. Please try rephrasing your question."
 
        return JSONResponse(content={"response": response})
 
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Server error: {str(e)}"}
        )
