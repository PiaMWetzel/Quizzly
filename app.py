import sqlite3, os
from PIL import Image
from User import User
from security import Password
from flask import Flask, jsonify, render_template, redirect, json, request, session, flash, url_for
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from functools import wraps
from flask_moment import Moment
from random import seed
from random import randint



app = Flask(__name__)
app.config["SECRET_KEY"] = "a secret key"

user = User(None)
DATABASE = "quiz.db"

moment = Moment(app)



def check_if_logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print("accessing wrapper: " )
        if not session.get("USER_ID"):
            flash("Please log in or register")
            return render_template("signup.html")
        global user 
        user = User(session.get("USER_ID"))
        return fn(*args, **kwargs)
    return wrapper

def get_db_content(query, tup, fetchall=False):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    if fetchall:
        if tup == None:
            result = cursor.execute(query).fetchall()
        else:
            result = cursor.execute(query, tup).fetchall()
    else:
        if tup == None:
            result = cursor.execute(query).fetchone()
        else:
            result = cursor.execute(query, tup).fetchone()
    conn.close()
    return result

def insert_db_content(query, tup, set_uid=False):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(query, tup)
    conn.commit()
    if set_uid:
        session["USER_ID"] = cursor.lastrowid

    conn.close()

#def timer():
    


def update_user():
    if session.get("USER_ID"):
        global user
        user = User(session.get("USER_ID"))

def logout():
    session.pop('USER_ID', None)

def get_quiz_list(order_by="quizzes.quiz_id", category = ""):
    if order_by == "default":
        order_by = "quizzes.quiz_id"
    if category == "All":
        category = ""

    query = "SELECT quizzes.quiz_id, quizzes.title, quizzes.description, quizzes.author, quizzes.category, quizzes.votes, votes.upvote, votes.downvote FROM quizzes LEFT JOIN votes ON votes.quiz_id = quizzes.quiz_id AND user_id=? WHERE quizzes.category LIKE '{}%' ORDER BY {} ".format(category, order_by)
    results = get_db_content(query,(user.get_user_id(), ), True)
    return [dict(zip(('id', 'title', 'description', 'author', 'category', 'votes', 'upvotes','downvotes'), result)) for result in results]

def check_if_user_exists(username):
    query = "SELECT * FROM users WHERE username=?"
    results = get_db_content(query, (username.lower(),))
    if results == None:
        return False
    return True

@app.route("/test1")
def test1():
    # test_pw = "password"
    # print(test_pw)
    # encr_test_pw = Password.encrypt_password(test_pw)
    # print(encr_test_pw)
    # r = Password.check_if_password_matches(3, test_pw)
    # print(r)

    return render_template("start.html")


@app.route("/add_challenge", methods = ["POST"])
def add_challenge():
    response = request.get_json()
    opponent_id = response['opponent_id']
    score = response['score']
    quiz_id = response['quiz_id']

    query = "INSERT INTO challenge_history VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)"
    insert_db_content(query, (user.get_user_id(), opponent_id, quiz_id, True, False, datetime.utcnow().replace(microsecond=0) + timedelta(days=1), score, None))
    
    return {"ok":20000}


@app.route("/")
def index():
    return redirect("/1/All/default")

