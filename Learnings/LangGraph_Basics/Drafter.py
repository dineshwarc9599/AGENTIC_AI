import os
from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv  

from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
)
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from langchain_groq import ChatGroq   

load_dotenv()

document_content = ""



class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

@tool
def update(content: str) -> str:
    """Updates the document with the provided content."""
    global document_content
    document_content = content
    return f"Document updated successfully.\nCurrent content:\n{document_content}"


@tool
def save(filename: str) -> str:
    """Save the current document to a text file and finish the process."""
    global document_content

    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"

    try:
        with open(filename, "w") as f:
            f.write(document_content)

        print(f"\n Saved to: {filename}")
        return f"Document saved successfully to '{filename}'."

    except Exception as e:
        return f"Error saving document: {str(e)}"


tools = [update, save]

model = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
).bind_tools(tools)


def our_agent(state: AgentState) -> AgentState:

    system_prompt = SystemMessage(content=f"""
You are Drafter, a helpful writing assistant.

Rules:
- If user wants to modify document → use 'update' tool
- If user wants to save → use 'save' tool
- Always maintain latest document content

Current document:
{document_content}
""")

    # First message
    if not state["messages"]:
        user_input = "I'm ready to help you create or edit a document."
    else:
        user_input = input("\n What would you like to do? ")

    print(f"\n USER: {user_input}")

    user_message = HumanMessage(content=user_input)

    messages = [system_prompt] + list(state["messages"]) + [user_message]

    response = model.invoke(messages)

    print(f"\n AI: {response.content}")

    if hasattr(response, "tool_calls") and response.tool_calls:
        print(f" TOOL CALLS: {[tc['name'] for tc in response.tool_calls]}")

    return {
        "messages": list(state["messages"]) + [user_message, response]
    }


def should_continue(state: AgentState) -> str:
    messages = state["messages"]

    if not messages:
        return "continue"

    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            if "saved" in msg.content.lower():
                return "end"

    return "continue"

def print_messages(messages):
    for msg in messages[-3:]:
        if isinstance(msg, ToolMessage):
            print(f"\nTOOL RESULT: {msg.content}")


graph = StateGraph(AgentState)

graph.add_node("agent", our_agent)
graph.add_node("tools", ToolNode(tools))

graph.set_entry_point("agent")

graph.add_edge("agent", "tools")

graph.add_conditional_edges(
    "tools",
    should_continue,
    {
        "continue": "agent",
        "end": END,
    },
)


app = graph.compile()

def run_document_agent():
    print("\n====== DRAFTER ======\n")

    state = {"messages": []}

    for step in app.stream(state, stream_mode="values"):
        if "messages" in step:
            print_messages(step["messages"])

    print("\n====== FINISHED ======")


if __name__ == "__main__":
    run_document_agent()