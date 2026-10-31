from langchain_google_genai import ChatGoogleGenerativeAI
from database.chromadb import get_collection
from database.postgres import get_connection
from agent.web_search import search_web
from ingestion.website import ingest_website
from config import GEMINI_API_KEY
import json
from datetime import date
from limit.rate_limiter import check_roadmap_limit, mark_roadmap_generated


def _response_text(response) -> str:
    """Normalize LangChain model responses that contain strings or text blocks."""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif isinstance(getattr(block, "text", None), str):
                parts.append(block.text)
        result = "\n".join(part for part in parts if part).strip()
        if result:
            return result
    raise ValueError(f"Unexpected LLM response content type: {type(content).__name__}")


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    google_api_key=GEMINI_API_KEY
)


def generate_roadmap(goal: str, user_id: int, current_knowledge: str):
    allowed, days_left = check_roadmap_limit(user_id)
    if not allowed:
        return {"error": f"You've used your free roadmap. Come back in {days_left} days or upgrade to Pro."}

    prompt = f"""Create a personalized learning roadmap.
Goal: {goal}
Current knowledge: {current_knowledge}

Generate 6-8 main learning steps that bridge the gap from current knowledge to the goal.
For EACH main step, include only 3-5 essential subtopics (3 or 4 is ideal).
Subtopics must be the important concepts the learner actually needs to know before the final step quiz.
Order subtopics from prerequisite to more advanced. Do not list every related concept or add filler.
Make each subtopic concrete, independently checkable, and suitable for a learner checklist.
Each subtopic needs a short practical description of what to learn.

Return ONLY a JSON object in this exact shape:
{{
  "goal": "goal text",
  "estimated_total_days": 30,
  "steps": [
    {{
      "step_number": 1,
      "title": "main topic name",
      "description": "what the main topic covers and why it matters",
      "estimated_days": 3,
      "why_needed": "how this bridges the gap",
      "search_query": "useful query to find learning resources",
      "subtopics": [
        {{"title": "essential subtopic", "description": "what the learner should understand or practise"}},
        {{"title": "another essential subtopic", "description": "what the learner should understand or practise"}},
        {{"title": "third essential subtopic", "description": "what the learner should understand or practise"}}
      ]
    }}
  ]
}}

Return valid JSON only, without Markdown fences."""

    try:
        response = llm.invoke(prompt)
        text = _response_text(response)
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        steps = data.get("steps")
        if not isinstance(steps, list) or not steps:
            return {"error": "The AI did not return any roadmap steps. Please try again."}

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO roadmaps(user_id, goal) VALUES(%s, %s) RETURNING id",
                (user_id, goal),
            )
            roadmap_id = cur.fetchone()[0]
            stored_steps = []

            for index, step in enumerate(steps, start=1):
                if not isinstance(step, dict):
                    continue
                step_number = int(step.get("step_number", index))
                title = str(step.get("title") or f"Step {step_number}").strip()[:255]
                description = str(step.get("description") or step.get("why_needed") or "").strip()
                estimated_days = max(1, int(step.get("estimated_days") or 1))
                cur.execute(
                    """INSERT INTO roadmap_steps
                       (roadmap_id, step_number, title, description, estimated_days)
                       VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                    (roadmap_id, step_number, title, description, estimated_days),
                )
                roadmap_step_id = cur.fetchone()[0]

                supplied = step.get("subtopics")
                clean_subtopics = []
                if isinstance(supplied, list):
                    for item in supplied:
                        if not isinstance(item, dict):
                            continue
                        sub_title = item.get("title")
                        if not isinstance(sub_title, str) or not sub_title.strip():
                            continue
                        sub_description = item.get("description")
                        clean_subtopics.append({
                            "title": sub_title.strip()[:255],
                            "description": sub_description.strip() if isinstance(sub_description, str) else "",
                        })
                # Keep a usable learning checklist if the model omits the requested field.
                if not clean_subtopics:
                    clean_subtopics = [
                        {"title": f"Understand the fundamentals of {title}", "description": f"Learn the core ideas and vocabulary for {title}."},
                        {"title": f"Practise {title}", "description": f"Apply the main ideas of {title} in a small example or exercise."},
                        {"title": f"Review {title}", "description": f"Review the key ideas and identify what you should be able to explain."},
                    ]
                elif len(clean_subtopics) < 3:
                    fallback_subtopics = [
                        {"title": f"Practise {title}", "description": f"Apply the main ideas of {title} in a small example or exercise."},
                        {"title": f"Review {title}", "description": f"Review the key ideas and identify what you should be able to explain."},
                    ]
                    for fallback in fallback_subtopics:
                        if len(clean_subtopics) >= 3:
                            break
                        if all(item["title"].casefold() != fallback["title"].casefold() for item in clean_subtopics):
                            clean_subtopics.append(fallback)
                for sort_order, subtopic in enumerate(clean_subtopics[:5], start=1):
                    cur.execute(
                        """INSERT INTO roadmap_subtopics
                           (roadmap_step_id, title, description, sort_order)
                           VALUES (%s, %s, %s, %s)""",
                        (roadmap_step_id, subtopic["title"], subtopic["description"], sort_order),
                    )
                stored_steps.append({
                    "step_number": step_number,
                    "title": title,
                    "description": description,
                    "estimated_days": estimated_days,
                    "subtopics": clean_subtopics[:5],
                })

            if not stored_steps:
                raise ValueError("The AI response did not contain any usable steps.")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

        mark_roadmap_generated(user_id)
        return {
            "roadmap_id": roadmap_id,
            "goal": goal,
            "estimated_total_days": data.get("estimated_total_days") or sum(s["estimated_days"] for s in stored_steps),
            "steps": stored_steps,
        }
    except Exception as exc:
        return {"error": str(exc)}

def start_step(roadmap_id: int, step_number: int, user_id: int):
    # Verify ownership before touching the roadmap or its steps.
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM roadmaps WHERE id = %s AND user_id = %s",
            (roadmap_id, user_id),
        )
        if not cur.fetchone():
            return {"error": "Roadmap not found"}

        cur.execute(
            "SELECT title, description, status FROM roadmap_steps WHERE roadmap_id = %s AND step_number = %s",
            (roadmap_id, step_number),
        )
        step = cur.fetchone()
        if not step:
            return {"error": "Step not found"}
        title, description, status = step
        if status == "completed":
            return {"error": "This step is already completed"}

        cur.execute(
            "UPDATE roadmap_steps SET status = 'in_progress' WHERE roadmap_id = %s AND step_number = %s",
            (roadmap_id, step_number),
        )
        cur.execute(
            "UPDATE roadmaps SET current_step = %s WHERE id = %s AND user_id = %s",
            (step_number, roadmap_id, user_id),
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        return {"error": f"Could not start roadmap step: {exc}"}
    finally:
        cur.close()
        conn.close()

    # Resource lookup is best-effort: starting a step should still work if search or ingestion fails.
    ingested = []
    try:
        results = search_web(f"{title} tutorial beginner")
        if isinstance(results, list):
            for result in results[:2]:
                if not isinstance(result, dict):
                    continue
                metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
                url = metadata.get("source_url") or result.get("url") or result.get("link") or ""
                if not url:
                    continue
                try:
                    ingest_result = ingest_website(url, user_id)
                    if not (isinstance(ingest_result, dict) and str(ingest_result.get("message", "")).startswith("Error:")):
                        ingested.append(url)
                except Exception:
                    continue
    except Exception:
        pass

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE roadmap_steps SET resources_ingested = %s WHERE roadmap_id = %s AND step_number = %s",
            (bool(ingested), roadmap_id, step_number),
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        return {"error": f"Step started, but resource status could not be saved: {exc}"}
    finally:
        cur.close()
        conn.close()

    return {
        "message": f"Started step {step_number}: {title}",
        "resources_ingested": ingested,
        "tip": (
            f"Resources added to your knowledge base. Ask me anything about {title}!"
            if ingested else
            f"Step started. No web resources were added this time; you can still study {title} manually."
        ),
    }

def complete_step(roadmap_id: int, step_number: int, quiz_passed: bool, user_id: int):
    """Complete a step only after its persisted checklist and quiz gate are satisfied."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM roadmaps WHERE id = %s AND user_id = %s",
            (roadmap_id, user_id),
        )
        if not cur.fetchone():
            return {"error": "Roadmap not found"}

        cur.execute(
            "SELECT id, status, quiz_passed FROM roadmap_steps WHERE roadmap_id = %s AND step_number = %s",
            (roadmap_id, step_number),
        )
        step = cur.fetchone()
        if not step:
            return {"error": "Step not found"}
        step_id, status, stored_quiz_passed = step
        if status == "completed":
            return {"message": f"Step {step_number} is already completed"}
        if status != "in_progress":
            return {"error": "Start this step before completing it"}
        # Never trust the client-supplied quiz_passed flag; the score route stores the real result.
        if not stored_quiz_passed:
            return {"error": "Pass the step quiz with at least 80% before completing this step."}

        cur.execute(
            """SELECT COUNT(*), COUNT(*) FILTER (WHERE is_completed = FALSE)
               FROM roadmap_subtopics WHERE roadmap_step_id = %s""",
            (step_id,),
        )
        total_subtopics, incomplete_subtopics = cur.fetchone()
        if total_subtopics > 0 and incomplete_subtopics > 0:
            return {"error": f"Complete all {total_subtopics} subtopics before completing this step. {incomplete_subtopics} remain."}

        cur.execute(
            """UPDATE roadmap_steps SET status = 'completed', completed_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (step_id,),
        )
        conn.commit()
        return {"message": f"Step {step_number} completed!"}
    except Exception as exc:
        conn.rollback()
        return {"error": f"Could not complete roadmap step: {exc}"}
    finally:
        cur.close()
        conn.close()

def get_progress(roadmap_id: int, user_id: int):
    """Return progress plus each main step's saved subtopic checklist."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT goal, current_step, streak, last_active FROM roadmaps WHERE id = %s AND user_id = %s",
            (roadmap_id, user_id),
        )
        roadmap = cur.fetchone()
        if not roadmap:
            return {"error": "Roadmap not found"}

        goal, current_step, streak, last_active = roadmap
        cur.execute(
            """SELECT id, step_number, title, description, status, estimated_days,
                      quiz_passed, resources_ingested
               FROM roadmap_steps WHERE roadmap_id = %s ORDER BY step_number""",
            (roadmap_id,),
        )
        rows = cur.fetchall()
        steps = []
        for row in rows:
            step_id, step_number, title, description, status, days, quiz_passed, resources_ingested = row
            cur.execute(
                """SELECT id, title, description, is_completed
                   FROM roadmap_subtopics WHERE roadmap_step_id = %s ORDER BY sort_order, id""",
                (step_id,),
            )
            subtopic_rows = cur.fetchall()
            steps.append({
                "step_number": step_number,
                "title": title,
                "description": description or "",
                "status": status,
                "estimated_days": days or 0,
                "quiz_passed": bool(quiz_passed),
                "resources_ingested": bool(resources_ingested),
                "subtopics": [
                    {"id": sub[0], "title": sub[1], "description": sub[2] or "", "is_completed": bool(sub[3])}
                    for sub in subtopic_rows
                ],
            })

        total = len(steps)
        completed = sum(1 for step in steps if step["status"] == "completed")
        percentage = round(completed / total * 100) if total else 0
        remaining_days = sum(step["estimated_days"] for step in steps if step["status"] != "completed")

        today = date.today()
        if last_active and (today - last_active).days == 1:
            streak = (streak or 0) + 1
        elif last_active and (today - last_active).days > 1:
            streak = 0
        streak = streak or 0
        cur.execute(
            "UPDATE roadmaps SET streak = %s, last_active = %s WHERE id = %s AND user_id = %s",
            (streak, today, roadmap_id, user_id),
        )
        conn.commit()
        return {
            "goal": goal,
            "progress_percentage": percentage,
            "completed_steps": completed,
            "total_steps": total,
            "current_step": current_step,
            "estimated_remaining_days": remaining_days,
            "streak": streak,
            "steps": steps,
        }
    except Exception as exc:
        conn.rollback()
        return {"error": f"Could not load roadmap progress: {exc}"}
    finally:
        cur.close()
        conn.close()

