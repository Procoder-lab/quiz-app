from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_teacher_key"

# --- DATABASE SETUP ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL, 
            question TEXT NOT NULL,
            opt1 TEXT NOT NULL,
            opt2 TEXT NOT NULL,
            opt3 TEXT NOT NULL,
            opt4 TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- STUDENT ROUTES ---

@app.route("/")
def home():
    conn = get_db_connection()
    subjects = conn.execute('SELECT DISTINCT subject FROM questions').fetchall()
    conn.close()
    return render_template("index.html", subjects=subjects)

@app.route("/quiz", methods=["POST"])
def quiz():
    student_name = request.form.get("student_name")
    subject = request.form.get("subject")

    conn = get_db_connection()
    db_questions = conn.execute('SELECT * FROM questions WHERE subject = ? ORDER BY RANDOM() LIMIT 10', (subject,)).fetchall()
    conn.close()

    questions = []
    for q in db_questions:
        questions.append({
            "id": f"q{q['id']}",
            "question": q["question"],
            "options": [q["opt1"], q["opt2"], q["opt3"], q["opt4"]],
            "answer": q["answer"]
        })

    return render_template("quiz.html", questions=questions, student_name=student_name, subject=subject)

@app.route("/submit", methods=["POST"])
def submit():
    student_name = request.form.get("student_name")
    subject = request.form.get("subject")
    score = 0
    detailed_results = []
    
    conn = get_db_connection()
    all_db_questions = conn.execute('SELECT * FROM questions').fetchall()
    question_dict = { f"q{q['id']}": q for q in all_db_questions }
    
    questions_asked = 0
    
    for key, user_answer in request.form.items():
        if key.startswith('q') and key in question_dict:
            questions_asked += 1
            actual_q = question_dict[key]
            is_correct = (user_answer == actual_q['answer'])
            if is_correct: score += 1
            detailed_results.append({
                "question": actual_q['question'],
                "user_answer": user_answer,
                "correct_answer": actual_q['answer'],
                "is_correct": is_correct
            })
            
    conn.execute('INSERT INTO scores (student_name, subject, score, total) VALUES (?, ?, ?, ?)', 
                 (student_name, subject, score, questions_asked))
    conn.commit()
    conn.close()
    
    return render_template("results.html", student_name=student_name, score=score, total=questions_asked, results=detailed_results)

# --- TEACHER ROUTES ---

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == "teacher123":
            session["logged_in"] = True
            return redirect(url_for("leaderboard")) 
        else:
            error = "Incorrect password."
    return render_template("login.html", error=error)

@app.route("/leaderboard")
def leaderboard():
    if not session.get("logged_in"): return redirect(url_for("login"))
    conn = get_db_connection()
    scores = conn.execute('SELECT * FROM scores ORDER BY score DESC').fetchall()
    conn.close()
    return render_template("leaderboard.html", scores=scores)

@app.route("/add", methods=["GET", "POST"])
def add_question():
    if not session.get("logged_in"): return redirect(url_for("login"))
    conn = get_db_connection()

    if request.method == "POST":
        subject = request.form.get("subject")
        question = request.form.get("question")
        opt1 = request.form.get("opt1")
        opt2 = request.form.get("opt2")
        opt3 = request.form.get("opt3")
        opt4 = request.form.get("opt4")
        answer = request.form.get("answer")

        conn.execute('INSERT INTO questions (subject, question, opt1, opt2, opt3, opt4, answer) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                     (subject, question, opt1, opt2, opt3, opt4, answer))
        conn.commit()
        return redirect(url_for("add_question"))
        
    all_questions = conn.execute('SELECT * FROM questions ORDER BY subject').fetchall()
    conn.close()
    return render_template("add.html", questions=all_questions)

@app.route("/edit/<int:q_id>", methods=["GET", "POST"])
def edit_question(q_id):
    if not session.get("logged_in"): return redirect(url_for("login"))
    conn = get_db_connection()
    
    if request.method == "POST":
        subject = request.form.get("subject")
        question = request.form.get("question")
        opt1 = request.form.get("opt1")
        opt2 = request.form.get("opt2")
        opt3 = request.form.get("opt3")
        opt4 = request.form.get("opt4")
        answer = request.form.get("answer")
        
        conn.execute('''
            UPDATE questions 
            SET subject=?, question=?, opt1=?, opt2=?, opt3=?, opt4=?, answer=?
            WHERE id=?
        ''', (subject, question, opt1, opt2, opt3, opt4, answer, q_id))
        conn.commit()
        conn.close()
        return redirect(url_for("add_question"))
        
    question_to_edit = conn.execute('SELECT * FROM questions WHERE id = ?', (q_id,)).fetchone()
    conn.close()
    return render_template("edit.html", q=question_to_edit)

@app.route("/delete/<int:q_id>")
def delete_question(q_id):
    if not session.get("logged_in"): return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute('DELETE FROM questions WHERE id = ?', (q_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("add_question"))

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=False)