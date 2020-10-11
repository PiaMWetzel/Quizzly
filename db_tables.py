import sqlite3, datetime
from datetime import datetime, timedelta
from passlib.hash import pbkdf2_sha256

conn_quiz = sqlite3.connect('quiz.db')
cursor = conn_quiz.cursor()

#create table 'quizzes'
create_table = "CREATE TABLE IF NOT EXISTS quizzes (quiz_id INTEGER PRIMARY KEY, title STRING, description STRING, author STRING, category STRING, votes INTEGER, date_created DATETIME)"
cursor.execute(create_table)


#create table 'quiz_questions'
create_table = "CREATE TABLE IF NOT EXISTS quiz_questions (question_id INTEGER PRIMARY KEY, question STRING, belongs_to INTEGER, FOREIGN KEY(belongs_to) REFERENCES quizzes(quiz_id))"
cursor.execute(create_table)

#create table 'quiz_answers'
create_table = "CREATE TABLE IF NOT EXISTS quiz_answers (answer_id INTEGER PRIMARY KEY, answer STRING, belongs_to INTEGER, correct BOOLEAN, FOREIGN KEY(belongs_to) REFERENCES quiz_questions(question_id))"
cursor.execute(create_table)

#create table users
create_table = "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username STRING, email STRING, password STRING, image STRING)"
cursor.execute(create_table)

#create table votes
create_table = "CREATE TABLE IF NOT EXISTS votes (vote_id INTEGER PRIMARY KEY, quiz_id INTEGER, user_id INTEGER, upvote BOOL, downvote BOOL, FOREIGN KEY(quiz_id) REFERENCES quizzes(quiz_id), FOREIGN KEY(user_id) REFERENCES users(user_id))"
cursor.execute(create_table)

#create table quiz_history
create_table = "CREATE TABLE IF NOT EXISTS quiz_history(hist_id INTEGER PRIMARY KEY, user INTEGER, quiz INTEGER, result INTEGER, date1 DATETIME, FOREIGN KEY(quiz) REFERENCES quizzes(quiz_id))"
cursor.execute(create_table)

#create table challenges
create_table = "CREATE TABLE IF NOT EXISTS challenge_history(challenge_id INTEGER PRIMARY KEY, challenger INTEGER, opponent INTEGER, quiz INTEGER, challenger_completed BOOL, opponent_completed BOOL, date1 DATETIME,\
                challenger_score INTEGER, opponent_score INTEGER,FOREIGN KEY(challenger) REFERENCES users(user_id), FOREIGN KEY(opponent) REFERENCES users(user_id), FOREIGN KEY(quiz) REFERENCES quizzes(quiz_id))"
cursor.execute(create_table)

#insert two users into user table
query = "INSERT INTO users VALUES(?, ?, ?, ?, ?)"
cursor.execute(query, (None, "ping_pong","pia@mail.com", pbkdf2_sha256.hash("password"), "somelink"))
cursor.execute(query, (None, "piaw","pia@mail.com", pbkdf2_sha256.hash("password"), "somelink"))
cursor.execute(query, (None, "hollypolly","holly@mail.com", pbkdf2_sha256.hash("123"), "somelink"))
cursor.execute(query, (None, "hulia","hulia@mail.com",pbkdf2_sha256.hash("piper7"), "somelink"))

#insert into quiz history
query = "INSERT INTO quiz_history VALUES(?, ?, ?, ?, ?)"
cursor.execute(query, (None, 1, 1, 0, datetime.utcnow().replace(microsecond=0)))
cursor.execute(query, (None, 1, 1, 5, datetime.utcnow().replace(microsecond=0)))

#insert into challenge history
query = "INSERT INTO challenge_history VALUES(?,?, ?, ?, ?, ?, ?, ?, ?)"
# cursor.execute(query, (None, 2,1, 1, True, False, datetime(2020, 9, 22, 2, 40, 0), 4, 0))
# cursor.execute(query, (None, 2,1, 1, True, False, datetime(2020, 9, 22, 2, 43, 0), 4, 0))
# cursor.execute(query, (None, 2,1, 1, True, False, datetime(2020, 9, 22, 2, 41, 0), 4, 0))
# cursor.execute(query, (None, 3,1, 1, True, False, datetime.utcnow().replace(microsecond=0) + timedelta(days=1), 2, 0))

