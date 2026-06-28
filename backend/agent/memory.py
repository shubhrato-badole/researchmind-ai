from database.postgres import get_connection


def get_chat_history(user_id:int , limit:10):
    conn= get_connection()
    cur = conn.curser()
    cur.execute(
        """SELECT role, message FROM chat_history
           WHERE user_id = %s
           ORDER BY created_at DESC
           LIMIT %s""",
        (user_id, limit)
    )

    rows=   cur.fetchall()
    cur.close()
    conn.close()

    rows.reverse()
    return [{"role": row[0], "message": row[1]} for row in rows]

def save_message(user_id: int, role: str, message: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO chat_history (user_id ,  role, message) VALUES(%s, %s ,%s) ", (user_id, role, message))
    conn.commit()
    cur.close()
    conn.close()

def get_long_term_memory(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT memory FROM user_memory WHERE user_id = %s ORDER BY created_at DESC LIMIT 5",
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]

def save_long_term_memory(user_id: int, memory: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_memory (user_id, memory) VALUES (%s, %s)",
        (user_id, memory)
    )
    conn.commit()
    cur.close()
    conn.close()