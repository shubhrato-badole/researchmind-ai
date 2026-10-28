from functools import lru_cache
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from agent.memory import get_chat_history, get_long_term_memory, save_message
from config import GEMINI_API_KEY


@lru_cache(maxsize=1)
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=GEMINI_API_KEY,
    )


checkpointer = MemorySaver()


def get_thread_id(user_id: int, session_id: Optional[int]) -> str:
    """Scope LangGraph state to a chat session when one is provided."""
    if session_id:
        return f"{user_id}:{session_id}"
    return str(user_id)


def get_tools_for_mode(user_id: int, search_mode: str):
    """Return only the tools permitted for the selected search mode."""
    from agent.tools import get_tools

    tools = {tool.name: tool for tool in get_tools(user_id)}

    if search_mode == "docs":
        return [
            tools["search_documents"],
            tools["search_documents_multi_query"],
        ]

    if search_mode == "web":
        return [tools["search_internet"]]

    if search_mode == "docs_web":
        return [
            tools["search_documents"],
            tools["search_documents_multi_query"],
            tools["search_internet"],
        ]

    raise ValueError(f"Unsupported search mode: {search_mode}")


def _ensure_str(content) -> str:
    """Convert message content into a string."""
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


def _current_turn_has_empty_document_search(messages: list) -> bool:
    """
    Check whether document search returned no results during the current turn.

    This prevents multi-query from being offered after an empty or failed
    original document search, without blocking it on later, separate turns.
    """
    last_user_index = None

    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            last_user_index = index
            break

    if last_user_index is None:
        return False

    for message in messages[last_user_index + 1:]:
        if getattr(message, "name", None) != "search_documents":
            continue

        content = _ensure_str(
            getattr(message, "content", "")
        ).strip()

        if not content.startswith("[DOCUMENT_SEARCH_CALL:"):
            continue

        parts = content.split("\n", 1)
        outcome = parts[1].strip() if len(parts) > 1 else ""

        if outcome in {"NO_RESULTS", "SEARCH_ERROR"}:
            return True

    return False


def route_tools(state):
    """Route the agent to the tool requested by its latest message."""
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None)

    if not tool_calls:
        return END

    tool_name = tool_calls[0]["name"]

    if tool_name == "search_documents":
        return "search_documents"

    if tool_name == "search_documents_multi_query":
        return "search_documents_multi_query"

    if tool_name == "search_internet":
        return "search_internet"

    # An unexpected tool name should end the graph safely.
    return END


def build_agent(tools, ask_before_web: bool = False):
    """Build a LangGraph agent with optional multi-query recovery."""
    doc_tool = next(
        (
            tool for tool in tools
            if tool.name == "search_documents"
        ),
        None,
    )

    multi_query_tool = next(
        (
            tool for tool in tools
            if tool.name == "search_documents_multi_query"
        ),
        None,
    )

    web_tool = next(
        (
            tool for tool in tools
            if tool.name == "search_internet"
        ),
        None,
    )

    bound_llm = get_llm().bind_tools(tools)

    def call_model(state):
        messages = state["messages"]

        # If document search returned no results during this turn,
        # keep the normal agent response flow but disable multi-query.
        if _current_turn_has_empty_document_search(messages):
            available_tools = [
                tool for tool in tools
                if tool.name != "search_documents_multi_query"
            ]

            if available_tools:
                model = get_llm().bind_tools(available_tools)
            else:
                model = get_llm()

            return {
                "messages": [model.invoke(messages)]
            }

        return {
            "messages": [bound_llm.invoke(messages)]
        }

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)

    routes = {END: END}

    if doc_tool:
        workflow.add_node(
            "search_documents",
            ToolNode([doc_tool]),
        )
        routes["search_documents"] = "search_documents"
        workflow.add_edge("search_documents", "agent")

    if multi_query_tool:
        workflow.add_node(
            "search_documents_multi_query",
            ToolNode([multi_query_tool]),
        )
        routes["search_documents_multi_query"] = (
            "search_documents_multi_query"
        )
        workflow.add_edge(
            "search_documents_multi_query",
            "agent",
        )

    if web_tool:
        workflow.add_node(
            "search_internet",
            ToolNode([web_tool]),
        )
        routes["search_internet"] = "search_internet"
        workflow.add_edge("search_internet", "agent")

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", route_tools, routes)

    interrupt = (
        ["search_internet"]
        if web_tool and ask_before_web
        else []
    )

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt,
    )


