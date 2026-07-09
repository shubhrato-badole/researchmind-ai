from mcp.server.fastmcp import FastMCP
from agent.graph import run_agent
from features.study_mode import generate_quiz, generate_summary, generate_flashcards
from features.evaluation import evaluate_rag

mcp = FastMCP("ResearchMind")

@mcp.tool()
def search_knowledge_base(query: str, user_id: int) -> str:
    """Search the user's personal knowledge base and get a cited answer.
    Use this when the user wants information from their uploaded documents."""
    result = run_agent(query, user_id)
    return result.get("answer", "No answer found")

@mcp.tool()
def search_with_web(query: str, user_id: int) -> str:
    """Search documents and the live web together for a comprehensive answer.
    Use this when documents alone may not have the answer."""
    result = run_agent(query, user_id, search_web=True)
    return result.get("answer", "No answer found")

@mcp.tool()
def generate_study_quiz(user_id: int, topic: str = None, num_questions: int = 5) -> str:
    """Generate a quiz from the user's uploaded documents.
    Optionally filter by a specific topic."""
    result = generate_quiz(user_id, num_questions, "medium", topic)
    if "error" in result:
        return result["error"]
    return str(result["questions"])

@mcp.tool()
def summarize_knowledge_base(user_id: int, topic: str = None) -> str:
    """Get a smart summary of the user's documents, optionally filtered by topic."""
    result = generate_summary(user_id, topic)
    if "error" in result:
        return result["error"]
    return result["summary"]

@mcp.tool()
def evaluate_answer_quality(query: str, user_id: int) -> str:
    """Evaluate the quality of a RAG answer using faithfulness, relevancy and precision metrics."""
    result = evaluate_rag(query, user_id)
    return str(result)

if __name__ == "__main__":
    mcp.run()