def set_subtopic_completed(roadmap_id: int, step_number: int, subtopic_id: int, completed: bool, user_id: int):
    """Update one subtopic only when it belongs to the signed-in user's roadmap."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """UPDATE roadmap_subtopics AS st
               SET is_completed = %s
               FROM roadmap_steps AS rs
               JOIN roadmaps AS r ON r.id = rs.roadmap_id
               WHERE st.roadmap_step_id = rs.id
                 AND rs.roadmap_id = %s AND rs.step_number = %s
                 AND rs.status = 'in_progress'
                 AND st.id = %s AND r.user_id = %s
               RETURNING st.id, st.is_completed""",
            (completed, roadmap_id, step_number, subtopic_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "Subtopic not found for this roadmap"}
        conn.commit()
        return {"message": "Subtopic progress saved", "subtopic_id": row[0], "is_completed": bool(row[1])}
    except Exception as exc:
        conn.rollback()
        return {"error": f"Could not update subtopic: {exc}"}
    finally:
        cur.close()
        conn.close()


def generate_step_quiz(roadmap_id: int, step_number: int, user_id: int):
    """Generate a final step quiz from the roadmap subtopics after all are checked off."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT rs.id, rs.title, rs.description, rs.status
               FROM roadmap_steps AS rs JOIN roadmaps AS r ON r.id = rs.roadmap_id
               WHERE r.user_id = %s AND rs.roadmap_id = %s AND rs.step_number = %s""",
            (user_id, roadmap_id, step_number),
        )
        step = cur.fetchone()
        if not step:
            return {"error": "Roadmap step not found"}
        step_id, title, description, status = step
        if status == "completed":
            return {"error": "This roadmap step is already completed"}
        if status != "in_progress":
            return {"error": "Start this step before taking its quiz"}

        cur.execute(
            "SELECT title, description, is_completed FROM roadmap_subtopics WHERE roadmap_step_id = %s ORDER BY sort_order, id",
            (step_id,),
        )
        subtopics = cur.fetchall()
        if not subtopics:
            return {"error": "This older roadmap has no saved subtopics. Generate a new roadmap to use the checklist quiz."}
        incomplete = [item[0] for item in subtopics if not item[2]]
        if incomplete:
            return {"error": f"Finish all subtopics before the quiz. Still to learn: {', '.join(incomplete)}"}
        learning_outline = "\n".join(f"- {item[0]}: {item[1] or ''}" for item in subtopics)
    finally:
        cur.close()
        conn.close()

    prompt = f"""Create exactly 5 multiple-choice quiz questions to check understanding of this roadmap step.
