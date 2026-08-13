from datetime import date;
from database.postgres import get_connection
from database.redis_client import get_redis


FREE_LIMITS= {
    "doc_search": 10,
    "web_search": 10,
    "quiz": 2,

}

FREE_DOC_UPLOAD_LIMIT = 5

def get_user_plan(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT plan FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else "free"



def check_daily_limit(user_id: int, feature: str):
    plan = get_user_plan(user_id)
    if plan == "pro":
        return True, None, None

    limit = FREE_LIMITS[feature]
    r = get_redis()
    key = f"usage:{user_id}:{feature}:{date.today()}"
    current = int(r.get(key) or 0)

    if current >= limit:
        return False, 0, limit

    r.incr(key)
    r.expire(key, 86400)
    return True, limit - current - 1, limit
   
def check_roadmap_limit(user_id: int):
    plan = get_user_plan(user_id)
    if plan == "pro":
        return True, None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT roadmap_last_generated FROM users WHERE id = %s", (user_id,))
    last = cur.fetchone()[0]
    cur.close()
    conn.close()

    if last is None:
        return True, None

    days_since = (date.today() - last).days
    if days_since < 30:
        return False, 30 - days_since
    return True, None


def mark_roadmap_generated(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET roadmap_last_generated = %s WHERE id = %s", (date.today(), user_id))
    conn.commit()
    cur.close()
    conn.close()



def check_document_limit(user_id: int):
    plan = get_user_plan(user_id)
    if plan == "pro":
        return True, None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents WHERE user_id = %s", (user_id,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    return count < FREE_DOC_UPLOAD_LIMIT, count