def compress_history(history: list, max_tokens: int = 3000):
    """Keep recent chat history within an approximate character limit."""
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


def build_system_prompt(
    long_term: list,
    search_mode: str = "docs_web",
):
    """Build system instructions for the selected search mode."""
    prompt = "You are ResearchMind, a helpful AI assistant.\n\n"

    if search_mode == "web":
        prompt += """Use web search to answer the user's question.
Use retrieved web-search results as evidence.
Do not ask the user to upload documents.
Do not claim that document search failed.

"""

    elif search_mode == "docs":
        prompt += """Use only the user's personal knowledge base.
Search documents to answer the user's question.
Do not attempt web search.

"""

    elif search_mode == "docs_web":
        prompt += """Search the user's documents first.
If the documents do not fully answer the question, request approval
before searching the web. Clearly distinguish document and web sources.

"""

    else:
        raise ValueError(f"Unsupported search mode: {search_mode}")

    prompt += """EVIDENCE SUFFICIENCY AND BOUNDED RETRY:

- Retrieved chunks are candidate evidence, not automatic proof that a
  question has been answered.
- After document search, check whether the returned evidence directly
  supports the answer, including relevant entities, scope, dates,
  versions, units, and conditions.
- If the evidence is sufficient, answer without another search.
- If the original document search returns NO_RESULTS or SEARCH_ERROR,
  do not call search_documents_multi_query. Continue the normal response
  workflow and explain the limitations when appropriate.
- If document search returns actual chunks but the evidence is insufficient,
  vague, or tangential, call search_documents_multi_query once.
- For that tool call, pass the original question as query and up to three
  meaningfully different formulations as alternate_queries.
- Generate the alternate formulations directly as tool-call arguments.
  Do not make a separate LLM call solely to generate alternate queries.
- Do not call search_documents again before using the multi-query fallback
  when returned chunks are insufficient.
- The original document search and multi-query fallback share a maximum
  of two document-search tool calls per agent run.
- After the second document-search call, do not search documents again.
  Answer using available evidence and describe remaining limitations.
- If FALLBACK_LIMIT_REACHED appears, stop document searching.
- In docs_web mode, follow the existing web-approval process when the
  document evidence remains insufficient. Never bypass approval.

"""

    prompt += """CONTRADICTION REVIEW:

- Compare retrieved evidence for numerical and semantic conflicts as part
  of normal answer generation. Do not make a separate LLM/tool call solely
  for contradiction detection.
- Treat any numeric conflict candidate from a search tool as a heuristic
  lead, not a confirmed contradiction. Check both excerpts against the full
  retrieved chunks.
- Confirm that sources discuss the same entity and fact under comparable
  scope, units, conditions, and time/version before calling claims
  contradictory.
- Different dates, versions, units, contexts, or entities are not
  automatically contradictions.
- If a conflict is supported, explicitly flag it in the final answer with
  "⚠ Contradiction detected". Include a "Contradictions in sources"
  subsection identifying both sources, the conflicting claims, and concise
  supporting excerpts from retrieved evidence.
- If the discrepancy is plausible but cannot be verified, label it
  "Possible discrepancy (not confirmed)" and explain the uncertainty.
- Never invent sources, quotations, or evidence.

CITATIONS AND SOURCE GROUNDING:

- Base factual claims on evidence returned by the search tools.
- For web-derived claims, cite only URLs present in actual web-search results.
- Never invent URLs or claim to have verified a source that was not retrieved.
- Include a Markdown "Sources" section with relevant retrieved URLs.
- Include only sources that support the answer; prefer relevant official
  documentation over unrelated third-party pages.
- If evidence is insufficient, say what could not be verified instead of
  guessing.
- For document citations, use retrieved filenames and page numbers only
  when available. Never invent page numbers.
- If documents were used, explain that the answer is based on the user's
  documents.
- If web results were used, explain that the answer is from web search.
- If both were used, distinguish which information came from each source.
- Be concise, clear, and helpful.
"""

    if search_mode == "web":
        prompt += """
If search_internet returns NO_RESULTS, explain that web search returned
no usable results. If WEB_SEARCH_LIMIT_REACHED is returned, explain that
the daily web-search limit has been reached. Never tell the user to upload
documents merely because web search failed.
"""

    elif search_mode == "docs":
        prompt += """
If search_documents returns NO_DOCUMENTS, explain that no documents have
been uploaded and ask the user to upload a supported source.
If search_documents returns NO_RESULTS, explain that no relevant evidence
was found in the available documents.
If search_documents returns SEARCH_ERROR, explain that document search
failed and that the result could not be verified.
"""

    else:
        prompt += """
If search_documents returns NO_DOCUMENTS, explain that no documents have
been uploaded. If document evidence is insufficient, follow the web-approval
process before searching the web. If the available sources still do not
support an answer, explain what information could not be verified.
"""

    if long_term:
        prompt += (
            "\n\nWhat I know about this user:\n"
            + "\n".join(long_term)
        )

    return prompt


