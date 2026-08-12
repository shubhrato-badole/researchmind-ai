from database.postgres import get_connection


def create_session(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_sessions (user_id) VALUES (%s) RETURNING id",
        (user_id,)
    )
    session_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return session_id


def update_session_title(session_id: int, title: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE chat_sessions SET title = %s WHERE id = %s",
        (title[:50], session_id)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_sessions(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, title, created_at FROM chat_sessions
           WHERE user_id = %s
           ORDER BY created_at DESC
           LIMIT 20""",
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "created_at": str(r[2])}
        for r in rows
    ]


def get_chat_history(user_id: int, session_id: int = None, limit: int = 10):
    conn = get_connection()
    cur = conn.cursor()

    if session_id:
        cur.execute(
            """SELECT role, message FROM chat_history
               WHERE user_id = %s AND session_id = %s
               ORDER BY created_at DESC
               LIMIT %s""",
            (user_id, session_id, limit)
        )
    else:
        cur.execute(
            """SELECT role, message FROM chat_history
               WHERE user_id = %s
               ORDER BY created_at DESC
               LIMIT %s""",
            (user_id, limit)
        )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    rows.reverse()
    return [{"role": row[0], "message": row[1]} for row in rows]


def save_message(user_id: int, role: str, message: str, session_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_history (user_id, role, message, session_id) VALUES (%s, %s, %s, %s)",
        (user_id, role, message, session_id)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_long_term_memory(user_id: int, session_id=None):
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