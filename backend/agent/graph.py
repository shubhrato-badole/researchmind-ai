from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from agent.tools import get_tools
from agent.memory import (
    get_chat_history,
    save_message,
    get_long_term_memory
)
from features.trust_score import get_trust_score
from retrieval.multi_query import multi_query_search
from config import GEMINI_API_KEY


llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GEMINI_API_KEY
)



checkpointer = MemorySaver()


agent = create_react_agent(
    llm,
    tools=[], 
    checkpointer=checkpointer,
    interrupt_before=["search_internet"]
)



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
Be concise and helpful."""

    if long_term:
        prompt += f"\n\nWhat I know about this user:\n" + "\n".join(long_term)

    return prompt

def run_agent(query: str, user_id: int, search_web: bool = False):
    tools = get_tools(user_id)

   
  
    if not search_web:
        tools = [tools[0]]

    
    history = get_chat_history(user_id)
    long_term = get_long_term_memory(user_id)

   
    compressed = compress_history(history)

   
    messages = []
    for msg in compressed:
        messages.append({
            "role": msg["role"],
            "content": msg["message"]
        })

    messages.append({"role": "user", "content": query})

    system_prompt = build_system_prompt(long_term)

   
    current_agent = create_react_agent(
        llm,
        tools,
        checkpointer=checkpointer,
        interrupt_before=["search_internet"] if len(tools) > 1 else []
    )

    config = {"configurable": {"thread_id": str(user_id)}}

    result = current_agent.invoke(
        {
            "messages": messages,
            "system": system_prompt
        },
        config=config
    )

    
    state = current_agent.get_state(config)
    if state.next and "search_internet" in str(state.next):
        return {
            "status": "awaiting_approval",
            "message": "I found limited info in your documents. Should I also search the web?",
            "thread_id": str(user_id)
        }

    final_answer = result["messages"][-1].content

   
    save_message(user_id, "user", query)
    save_message(user_id, "assistant", final_answer)

    return {
        "status": "complete",
        "answer": final_answer
    }

def resume_agent(user_id: int, approved: bool):
    """resume after human approval"""
    config = {"configurable": {"thread_id": str(user_id)}}

    tools = get_tools(user_id)

    current_agent = create_react_agent(
        llm,
        tools,
        checkpointer=checkpointer
    )

    if approved:
        result = current_agent.invoke(None, config=config)
        answer = result["messages"][-1].content
    else:
       
        state = current_agent.get_state(config)
        answer = state.values["messages"][-1].content

    save_message(user_id, "assistant", answer)

    return {
        "status": "complete",
        "answer": answer
    }

def stream_agent(query: str, user_id: int, search_web: bool = False):
    """stream answer token by token"""
    tools = get_tools(user_id)


    if not search_web:
        tools = [tools[0]]

    history = get_chat_history(user_id)
    long_term = get_long_term_memory(user_id)
    compressed = compress_history(history)

    messages = []
    for msg in compressed:
        messages.append({
            "role": msg["role"],
            "content": msg["message"]
        })
    messages.append({"role": "user", "content": query})

    system_prompt = build_system_prompt(long_term)

    current_agent = create_react_agent(
        llm,
        tools,
        checkpointer=checkpointer
    )

    config = {"configurable": {"thread_id": str(user_id)}}

    full_answer = ""

    for chunk in current_agent.stream(
        {
            "messages": messages,
            "system": system_prompt
        },
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


    save_message(user_id, "user", query)
    save_message(user_id, "assistant", full_answer)