cursor.execute(query, (None, 3,1, 2, True, True, datetime.utcnow().replace(microsecond=0) + timedelta(days=1), 3, 1))
cursor.execute(query, (None, 3,1, 2, True, True, datetime.utcnow().replace(microsecond=0) + timedelta(days=1), 1, 3))
cursor.execute(query, (None, 1,3, 2, True, True, datetime.utcnow().replace(microsecond=0) + timedelta(days=1), 1, 3))

# cursor.execute(query, (None, 1,3, 2, True, False, datetime(2020, 9, 22, 2, 39, 0), 3, 1))

#insert into quizzes
query = "INSERT INTO quizzes VALUES(?, ?, ?, ?, ?, ?, ?)"
cursor.execute(query, (None, "Animal Quiz", "Testing your knowledge on weird and rare animals", "Pia Wetzel", "Animals", 100, datetime.utcnow()))
cursor.execute(query, (None, "Citizenship Quiz", "Five hard questions testing your civics knowledge", "Pia Wetzel", "History", -500, datetime.utcnow()))



#insert votes
query = "INSERT INTO votes VALUES(NULL, ?, ?, ?, ?)"
cursor.execute(query, (1, 1, 1, 0))
cursor.execute(query, (2, 2, 0, 1))
cursor.execute(query, (1, 2, 1, 0))
cursor.execute(query, (2, 3, 1, 0))
cursor.execute(query, (1, 3, 1, 0))

query = "INSERT INTO quiz_questions VALUES(?, ?, ?)"
#Questions for Q1
cursor.execute(query, (None, "How many Northern White Rhinos exist",1))#3
cursor.execute(query, (None, "The Tiger Quoll is also known as",1)) #Tiger Cat
cursor.execute(query, (None, "What is a Vaquita?",1)) #A porpoise
cursor.execute(query, (None, "A Spoon-Billed Sandpiper breeds in ",1))#Russia
cursor.execute(query, (None, "A Saola is also known as ",1))#Asian Unicorn
#Questions for Q2
cursor.execute(query, (None, "How many voting members does the House of Representative have?",2))#435
cursor.execute(query, (None, "For how many years is a U.S. Representative elected?",2)) #2
cursor.execute(query, (None, "Why have some states more Representatives than others?",2)) #because more ppl
cursor.execute(query, (None, "For how many years is a President elected?",2))#4
cursor.execute(query, (None, "In which month does the presidential election take place?",2))#November

query = "INSERT INTO quiz_answers VALUES(?,?,?,?)"

#Answers for Q2 Question1
cursor.execute(query, (None, "30",2, False))
cursor.execute(query, (None, "55",2, False))
cursor.execute(query, (None, "301",2, False))
cursor.execute(query, (None, "3",2, True))

#Answers for Q2 Question2
cursor.execute(query, (None, "Tiger Cat",5, True))
cursor.execute(query, (None, "Rodent Mouse",5, False))
cursor.execute(query, (None, "Zebra Horse",5, False))
cursor.execute(query, (None, "Mosquito Butterfly",5, False))

#Answers for Q2 Question3
cursor.execute(query, (None, "A wingless butterfly",3, False))
cursor.execute(query, (None, "A porpoise",3, True))
cursor.execute(query, (None, "A toad",3, False))
cursor.execute(query, (None, "A horse",3, False))

#Answers for Q2 Question4
cursor.execute(query, (None, "Spain",4, False))
cursor.execute(query, (None, "USA",4, False))
cursor.execute(query, (None, "Canada",4, False))
cursor.execute(query, (None, "Russia",4, True))

#Answers for Q2 Question5
cursor.execute(query, (None, "European flying carpet",1, False))#Asian Unicorn
cursor.execute(query, (None, "Asian unicorn",1, True))
cursor.execute(query, (None, "African golden swan",1, False))
cursor.execute(query, (None, "Australian pink rabbit",1, False))



conn_quiz.commit()
conn_quiz.close()