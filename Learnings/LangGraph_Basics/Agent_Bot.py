from typing import TypedDict,List 
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph,START,END 
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["GROQ_API_KEY"] ="GROQ_API_KEY"
class AgentState(TypedDict):
    messages: list[HumanMessage]
    

llm = ChatGroq(model="llama-3.3-70b-versatile",)

def process_messages(state:AgentState) -> str:
    response = llm.invoke(state['messages'])
    print(f"LLM Response: {response.content}")
    return state

graph = StateGraph(AgentState)
graph.add_node('process',process_messages)
graph.add_edge(START,'process')
graph.add_edge('process', END)
agent = graph.compile()

user_input = input('Enter your message:')

