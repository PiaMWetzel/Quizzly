import sqlite3
class User:

    def __init__(self, _id):

        self.username = None
        self.password = None
        self._id = _id
        self.email = None
        
        conn = sqlite3.connect("quiz.db")
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE user_id=?"
        result = cursor.execute(query, (_id,)).fetchone()
        conn.close()
        if result:
            self.username = result[1]
            self.password = result[3]
            self._id = _id
            self.email = result[2]

    def get_username(self):
        print(f"username:{self.username}")
        return self.username

    def get_user_id(self):
        print(f"user id:{self._id}")
        return self._id

    def get_email(self):
        return self.email
    

    def logout(self):
        self.username = None
        self.password = None
        self._id = None
        self.email = None
