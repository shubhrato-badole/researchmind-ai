from langchain_google_genai import ChatGoogleGenerativeAI
from database.chromadb import get_collection
from database.postgres import get_connection
from config import GEMINI_API_KEY
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=GEMINI_API_KEY
    )

def get_user_topics(user_id: int):
    """get all topics extracted from user's documents"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT DISTINCT topic FROM document_topics
           WHERE user_id = %s ORDER BY topic""",
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]

def get_chunks_by_topic(user_id: int, topic: str):
    """get chunks related to a specific topic from ChromaDB"""
    collection = get_collection(str(user_id))
    results = collection.query(
        query_texts=[topic],
        n_results=10
    )
    if not results["documents"][0]:
        return []
    return results["documents"][0]

def get_titles_for_documents(user_id: int, document_ids: list):
    """look up filenames for given document ids, scoped to this user"""
    if not document_ids:
        return []
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT title FROM documents WHERE user_id = %s AND id = ANY(%s)",
        (user_id, document_ids)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]

def get_chunks_by_documents(user_id: int, document_ids: list):
    """get chunks belonging only to the selected documents"""
    titles = get_titles_for_documents(user_id, document_ids)
    if not titles:
        return []
    collection = get_collection(str(user_id))
    results = collection.get(
        where={"filename": {"$in": titles}}
    )
    return results["documents"] if results["documents"] else []

def _get_content_sample(user_id: int, topic: str = None, document_ids: list = None, char_limit: int = 3000, fallback_limit: int = 10):
    """shared logic: prefer document_ids, then topic, then all documents"""
    if document_ids:
        docs = get_chunks_by_documents(user_id, document_ids)
        if not docs:
            return None, "No content found for selected documents"
        return " ".join(docs)[:char_limit], None
    elif topic:
        docs = get_chunks_by_topic(user_id, topic)
        if not docs:
            return None, f"No content found for topic: {topic}"
        return " ".join(docs)[:char_limit], None
    else:
        collection = get_collection(str(user_id))
        all_docs = collection.get()
        if not all_docs["documents"]:
            return None, "No documents found. Upload something first."
        return " ".join(all_docs["documents"][:fallback_limit])[:char_limit], None


def generate_quiz(
    user_id: int,
    num_questions: int = 5,
    difficulty: str = "medium",
    topic: str = None,
    document_ids: list = None
):
    sample, error = _get_content_sample(user_id, topic, document_ids)
    if error:
        return {"error": error}

    difficulty_guide = {
        "easy": "definition and recall based — what is X, who invented Y",
        "medium": "concept and understanding based — how does X work, why is Y used",
        "hard": "application and analysis based — when would you use X, what happens if Y"
    }

    prompt = f"""Based on this content, generate {num_questions} multiple choice questions.
Difficulty: {difficulty} — {difficulty_guide.get(difficulty, 'medium')}
Topic focus: {topic if topic else 'all topics'}

Return ONLY a JSON array in this exact format:
[
  {{
    "question": "question text",
    "options": ["option A", "option B", "option C", "option D"],
    "correct": 0,
    "explanation": "why this answer is correct",
    "topic": "specific topic this question covers"
  }}
]

Note: "correct" is the index (0,1,2,3) of the correct option.

Content:
{sample}

Return only the JSON array, nothing else."""

    try:
        response = get_llm().invoke(prompt)
        text = response.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        questions = json.loads(text)
        return {
            "questions": questions,
            "topic": topic or "all",
            "difficulty": difficulty
        }
    except Exception as e:
        return {"error": f"Could not generate quiz: {str(e)}"}

def check_answer(selected: int, correct: int, explanation: str):
    is_correct = selected == correct
    return {
        "correct": is_correct,
        "explanation": explanation,
        "message": "Correct!" if is_correct else f"Wrong. {explanation}"
    }

def save_score(user_id: int, score: int, total: int, topic: str, difficulty: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO quiz_scores (user_id, topic, score, total, difficulty)
           VALUES (%s, %s, %s, %s, %s)""",
        (user_id, topic or "all", score, total, difficulty)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Score saved"}

def get_score_history(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT topic, score, total, difficulty, created_at
           FROM quiz_scores WHERE user_id = %s
           ORDER BY created_at DESC LIMIT 20""",
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "topic": r[0],
            "score": r[1],
            "total": r[2],
            "percentage": round((r[1] / r[2]) * 100),
            "difficulty": r[3],
            "date": str(r[4])
        }
        for r in rows
    ]

def get_weak_topics(user_id: int):
    """find topics where user consistently scores below 60%"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT topic,
                  AVG(score::float / total * 100) as avg_percentage,
                  COUNT(*) as attempts
           FROM quiz_scores
           WHERE user_id = %s
           GROUP BY topic
           HAVING AVG(score::float / total * 100) < 60
           ORDER BY avg_percentage ASC""",
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "topic": r[0],
            "avg_score": round(r[1]),
            "attempts": r[2],
            "suggestion": f"You score {round(r[1])}% on {r[0]}. Try studying this topic more."
        }
        for r in rows
    ]

def generate_flashcards(user_id: int, topic: str = None, count: int = 10, document_ids: list = None):
    sample, error = _get_content_sample(user_id, topic, document_ids)
    if error:
        return {"error": error}

    prompt = f"""Generate {count} flashcards from this content.
Return ONLY a JSON array in this exact format:
[
  {{
    "front": "question or term",
    "back": "answer or definition",
    "topic": "topic this belongs to"
  }}
]

Content:
{sample}

Return only the JSON array, nothing else."""

    try:
        response = get_llm().invoke(prompt)
        text = response.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        cards = json.loads(text)
        return {"flashcards": cards, "topic": topic or "all"}
    except Exception as e:
        return {"error": f"Could not generate flashcards: {str(e)}"}


def generate_summary(user_id: int, topic: str = None, document_ids: list = None):
    sample, error = _get_content_sample(user_id, topic, document_ids)
    if error:
        return {"error": error}

    prompt = f"""Summarise this content in exactly this format:

KEY POINTS:
- point 1
- point 2
- point 3
- point 4
- point 5

ONE LINE SUMMARY:
[one sentence summary]

IMPORTANT TERMS:
[term1, term2, term3, term4, term5]

Content:
{sample}"""

    try:
        response = get_llm().invoke(prompt)
        return {
            "summary": response.content.strip(),
            "topic": topic or "all"
        }
    except Exception as e:
        return {"error": str(e)}


def generate_interview_question(user_id: int, topic: str = None, document_ids: list = None):
    sample, error = _get_content_sample(user_id, topic, document_ids, char_limit=2000, fallback_limit=5)
    if error:
        return {"error": error}

    prompt = f"""Generate one technical interview question from this content.
The question should be open ended and require explanation.

Return ONLY a JSON object:
{{
    "question": "interview question here",
    "key_points": ["point1", "point2", "point3"],
    "topic": "topic this covers"
}}

Content:
{sample}

Return only the JSON, nothing else."""

    try:
        response = get_llm().invoke(prompt)
        text = response.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}

def evaluate_interview_answer(question: str, answer: str, key_points: list):
    prompt = f"""Evaluate this interview answer.

Question: {question}
Answer: {answer}
Expected key points: {", ".join(key_points)}

Return ONLY a JSON object:
{{
    "score": 7,
    "max_score": 10,
    "covered_points": ["point1", "point2"],
    "missed_points": ["point3"],
    "feedback": "detailed feedback here",
    "grade": "Good"
}}

Return only the JSON, nothing else."""

    try:
        response = get_llm().invoke(prompt)
        text = response.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}