@app.route("/<int:page>/<string:category>/<string:sort_by>")
def get_start(page = 1, category='All', sort_by = 'default'):
    update_user()
    prompts  ={"date":"quizzes.date_created DESC", "default":"quizzes.quiz_id", "highest_score":"quizzes.votes DESC", "lowest_score":"quizzes.votes"}
    res = get_quiz_list(prompts[sort_by], category)
    results = get_db_content("SELECT DISTINCT category FROM quizzes ORDER BY category", None, True)
    categories = [result[0] for result in results]
    start = (page-1)*10
    end = page*10
    if len(res) < end:
        end = len(res)
    if len(res) < start:
        start = int(end/10)*10
    
    number_of_pages = int(len(res)/10)
    if len(res)%10 > 0:
        number_of_pages += 1
    
    if number_of_pages <= page:
        page = number_of_pages

    #get best performing users
    #most quizzes
    results = get_db_content("SELECT username, user_id, COUNT(quiz_history.user) AS quiz_count FROM users INNER JOIN quiz_history ON quiz_history.user = users.user_id GROUP BY username ORDER BY quiz_count DESC LIMIT 1", None, True)
    print(results)
    most_quizzes = [result for result in results[0]]
    fname = "images/ProfilePics/{}.png".format(most_quizzes[1])
    most_quizzes[1] = url_for("static", filename=fname)

    #best average
    results = get_db_content("SELECT username, user_id, (AVG(quiz_history.result))*100/5 AS quiz_avg FROM users INNER JOIN quiz_history ON quiz_history.user = users.user_id GROUP BY username ORDER BY quiz_avg DESC LIMIT 1", None, True)
    best_avg = [result for result in results[0]]
    fname = "images/ProfilePics/{}.png".format(best_avg[1])
    best_avg[1] = url_for("static", filename=fname)
    print(results)
    return render_template("start.html", quizzes=res[start:end], categories=categories, number_of_pages = number_of_pages, current_page = page, category=category, sort_by=sort_by, most_quizzes = most_quizzes, best_avg = best_avg )


@app.route("/signup")
def sign_up():
    return render_template("signup.html")

@app.route("/register_user", methods = ["POST"])
def register_user():
    print("signup in progress...")
    response = request.get_json()
    username = response['username']
    password = response['password']
    email = response['email']
    if not check_if_user_exists(username):
        query = "INSERT INTO users VALUES(?,?,?,?,?)"
        insert_db_content(query, (None, username.lower(), email.lower(), Password.encrypt_password(password), "blub blah"), True)
        update_user()
        upload_image(Image.open("static/images/ProfilePics/0.png"))
        print("signup completed")
        
    else:
        return {"message":"user already exists"}, 500
    return {"message":"successfully registered user"}, 200

    
@app.route("/complete_challenge", methods = ["POST"])
def complete_challenge():

    response = request.get_json()
    challenge_id = response['challenge_id']
    score = response['score']
    query = "UPDATE challenge_history SET opponent_score=? WHERE challenge_id=?"
    insert_db_content(query, (score, challenge_id))
    return render_template("/user_profile.html")

@app.route("/challenge", methods=["POST"])
def challenge():
    response = request.get_json()
    opponent = response['opponent_id']
    score = response['score']
    quiz_id = response['quiz_id']

    print(f"opponent: {opponent}")
    print(f"score: {score}")
    print(f"quiz_id: {quiz_id}")
    query = "INSERT INTO challenge_history Values(NULL, ?, ?, ?, ?, ?, ?, ?, ?)"
    insert_db_content(query, (user.get_user_id(), opponent,quiz_id, True, False, datetime.utcnow().replace(microsecond=0) + timedelta(days=1), score, 0))
    return {"hello": "hello"}


@app.route("/quiz/<int:quiz_id>/<int:challenge_id>", methods=["GET"])
@check_if_logged_in
def quiz(quiz_id, challenge_id):
    query = "SELECT quiz_questions.question, quiz_answers.answer, quiz_answers.correct FROM quiz_questions INNER JOIN quiz_answers ON quiz_answers.belongs_to=quiz_questions.question_id WHERE quiz_questions.belongs_to=?"
    questions = get_db_content(query,(quiz_id,), True)
    print("piaiaiaiiaiai")
    print(questions)
    return render_template("quiz.html", questions=json.dumps(questions), challenge_id = json.dumps(challenge_id), quiz_id  =json.dumps(quiz_id))

