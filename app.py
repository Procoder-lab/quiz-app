from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "super_secret_teacher_key"

# --- DATABASE SETUP ---
database_url = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
# Handle PostgreSQL URL prefix change
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    opt1 = db.Column(db.String(200), nullable=False)
    opt2 = db.Column(db.String(200), nullable=False)
    opt3 = db.Column(db.String(200), nullable=False)
    opt4 = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.String(200), nullable=False)

class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)

def init_db():
    with app.app_context():
        db.create_all()

init_db()

# --- STUDENT ROUTES ---

@app.route("/")
def home():
    subjects = db.session.execute(db.select(db.func.distinct(Question.subject))).scalars().all()
    return render_template("index.html", subjects=[{"subject": s} for s in subjects])

@app.route("/quiz", methods=["POST"])
def quiz():
    student_name = request.form.get("student_name")
    subject = request.form.get("subject")

    db_questions = db.session.execute(
        db.select(Question).filter_by(subject=subject).order_by(db.func.random()).limit(10)
    ).scalars().all()

    questions = []
    for q in db_questions:
        questions.append({
            "id": f"q{q.id}",
            "question": q.question,
            "options": [q.opt1, q.opt2, q.opt3, q.opt4],
            "answer": q.answer
        })

    return render_template("quiz.html", questions=questions, student_name=student_name, subject=subject)

@app.route("/submit", methods=["POST"])
def submit():
    student_name = request.form.get("student_name")
    subject = request.form.get("subject")
    score = 0
    detailed_results = []
    
    all_db_questions = db.session.execute(db.select(Question)).scalars().all()
    question_dict = {f"q{q.id}": q for q in all_db_questions}
    
    questions_asked = 0
    
    for key, user_answer in request.form.items():
        if key.startswith('q') and key in question_dict:
            questions_asked += 1
            actual_q = question_dict[key]
            is_correct = (user_answer == actual_q.answer)
            if is_correct: 
                score += 1
            detailed_results.append({
                "question": actual_q.question,
                "user_answer": user_answer,
                "correct_answer": actual_q.answer,
                "is_correct": is_correct
            })
            
    new_score = Score(student_name=student_name, subject=subject, score=score, total=questions_asked)
    db.session.add(new_score)
    db.session.commit()
    
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
    if not session.get("logged_in"): 
        return redirect(url_for("login"))
    scores = db.session.execute(db.select(Score).order_by(Score.score.desc())).scalars().all()
    return render_template("leaderboard.html", scores=scores)

@app.route("/add", methods=["GET", "POST"])
def add_question():
    if not session.get("logged_in"): 
        return redirect(url_for("login"))

    if request.method == "POST":
        subject = request.form.get("subject")
        question = request.form.get("question")
        opt1 = request.form.get("opt1")
        opt2 = request.form.get("opt2")
        opt3 = request.form.get("opt3")
        opt4 = request.form.get("opt4")
        answer = request.form.get("answer")

        new_question = Question(subject=subject, question=question, opt1=opt1, opt2=opt2, opt3=opt3, opt4=opt4, answer=answer)
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for("add_question"))
        
    all_questions = db.session.execute(db.select(Question).order_by(Question.subject)).scalars().all()
    return render_template("add.html", questions=all_questions)

@app.route("/edit/<int:q_id>", methods=["GET", "POST"])
def edit_question(q_id):
    if not session.get("logged_in"): 
        return redirect(url_for("login"))
    
    question_to_edit = db.session.execute(db.select(Question).filter_by(id=q_id)).scalar_one_or_none()
    
    if request.method == "POST":
        subject = request.form.get("subject")
        question = request.form.get("question")
        opt1 = request.form.get("opt1")
        opt2 = request.form.get("opt2")
        opt3 = request.form.get("opt3")
        opt4 = request.form.get("opt4")
        answer = request.form.get("answer")
        
        question_to_edit.subject = subject
        question_to_edit.question = question
        question_to_edit.opt1 = opt1
        question_to_edit.opt2 = opt2
        question_to_edit.opt3 = opt3
        question_to_edit.opt4 = opt4
        question_to_edit.answer = answer
        db.session.commit()
        return redirect(url_for("add_question"))
        
    return render_template("edit.html", q=question_to_edit)

@app.route("/delete/<int:q_id>")
def delete_question(q_id):
    if not session.get("logged_in"): 
        return redirect(url_for("login"))
    question_to_delete = db.session.execute(db.select(Question).filter_by(id=q_id)).scalar_one_or_none()
    if question_to_delete:
        db.session.delete(question_to_delete)
        db.session.commit()
    return redirect(url_for("add_question"))

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=False)