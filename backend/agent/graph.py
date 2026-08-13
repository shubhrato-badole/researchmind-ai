from typing import Optional
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
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


def get_thread_id(user_id: int, session_id: Optional[int]) -> str:
    """scope the LangGraph thread to the specific chat session, not just
    the user, so switching sessions or search modes doesn't reuse stale
    graph state built for a different tool configuration"""
    if session_id:
        return f"{user_id}:{session_id}"
    return str(user_id)


def get_tools_for_mode(user_id: int, search_mode: str):
    """
    web        -> web tool only, no approval needed, searches web directly
    docs       -> both tools, but asks approval before touching web
    docs_web   -> both tools, asks approval before touching web
    """
    from agent.tools import get_tools
    tools = get_tools(user_id)

    if search_mode == "web":
        return [tools[1]]
    return tools


def route_tools(state):
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None)
    if not tool_calls:
        return END

    tool_name = tool_calls[0]["name"]
    if tool_name == "search_internet":
        return "search_internet"
    return "search_documents"


def build_agent(tools, ask_before_web: bool = False):
    has_doc_tool = tools[0].name == "search_documents"
    doc_tool = tools[0] if has_doc_tool else None
    web_tool = tools[0] if not has_doc_tool else (tools[1] if len(tools) > 1 else None)

    bound_llm = get_llm().bind_tools(tools)

    def call_model(state):
        return {"messages": [bound_llm.invoke(state["messages"])]}

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)

    routes = {END: END}

    if doc_tool:
        workflow.add_node("search_documents", ToolNode([doc_tool]))
        routes["search_documents"] = "search_documents"
        workflow.add_edge("search_documents", "agent")

    if web_tool:
        workflow.add_node("search_internet", ToolNode([web_tool]))
        routes["search_internet"] = "search_internet"
        workflow.add_edge("search_internet", "agent")

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", route_tools, routes)

    interrupt = ["search_internet"] if (web_tool and ask_before_web) else []

    return workflow.compile(checkpointer=checkpointer, interrupt_before=interrupt)


def compress_history(history: list, max_tokens: int = 3000):
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


def build_system_prompt(long_term: list, search_mode: str = "docs_web"):
    prompt = "You are ResearchMind, a helpful AI assistant.\n\n"

    if search_mode == "web":
        prompt += "Search the web to answer the user's question.\n\n"
    else:
        prompt += """You have access to the user's personal knowledge base.
Always search documents first before searching the web.
If documents alone don't fully answer the question, you may also search the web after approval.

"""

    prompt += """If you see a ⚠ NOTE about a contradiction in the context — 
always mention it in your answer clearly like:
"⚠ Contradiction found: [source A] says X but [source B] says Y"
Even without a note — if you notice two sources disagreeing on a fact,
flag it the same way.

Always cite your sources clearly:
- If documents used → say "Based on your documents..."
- If web used → say "From web search..."
- If both were used → clearly state which part of the answer came from your documents and which part came from the web.
If you get NO_RESULTS from both tools say:
"I couldn't find enough information. Try uploading more documents on this topic."
Be concise and helpful.
If search_documents returns NO_DOCUMENTS:
- Tell the user that no documents have been uploaded yet.
- Ask them to upload a PDF, website, YouTube video, or other supported source.
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
            messages.append(AIMessage(content=msg["message"]))
    messages.append(HumanMessage(content=query))
    return messages


def _ensure_str(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


def run_agent(query: str, user_id: int, search_mode: str = "docs_web", session_id: Optional[int] = None):
    tools = get_tools_for_mode(user_id, search_mode)
    ask_before_web = search_mode != "web"

    history = get_chat_history(user_id, session_id)
    long_term = get_long_term_memory(user_id)
    compressed = compress_history(history)

    system_prompt = build_system_prompt(long_term, search_mode)
    messages = _build_messages(compressed, query, system_prompt)

    current_agent = build_agent(tools, ask_before_web)

    thread_id = get_thread_id(user_id, session_id)
    config = {"configurable": {"thread_id": thread_id}}

    result = current_agent.invoke({"messages": messages}, config=config)

    state = current_agent.get_state(config)
    if state.next and "search_internet" in str(state.next):
        return {
            "status": "awaiting_approval",
            "message": "I found limited info in your documents. Should I also search the web?",
            "thread_id": thread_id
        }

    final_answer = _ensure_str(result["messages"][-1].content)

    if final_answer.strip():
        save_message(user_id, "user", query, session_id)
        save_message(user_id, "assistant", final_answer, session_id)

    return {
        "status": "complete",
        "answer": final_answer
    }


def resume_agent(user_id: int, approved: bool, session_id: Optional[int] = None):
    from agent.tools import get_tools
    tools = get_tools(user_id)
    current_agent = build_agent(tools, ask_before_web=True)

    thread_id = get_thread_id(user_id, session_id)
    config = {"configurable": {"thread_id": thread_id}}

    if approved:
        result = current_agent.invoke(None, config=config)
        answer = result["messages"][-1].content
    else:
        state = current_agent.get_state(config)
        answer = state.values["messages"][-1].content

    answer = _ensure_str(answer)

    if answer.strip():
        save_message(user_id, "assistant", answer, session_id)

    return {
        "status": "complete",
        "answer": answer
    }


def stream_agent(query: str, user_id: int, search_mode: str = "docs_web", session_id: Optional[int] = None):
    tools = get_tools_for_mode(user_id, search_mode)
    ask_before_web = search_mode != "web"

    history = get_chat_history(user_id, session_id)
    long_term = get_long_term_memory(user_id)
    compressed = compress_history(history)

    system_prompt = build_system_prompt(long_term, search_mode)
    messages = _build_messages(compressed, query, system_prompt)

    current_agent = build_agent(tools, ask_before_web)

    thread_id = get_thread_id(user_id, session_id)
    config = {"configurable": {"thread_id": thread_id}}

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
                content = _ensure_str(msg.content)
                full_answer += content
                yield content

    if full_answer.strip():
        save_message(user_id, "user", query, session_id)
        save_message(user_id, "assistant", full_answer, session_id)