@app.route("/test")
def test():
    print("reached test")
    info = {"quiz_id":1, "score": 100}
    
    answers=[['eee','eeaaa hdhdhdhdhdhhdhd djdjjdd','kdkdd'],['eee','eeaaahdhdhdhdhdhhdhd djdjjdd','kdkdd'],['eee hdhdhdhdhdhhdhd djdjjdd','eeaaa hdhdhdhdhdhhdhd djdjjdd','kdkdd'],['eee','eeaaa hdhdhdhdhdhhdhd djdjjdd','kdkdd'],['eee','eeaaa','kdkdd']]
    answers=[['eee','eeaaa','kdkdd'],['eee','eeaaa','kdkdd'],['eee','eeaaa','kdkdd'],['eee','eeaaa','kdkdd'],['eee','eeaaa','kdkdd']]

    return render_template("result.html", answers=answers, udata=None, info=json.dumps(info))

@app.route("/get_challengers", methods=["POST"])
def get_challengers():

    response = request.get_json()
    user_input = response["user_input"]

    if user_input == "":
        return None
    query = "SELECT user_id, username, image FROM users WHERE username LIKE '{}%' AND user_id IS NOT {}".format(user_input, session["USER_ID"])
    results = get_db_content(query,None, True)
    re = [dict(zip(('user_id', 'username', 'link'), result)) for result in results]

    print(json.dumps(re))

    return json.dumps(re)


@app.route("/results", methods=["POST"])
def result():
    response = request.get_json()
    user_answers = response['user_answers']
    quiz_id = response['quiz_id']
    challenge_id = response['challenge_id']
    print(f"challenge id: {challenge_id}")
    print(f"quiz id: {quiz_id}")

    #get title of quiz
    query = "SELECT title FROM quizzes WHERE quiz_id=?"
    quiz_title = get_db_content(query, (quiz_id,), False)

    query = "SELECT answer, quiz_questions.question FROM quiz_answers JOIN quiz_questions ON quiz_questions.question_id = quiz_answers.belongs_to WHERE quiz_questions.belongs_to=? AND quiz_answers.correct=?"
    results = get_db_content(query, (quiz_id, True), True)
    answers = [str(result[0]) for result in results]
    questions = [result[1] for result in results]
    score = sum([1 for i in range(0, len(answers)) if str(answers[i]) == user_answers[i]])
    #if challenge...
    if int(challenge_id) > 0:
        query = "UPDATE challenge_history SET opponent_score=?, opponent_completed=? WHERE challenge_id=?"
        insert_db_content(query, (score, True, challenge_id))
        #query = "SELECT challenger_score, opponent_score FROM challenge_history WHERE challenge_id=?"
        info = {"quiz_id":1, "score": score, "challenge_id":challenge_id}
        return render_template("result.html", answers = zip(questions,user_answers, answers), score=score, info = json.dumps(info))
    #if regular quiz...
    print("User answers {}".format(user_answers))
    print("Correct answers {}".format(answers))
    print("score: {}".format(score))

    info = {"quiz_id":quiz_id, "score": score, "challenge_id":challenge_id, "quiz_title":quiz_title}

    return render_template("result.html", answers = zip(questions,user_answers, answers), score=score, info = json.dumps(info), quiz_title=quiz_title[0])

@app.route("/add_quiz_history", methods=["POST"])
def add_quiz_history():
    response = request.get_json()
    score = response['score']
    quiz_id = response['quiz_id']
    query = "INSERT INTO quiz_history VALUES(NULL, ?, ?, ?, ?)"
    insert_db_content(query, (user.get_user_id(), quiz_id, score, datetime.utcnow().replace(microsecond=0)))

    return redirect("/")


@app.route("/log_in", methods=["POST"])
def login():
    print("hello - logging in")
    response = request.get_json()
    username = response['username']
    password = response['password']

    if check_if_user_exists(username):
        query = "SELECT user_id FROM users WHERE username=?"
        result = get_db_content(query, (username.lower(),))
        verify_pw = Password.check_if_password_matches(result[0], password)
        print(result)
        if verify_pw == False:
            return {"message":"Incorrect username or password"}, 500
        else:
            user =  User(result[0])
            print(user.get_username())
            session["USER_ID"] = result[0]
            return {"message":"successfully logged in"}, 200