def _build_messages(compressed, query, system_prompt):
    """Combine system instructions, saved history, and the new question."""
    messages = [SystemMessage(content=system_prompt)]

    for msg in compressed:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["message"]))
        else:
            messages.append(AIMessage(content=msg["message"]))

    messages.append(HumanMessage(content=query))
    return messages


def run_agent(
    query: str,
    user_id: int,
    search_mode: str = "docs_web",
    session_id: Optional[int] = None,
):
    """Run the agent for a single chat request."""
    tools = get_tools_for_mode(user_id, search_mode)
    ask_before_web = search_mode == "docs_web"

    history = get_chat_history(user_id, session_id)
    long_term = get_long_term_memory(user_id)
    compressed = compress_history(history)

    system_prompt = build_system_prompt(long_term, search_mode)
    messages = _build_messages(compressed, query, system_prompt)

    current_agent = build_agent(tools, ask_before_web)
    thread_id = get_thread_id(user_id, session_id)
    config = {"configurable": {"thread_id": thread_id}}

    result = current_agent.invoke(
        {"messages": messages},
        config=config,
    )

    state = current_agent.get_state(config)

    if state.next and "search_internet" in str(state.next):
        return {
            "status": "awaiting_approval",
            "message": (
                "I found limited information in your documents. "
                "Should I also search the web?"
            ),
            "thread_id": thread_id,
        }

    final_answer = _ensure_str(result["messages"][-1].content)

    if final_answer.strip():
        save_message(user_id, "user", query, session_id)
        save_message(user_id, "assistant", final_answer, session_id)

    return {
        "status": "complete",
        "answer": final_answer,
    }


def resume_agent(
    user_id: int,
    approved: bool,
    session_id: Optional[int] = None,
):
    """Resume a docs+web interaction after the user's approval decision."""
    tools = get_tools_for_mode(user_id, "docs_web")
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
        "answer": answer,
    }


def stream_agent(
    query: str,
    user_id: int,
    search_mode: str = "docs_web",
    session_id: Optional[int] = None,
):
    """Stream the agent's answer while saving completed conversation turns."""
    tools = get_tools_for_mode(user_id, search_mode)
    ask_before_web = search_mode == "docs_web"

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
        stream_mode="messages",
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