Main topic: {title}
Step description: {description or ''}
Required subtopics:
{learning_outline}

Rules: test the listed subtopics only; avoid obscure trivia; each question has four distinct options; exactly one option is correct; vary the position of the correct answer.
Return only a JSON array with this shape:
[{{"question":"...","options":["A","B","C","D"],"correct":0,"explanation":"...","topic":"{title}"}}]
Return valid JSON only, without Markdown fences."""
    try:
        response = llm.invoke(prompt)
        text = _response_text(response).replace("```json", "").replace("```", "").strip()
        questions = json.loads(text)
        if not isinstance(questions, list) or not questions:
            return {"error": "The AI did not return valid quiz questions. Please try again."}
        valid = []
        for item in questions:
            if not isinstance(item, dict) or not isinstance(item.get("question"), str) or not isinstance(item.get("options"), list):
                continue
            try:
                correct = int(item.get("correct"))
            except (TypeError, ValueError):
                continue
            options = [str(option) for option in item["options"]]
            if len(options) < 2 or correct < 0 or correct >= len(options):
                continue
            valid.append({
                "question": item["question"],
                "options": options,
                "correct": correct,
                "explanation": str(item.get("explanation") or ""),
                "topic": str(item.get("topic") or title),
            })
        if not valid:
            return {"error": "The AI response did not contain usable quiz questions."}
        return {"questions": valid, "topic": title, "difficulty": "medium", "roadmap_id": roadmap_id, "step_number": step_number}
    except Exception as exc:
        return {"error": str(exc)}


def get_user_roadmaps(user_id: int):

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, goal, current_step, streak FROM roadmaps WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "goal": r[1], "current_step": r[2], "streak": r[3]}
        for r in rows
    ]