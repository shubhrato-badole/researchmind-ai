from typing import Optional
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from agent.memory import (
    get_chat_history,
    save_message,
    get_long_term_memory
)
from config import GEMINI_API_KEY
from functools import lru_cache



@lru_cache(maxsize=1)
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=GEMINI_API_KEY
)


checkpointer = MemorySaver()


def route_tools(state):
    """Decide which tool node to go to based on the tool the LLM chose."""
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None)
    if not tool_calls:
        return END

    tool_name = tool_calls[0]["name"]
    if tool_name == "search_internet":
        return "search_internet"
    return "search_documents"


def build_agent(tools):
    """Build a graph where search_documents auto-executes but
    search_internet pauses for human approval before running."""

    doc_tool = tools[0]
    web_tool = tools[1] if len(tools) > 1 else None

    bound_llm = get_llm().bind_tools(tools)

    def call_model(state):
        return {"messages": [bound_llm.invoke(state["messages"])]}

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("search_documents", ToolNode([doc_tool]))

    if web_tool:
        workflow.add_node("search_internet", ToolNode([web_tool]))

    workflow.set_entry_point("agent")

    routes = {"search_documents": "search_documents", END: END}
    if web_tool:
        routes["search_internet"] = "search_internet"

    workflow.add_conditional_edges("agent", route_tools, routes)
    workflow.add_edge("search_documents", "agent")
    if web_tool:
        workflow.add_edge("search_internet", "agent")

    interrupt = ["search_internet"] if web_tool else []

    return workflow.compile(checkpointer=checkpointer, interrupt_before=interrupt)


def compress_history(history: list, max_tokens: int = 3000):
    """keep only recent messages that fit within token budget"""
    total_chars = max_tokens * 4
    compressed = []
    current_chars = 0

    for msg in reversed(history):
        msg_chars = len(msg["message"])
        if current_chars + msg_chars > total_chars:
            break
        compressed.insert(0, msg)
        current_chars += msg_chars

    return compressed


def build_system_prompt(long_term: list):
    prompt = """You are ResearchMind, a helpful AI assistant.

You have access to the user's personal knowledge base.
Always search documents first before searching the web.

If you see a ⚠ NOTE about a contradiction in the context — 
always mention it in your answer clearly like:
"⚠ Contradiction found: [source A] says X but [source B] says Y"
Even without a note — if you notice two sources disagreeing on a fact,
flag it the same way.

Always cite your sources clearly:
- If documents used → say "Based on your documents..."
- If web used → say "From web search..."
- If both → say which part came from where.
If you get NO_RESULTS from both tools say:
"I couldn't find enough information. Try uploading more documents on this topic."
Be concise and helpful.
If search_documents returns NO_DOCUMENTS:
- Tell the user that no documents have been uploaded yet.
- Ask them to upload a PDF, website, YouTube video, or other supported source.
- Do NOT search the web if the request is specifically about "my documents", "my PDF", "my notes", "my files", or "summarize my document".
"""

    if long_term:
        prompt += f"\n\nWhat I know about this user:\n" + "\n".join(long_term)

    return prompt


def _build_messages(compressed, query, system_prompt):
    messages = [SystemMessage(content=system_prompt)]
    for msg in compressed:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["message"]))
        else:
            messages.append({"role": msg["role"], "content": msg["message"]})
    messages.append(HumanMessage(content=query))
    return messages


def run_agent(query: str, user_id: int, search_web: bool = False , session_id: Optional[int] = None):
    from agent.tools import get_tools
    tools = get_tools(user_id)

    if not search_web:
        tools = [tools[0]]

    history = get_chat_history(user_id , session_id)
    long_term = get_long_term_memory(user_id)
    compressed = compress_history(history)

    system_prompt = build_system_prompt(long_term)
    messages = _build_messages(compressed, query, system_prompt)

    current_agent = build_agent(tools)

    config = {"configurable": {"thread_id": str(user_id)}}

    result = current_agent.invoke({"messages": messages}, config=config)

    state = current_agent.get_state(config)
    if state.next and "search_internet" in str(state.next):
        return {
            "status": "awaiting_approval",
            "message": "I found limited info in your documents. Should I also search the web?",
            "thread_id": str(user_id)
        }

    final_answer = result["messages"][-1].content

    save_message(user_id, "user", query , session_id)
    save_message(user_id, "assistant", final_answer , session_id)

    return {
        "status": "complete",
        "answer": final_answer
    }


def resume_agent(user_id: int, approved: bool, session_id: Optional[int] = None):
    from agent.tools import get_tools
    """resume after human approval"""
    config = {"configurable": {"thread_id": str(user_id)}}

    tools = get_tools(user_id)
    current_agent = build_agent(tools)

    if approved:
        result = current_agent.invoke(None, config=config)
        answer = result["messages"][-1].content
    else:
        state = current_agent.get_state(config)
        answer = state.values["messages"][-1].content

    save_message(user_id, "assistant", answer, session_id)

    return {
        "status": "complete",
        "answer": answer
    }


def stream_agent(query: str, user_id: int, search_web: bool = False , session_id: int | None = None):
    from agent.tools import get_tools
    """stream answer token by token"""
    tools = get_tools(user_id)

    if not search_web:
        tools = [tools[0]]

    history = get_chat_history(user_id)
    long_term = get_long_term_memory(user_id)
    compressed = compress_history(history)

    system_prompt = build_system_prompt(long_term)
    messages = _build_messages(compressed, query, system_prompt)

    current_agent = build_agent(tools)

    config = {"configurable": {"thread_id": str(user_id)}}

    full_answer = ""

    for chunk in current_agent.stream(
        {"messages": messages},
        config=config,
        stream_mode="messages"
    ):
        if chunk and isinstance(chunk, tuple):
            msg, metadata = chunk
            if (
                hasattr(msg, "content")
                and msg.content
                and metadata.get("langgraph_node") == "agent"
            ):
                full_answer += msg.content
                yield msg.content

    save_message(user_id, "user", query ,  session_id)
    save_message(user_id, "assistant", full_answer , session_id)





