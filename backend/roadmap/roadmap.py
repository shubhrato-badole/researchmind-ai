from langchain_google_genai import ChatGoogleGenerativeAI
from database.chromadb import get_collection
from database.postgres import get_connection
from agent.web_search import search_web
from ingestion.website import ingest_website
from config import GEMINI_API_KEY
import json
from datetime import date


llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GEMINI_API_KEY
)


def generate_roadmap(goal:str, user_id:int , current_knowledge:str):
    """generate personalised roadmap based on skill gap"""
    prompt= f""" Create a personilised learning roadmap


    Gola:{goal}
    Current knowledge: {current_knowledge}

    Analyze the gap between current knowledge and goal
     Generate 6-8 steps to bridge that gap_skip what they already know
      
       
        Return only a JSON object:
        {{
        "goal":"goal text"
        "estimated_total_days":30,
        "steps":[
        "step_number:1,
        "title":"topic name,
        "estimated_dyas:3,
        "why_needed": "how this bridges the gap",
        "search_query": "best query to find resources for this step"
        
        ]
        }}
        
        
        Return only the JSON, nothing else."""
    
    try:
        response = llm.invoke(prompt)
        text= response.content.strip()
        text=text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
         
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("INSERT INTO roadmaps(user_id, goal) VALUES(%s, %s) RETURNING id",
                    (user_id, goal))
        roadmap_id = cur.fetchone()[0]

        for step in data["steps"]:
            cur.execute(
                """INSERT INTO roadmap_steps
                   (roadmap_id, step_number, title, description, estimated_days)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    roadmap_id,
                    step["step_number"],
                    step["title"],
                    step["description"],
                    step["estimated_days"]
                )
            )

        conn.commit()
        cur.close()
        conn.close()
  
        return {
            "roadmap_id": roadmap_id,
            "goal": goal,
            "estimated_total_days": data["estimated_total_days"],
            "steps": data["steps"]
        }
    

    except Exception as e:
        return {"error": str(e)}


def start_step(roadmap_id:int , step_number: int , user_id:int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT tittle, description FROM roadmap_steps WHERE roadmap_id = %s AND step_number = %s""" , (roadmap_id , step_number))

    step = cur.fetchone()

    if not step:
        return {"error": "Step not found"}

    title, description = step
  

    results = search_web(f"{title} tutorial beginner")
    ingested = []
    for r in results[:2]:
        url = r["metadata"].get("source_url", "")
        if url:
            try:
                ingest_website(url, user_id)
                ingested.append(url)
            except:
                pass

    cur.execute(
        """UPDATE roadmap_steps SET resources_ingested = TRUE
           WHERE roadmap_id = %s AND step_number = %s""",
        (roadmap_id, step_number)
    )


    cur.execute(
        "UPDATE roadmaps SET current_step = %s WHERE id = %s",
        (step_number, roadmap_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": f"Started step {step_number}: {title}",
        "resources_ingested": ingested,
        "tip": f"Resources added to your knowledge base. Ask me anything about {title}!"
    }


def complete_step(roadmap_id: int, step_number: int, quiz_passed: bool):

    if not quiz_passed:
        return {
            "error": "You must pass the quiz for this topic before marking it complete",
            "tip": "Go to Study Mode and take the quiz on this topic"
        }

    conn = get_connection()
    cur = conn.cursor()

    from datetime import datetime
    cur.execute(
        """UPDATE roadmap_steps
           SET status = 'completed', quiz_passed = TRUE, completed_at = %s
           WHERE roadmap_id = %s AND step_number = %s""",
        (datetime.now(), roadmap_id, step_number)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": f"Step {step_number} completed!"}



def get_progress(roadmap_id: int, user_id: int):
    """get full progress report"""
    conn = get_connection()
    cur = conn.cursor()

    
    cur.execute(
        "SELECT goal, current_step, streak, last_active FROM roadmaps WHERE id = %s AND user_id = %s",
        (roadmap_id, user_id)
    )
    roadmap = cur.fetchone()

    if not roadmap:
        return {"error": "Roadmap not found"}

    goal, current_step, streak, last_active = roadmap

  
    cur.execute(
        """SELECT step_number, title, status, estimated_days, quiz_passed
           FROM roadmap_steps WHERE roadmap_id = %s ORDER BY step_number""",
        (roadmap_id,)
    )
    steps = cur.fetchall()

 
    total = len(steps)
    completed = sum(1 for s in steps if s[2] == "completed")
    percentage = round((completed / total) * 100) if total > 0 else 0


    remaining_days = sum(s[3] for s in steps if s[2] != "completed")


    today = date.today()
    if last_active and (today - last_active).days == 1:
        streak += 1
    elif last_active and (today - last_active).days > 1:
        streak = 0

    cur.execute(
        "UPDATE roadmaps SET streak = %s, last_active = %s WHERE id = %s",
        (streak, today, roadmap_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "goal": goal,
        "progress_percentage": percentage,
        "completed_steps": completed,
        "total_steps": total,
        "current_step": current_step,
        "estimated_remaining_days": remaining_days,
        "streak": streak,
        "steps": [
            {
                "step_number": s[0],
                "title": s[1],
                "status": s[2],
                "estimated_days": s[3],
                "quiz_passed": s[4]
            }
            for s in steps
        ]
    }


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