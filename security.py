import sqlite3
from passlib.hash import pbkdf2_sha256

class Password:
    @classmethod
    def encrypt_password(cls, plain_password):
        encrypted_password = pbkdf2_sha256.hash(plain_password)
        return encrypted_password
    @classmethod
    def check_if_password_matches(cls, user_id, plain_password):
        conn = sqlite3.connect("Quiz.db")
        cursor = conn.cursor()
        query = "SELECT password FROM users WHERE user_id=?"
        result = cursor.execute(query, (user_id,)).fetchone()
        return pbkdf2_sha256.verify(plain_password, result[0])