@app.route("/profile")
@check_if_logged_in
def profile():
    # response = request.get_json()
    # username = response['username']
    # user_id = response["user_id"]

    username = user.get_username()
    user_id = user.get_user_id()
    email = user.get_email()
    fname = "images/ProfilePics/{}.png".format(user_id)
    image = url_for("static", filename=fname)

    #get list of completed quizzes
    query = "SELECT quiz_history.result, DATE(quiz_history.date1) as 'DATE()', quizzes.title from quiz_history INNER JOIN quizzes ON quizzes.quiz_id = quiz_history.quiz WHERE user=?"
    results = get_db_content(query, (user_id,), True)
    completed_quizzes = [dict(zip(('result', 'date', 'title'), result)) for result in results]

    #get datetime for completed quizzes
    query = "SELECT quiz_history.date1 from quiz_history INNER JOIN quizzes ON quizzes.quiz_id = quiz_history.quiz WHERE user=?"
    results = get_db_content(query, (user_id,), True)
    times3 = [datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S') for result in results]
    print(times3)
    print(datetime.utcnow().date().strftime('%Y-%m-%d'))
    print(completed_quizzes)
    print(completed_quizzes)
    todays_quizzes = [comp for comp in completed_quizzes if (comp['date'] == datetime.utcnow().date().strftime('%Y-%m-%d'))]
    print("piababooon")
    print(todays_quizzes)
    #all time score
    total_score = 0
    #todays score
    todays_score = 0

    #total score
    print("pppp")
    print(sum([quiz['result'] for quiz in completed_quizzes]))
    if len(completed_quizzes) > 0:
        total_score = int((sum([quiz['result'] for quiz in completed_quizzes])/len(completed_quizzes))*(100/(5)))
    #todays score
    if len(todays_quizzes) > 0:
        todays_score = int(sum([quiz['result'] for quiz in todays_quizzes])/len(todays_quizzes)*(100/(5)))

    #print(completed_quizzes)

    #get list of open challenges (someone challenged you)
    #time(strftime('%H','2017-11-01 22:25:28') - strftime('%H',challenge_history.date1), 'unixepoch')
    query = "SELECT challenge_history.challenge_id,quizzes.quiz_id, quizzes.title, users.username from challenge_history INNER JOIN quizzes ON quizzes.quiz_id = challenge_history.quiz INNER JOIN users ON users.user_id = challenge_history.challenger WHERE opponent=? AND opponent_completed=? ORDER BY challenge_history.date1 ASC"
    results = get_db_content(query, (user_id, False), True)
    open_challenges = [dict(zip(('challenge_id','quiz_id','title', 'username', 'remtime'), result)) for result in results]
    print(open_challenges)

    war_start = '2011-01-03 5:12:12'
    b = datetime.strptime(war_start, '%Y-%m-%d %H:%M:%S')
    print(b)
    #get expiration date/time
    query = "SELECT challenge_history.date1 from challenge_history INNER JOIN quizzes ON quizzes.quiz_id = challenge_history.quiz INNER JOIN users ON users.user_id = challenge_history.challenger WHERE opponent=? AND opponent_completed=? ORDER BY challenge_history.date1 ASC"
    results = get_db_content(query, (user_id, False), True)
    times = [datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S') for result in results]
    #[datetime(result[0]) for result in results]
    print(times)
 

    #get list of open challenges (you challened someone)
    query = "SELECT challenge_history.challenge_id,quizzes.quiz_id, quizzes.title, users.username from challenge_history INNER JOIN quizzes ON quizzes.quiz_id = challenge_history.quiz INNER JOIN users ON users.user_id = challenge_history.opponent WHERE challenger=? AND opponent_completed=? ORDER BY challenge_history.date1 ASC"
    results = get_db_content(query, (user_id, False), True)
    open_challenges_you = [dict(zip(('challenge_id','quiz_id','title', 'username'), result)) for result in results]
    print(open_challenges_you)

     #get expiration date/time open challenges
    query = "SELECT challenge_history.date1 from challenge_history INNER JOIN quizzes ON quizzes.quiz_id = challenge_history.quiz INNER JOIN users ON users.user_id = challenge_history.opponent WHERE challenger=? AND opponent_completed=? ORDER BY challenge_history.date1 ASC"
    results = get_db_content(query, (user_id, False), True)
    times2 = [datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S') for result in results]
    print("jejejejeje")

    #get list of completed challenges
    query = "SELECT challenge_history.challenge_id, quizzes.quiz_id, quizzes.title, users.username, \
            challenge_history.opponent,challenge_history.challenger_score, challenge_history.opponent_score from challenge_history INNER JOIN \
            quizzes ON quizzes.quiz_id = challenge_history.quiz INNER JOIN users ON users.user_id = \
            (case when (challenge_history.challenger = ?) then (challenge_history.opponent) else \
            (challenge_history.challenger) END) WHERE (opponent=? OR challenger=?) AND opponent_completed=?"

    results = get_db_content(query, (user_id, user_id,user_id, True), True)
    completed_challenges = [dict(zip(('challenge_id','quiz_id', 'title', 'username', 'opponent', 'challenger_score', 'opponent_score'), result)) for result in results]
    print(completed_challenges)

    q, op = get_soonest_expiring_challenge(open_challenges, times, open_challenges_you, times2)
    print("q: " + str(q))
    print("challenge id for deletion is " + str(op))
    return render_template("user_profile.html", quizzes = completed_quizzes, times3=times3, open_challenges = open_challenges, open_challenges_you=open_challenges_you, completed_challenges = completed_challenges, total_count = len(completed_quizzes), today_count=len(todays_quizzes),\
                            total_score = total_score, today_score = todays_score, username=username, email = email, image=image, user_id = session["USER_ID"], s_time = b, times=times, times2=times2, shortest_t = q, c_id = op)


#get challenge expiring the soonest
def get_soonest_expiring_challenge(your, your_time, for_you, for_you_time):
    best = your
    best_time = your_time
    time_seconds = 0
    challenge_id = 0

    if your and for_you:
        if your_time[0] > for_you_time[0]:
           best = for_you
           best_time = for_you_time
    elif for_you and not your:
        best = for_you
        best_time = for_you_time
    else:
        return -1, -1

    time_seconds = (best_time[0] - datetime.utcnow()).seconds
    challenge_id = best[0]["challenge_id"]

    return time_seconds, challenge_id



#get votes

def get_votes():
    query = "SELECT quiz_id, upvote, downvote FROM votes WHERE user_id=?"
    results = get_db_content(query, (user.get_user_id(),), True)
    re = [dict(zip(('quiz_id', 'upvote', 'downvote'), result)) for result in results]

    return re

#upvote
@app.route("/upvote", methods = ["POST"])
def upvote():
    response = request.get_json()
    quiz_id = response['quiz_id']

    conn = sqlite3.connect("quiz.db")
    cursor = conn.cursor()
    query = "SELECT * FROM votes WHERE quiz_id = ? AND user_id=?"
    result = cursor.execute(query, (quiz_id, user.get_user_id())).fetchone()
    print(result)
    if not result:
        query = "INSERT INTO votes VALUES (NULL, ?, ?, ?, ?)"
        cursor.execute(query, (quiz_id, user.get_user_id(),True,False ))
        conn.commit()
        query = "UPDATE quizzes SET votes = votes + 1 WHERE quiz_id=?"
        cursor.execute(query, (quiz_id,))
        conn.commit()
    else:
        
        if result[3] == True:
            query = "UPDATE quizzes SET votes = votes - 1 WHERE quiz_id=?"
            cursor.execute(query, (quiz_id,))
            conn.commit()
            query = "DELETE FROM votes WHERE quiz_id=? AND user_id=?"
            cursor.execute(query, (quiz_id, user.get_user_id()))
            conn.commit()
        else:
            query = "UPDATE quizzes SET votes = votes + 2 WHERE quiz_id=?"
            cursor.execute(query, (quiz_id,))
            conn.commit()
            query = "UPDATE votes SET upvote=?, downvote=? WHERE quiz_id=? AND user_id=?"
            cursor.execute(query, (True, False, quiz_id, user.get_user_id()))
            conn.commit()
        conn.commit()

    query = "SELECT votes FROM quizzes WHERE quiz_id=?"
    result = cursor.execute(query, (quiz_id,)).fetchall()
    conn.commit()
    conn.close()

    return json.dumps({"votes":result[0]})

#downvote
@app.route("/downvote", methods = ["POST"])
def downvote():
    response = request.get_json()
    quiz_id = response['quiz_id']

    conn = sqlite3.connect("quiz.db")
    cursor = conn.cursor()
    query = "SELECT * FROM votes WHERE quiz_id = ? AND user_id=?"
    result = cursor.execute(query, (quiz_id, user.get_user_id())).fetchone()
    conn.commit()
    print(result)
    if not result:
        query = "INSERT INTO votes VALUES (NULL, ?, ?, ?, ?)"
        cursor.execute(query, (quiz_id, user.get_user_id(),False,True))
        conn.commit()
        query = "UPDATE quizzes SET votes = votes - 1 WHERE quiz_id=?"
        cursor.execute(query, (quiz_id,))
        conn.commit()
    else:
        if result[4] == True:
            query = "UPDATE quizzes SET votes = votes + 1 WHERE quiz_id=?"
            cursor.execute(query, (quiz_id,))
            conn.commit()
            query = "DELETE FROM votes WHERE quiz_id=? AND user_id=?"
            cursor.execute(query, (quiz_id, user.get_user_id()))
            conn.commit()
        else:       
            query = "UPDATE quizzes SET votes = votes - 2 WHERE quiz_id=?"
            cursor.execute(query, (quiz_id,))
            conn.commit()
            query = "UPDATE votes SET upvote=?, downvote=? WHERE quiz_id=? AND user_id=?"
            cursor.execute(query, (False,True, quiz_id, user.get_user_id()))
            conn.commit()
        conn.commit()

    query = "SELECT votes FROM quizzes WHERE quiz_id=?"
    result = cursor.execute(query, (quiz_id,)).fetchall()
    conn.commit()
    conn.close()

    return json.dumps({"votes":result[0]})

@app.route("/verify_username", methods=["POST"])
def verify_username():
    response = request.get_json()
    username = response['username']

    query = "SELECT * FROM users WHERE UPPER(username)=?"
    result = get_db_content(query, (username,))

    #username already exists
    if result:
        return json.dumps({"duplicate":True})

    return json.dumps({"duplicate":False})

@app.route("/verify_email", methods=["POST"])
def verify_email():
    response = request.get_json()
    email = response['email']

    query = "SELECT * FROM users WHERE UPPER(email)=?"
    result = get_db_content(query, (email,))

    #username already exists
    if result:
        return json.dumps({"duplicate":True})

    return json.dumps({"duplicate":False})


@app.route("/picture")
@check_if_logged_in
def picture():
    return render_template("/profile_picture.html")


def check_extension(filename):
    print(filename)
    permitted_extensions = {"jpg", "jpeg", "png", "gif"}
    extension = ((filename.split(".", 1))[1]).lower()
    print(extension)
    if extension in permitted_extensions:
        return True
    return False


@app.route("/upload_profile_picture", methods=["POST"])
def upload_profile_picture():
    print("uploading image")
    image = request.files['image']
    if upload_image(image):
        return {"message": "upload successful"},200
    return {"message": "something went wrong"},500
def upload_image(image):
    upload_path = "static/images/ProfilePics/"
    filename = secure_filename(image.filename)
    if check_extension(filename):
        image.save(os.path.join(upload_path, str(user.get_user_id())+".png"))
        return True
    return False

@app.route("/create_quiz")
@check_if_logged_in
def create_quiz():
    return render_template("/create-quiz.html")

@app.route("/save_user_quiz", methods=["POST"])
@check_if_logged_in
def save_user_quiz():

    #intialize user
    update_user()

    response = request.get_json()
    title = response['title']
    category = response['category']
    questions = response['questions']
    description = response['description']
    answers = response['answers']
    answer_corr = response['answer_correctness']

    print(questions)
    print(answers)
    print(answer_corr)
    print(title)

    conn = sqlite3.connect("quiz.db")
    cursor = conn.cursor()
    query = "INSERT INTO quizzes VALUES(NULL, ?, ?, ?, ?, ?, ?)"
    un = user.get_username()
    print(un)
    cursor.execute(query, (title, description, user.get_username(), category, 0, datetime.utcnow().replace(microsecond=0)))
    quiz_id = cursor.lastrowid

    query = "INSERT INTO quiz_questions VALUES(NULL, ?, ?)"

    counter = 0
    last_ids = []
    for question in questions:
        cursor.execute(query, (question, quiz_id))
        last_ids.append(cursor.lastrowid)
        counter = counter + 1


    query = "INSERT INTO quiz_answers VALUES(NULL, ?, ?, ?)"

    counter=0
    question=0
    for i in range(0, len(answer_corr)):
        cursor.execute(query, (answers[i], last_ids[question], answer_corr[i]))
        if counter >= 3:
            question = question + 1
            counter = 0
        else: 
            counter = counter+1
    conn.commit()
    


    return {"blub":"blah"}

@app.route("/verify_login_status", methods=["POST"])
def verify_login_status():
    if session.get('USER_ID'):
        print("logged in")
        return {"status":True}
    print("not logged in")
    return {"status":False}

@app.route("/log_out", methods=["POST"])
def log_out():
    logout()
    user.logout()
    return {"message":"successfully logged out"}, 200


@app.route("/delete_challenge", methods=["POST"])
def delete_challenge():
    response = request.get_json()
    challenge_id = response['challenge_id']
    query = "DELETE FROM challenge_history WHERE challenge_id=?"
    insert_db_content(query, (challenge_id,))
    return {"dd":"djdj"}

@app.route("/random_quiz")
@check_if_logged_in
def random_quiz():
    seed()
    num_quizzes = len(get_db_content("SELECT quiz_id FROM quizzes", None, True))
    value = randint(1,num_quizzes)
    return redirect(f"quiz/{value}/0")


@app.route("/see_all/quiz_history")
@check_if_logged_in
def see_quiz_history():
    user_id = session.get("USER_ID")
    query = "SELECT quiz_history.result, DATE(quiz_history.date1) as 'DATE()', quizzes.title from quiz_history INNER JOIN quizzes ON quizzes.quiz_id = quiz_history.quiz WHERE user=?"
    results = get_db_content(query, (user_id,), True)
    quizzes = [dict(zip(('result', 'date', 'title'), result)) for result in results]
    print(quizzes)
    times = [datetime.strptime(quiz['date'], '%Y-%m-%d') for quiz in quizzes]
    print(times)
    return render_template("see_quiz_history.html", quizzes = quizzes, times=times, user_id=user_id)


@app.route("/see_all/challenges")
@check_if_logged_in
def see_challenges():
    user_id = session.get("USER_ID")
    query = "SELECT challenge_history.challenge_id, challenge_history.date1, quizzes.quiz_id, quizzes.title, users.username, \
            challenge_history.opponent,challenge_history.challenger_score, challenge_history.opponent_score from challenge_history INNER JOIN \
            quizzes ON quizzes.quiz_id = challenge_history.quiz INNER JOIN users ON users.user_id = \
            (case when (challenge_history.challenger = ?) then (challenge_history.opponent) else \
            (challenge_history.challenger) END) WHERE (opponent=? OR challenger=?) AND opponent_completed=?"

    results = get_db_content(query, (user_id, user_id,user_id, True), True)
    challenges = [dict(zip(('challenge_id','time','quiz_id', 'title', 'username', 'opponent', 'challenger_score', 'opponent_score'), result)) for result in results]
    print(challenges)
    times = [datetime.strptime(challenge['time'], '%Y-%m-%d %H:%M:%S') for challenge in challenges]
    print(times)
    return render_template("see_challenges.html", challenges = challenges, times=times, user_id=user_id)
if __name__ == "__main__":
    app.run(port=5000)