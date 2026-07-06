from authlib.integrations.starlette_client import OAuth
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from database.postgres import get_connection
import secrets
import bcrypt

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)

def get_or_create_google_user(email: str, name: str):
    conn = get_connection()
    cur = conn.cursor()

    
    cur.execute(
        "SELECT id, name FROM users WHERE email = %s",
        (email,)
    )
    user = cur.fetchone()

    if user:
        cur.close()
        conn.close()
        return user[0], user[1]

   
    random_password = secrets.token_urlsafe(32)
    hashed = bcrypt.hashpw(
        random_password.encode(),
        bcrypt.gensalt()
    ).decode()

    cur.execute(
        """INSERT INTO users (name, email, password, auth_provider)
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (name, email, hashed, "google")
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return user_id, name