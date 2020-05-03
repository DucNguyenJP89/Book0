import os
import requests

from flask import Flask, flash, render_template, request, session, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

app.secret_key = b'7\xfeI\xc8\xf1g\xb2\xc4=\xe1b\xad~\xf8\xe6\xa9'

@app.route("/")
def home():
    if not session.get("logged_in"):
        return render_template("login.html")
    else:
        return render_template("booksearch.html", message=f"Welcome back! {session.get('username')}")

@app.route("/login", methods=["POST"])
def login():
    #get user information.
    error = None
    username = request.form.get("username")
    password = request.form.get("password")
    if db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": username, "password": password}).rowcount ==  1:
        session['logged_in'] = True
        session['username'] = username
        return render_template("booksearch.html", message="You have successfully logged in.")
    else:
        error = "Login failed. Please check your username or password."
        return render_template("login.html", error = error)

@app.route("/logout")
def logout():
    #remove session
    session.pop('username', None)
    session['logged_in'] = False
    return render_template("login.html")

@app.route("/register.html")
def registration():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    #check username existed or not.
    error = None
    username = request.form.get("username")
    password = request.form.get("password")
    if db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).rowcount != 0:
        error = "This username already existed. Please try another username."
        return render_template("register.html", error = error)
    else:
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": username, "password": password})
        db.commit()
        session['logged_in'] = True
        session['username'] = username
        return render_template("booksearch.html", message = "You have successfully registered.")

@app.route("/search_result", methods=["POST"])
def search():
    #get user input.
    user_input = str(request.form.get("search_text"))
    search_str = '%'+user_input+'%'
    search_result = db.execute("SELECT * FROM books WHERE isbn LIKE :string OR author LIKE :string OR title LIKE :string", {"string": search_str}).fetchall()
    book_count = len(search_result)
    return render_template("book_result.html", book_count = book_count, search_result = search_result)

@app.route("/books/<string:isbn>", methods=["POST", "GET"])
def book(isbn):
    #Check if isbn code exists.
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return render_template("error.html", message="No book found with this isbn. Please try again.")

    #get comments.
    comments = db.execute("SELECT * FROM user_comment WHERE isbn=:isbn", {"isbn": isbn}).fetchall()

    #check if user commented
    username = session.get("username")
    user_check = False
    if db.execute("SELECT * FROM user_comment WHERE isbn=:isbn AND username=:username", {"isbn":isbn, "username": username}).rowcount == 1:
        user_check = True

    if request.method == "POST":
            rate_score = int(request.form.get("rating"))
            comment_content = request.form.get("comment_content")
            comment={"username": username, "rate_score": rate_score, "comment_content": comment_content}
            comments.append(comment)
            user_check = True
            db.execute("INSERT INTO user_comment (isbn, username, rate_score, comment_content) VALUES (:isbn, :username, :rate_score, :comment_content)", {"isbn":isbn, "username": username, "rate_score": rate_score, "comment_content": comment_content})
            db.commit()


    #Get ratings from Goodreads API
    key = "iNP9LfqxwnTkU5z9ygJPaA"
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
    if res.status_code == 404:
        return render_template("book_details.html", book=book, work_ratings_count="No data", average_rating="No data", comments=comments, user_check=user_check)
    data = res.json()['books'][0]
    work_ratings_count = data['work_ratings_count']
    average_rating = data['average_rating']

    return render_template("book_details.html", book=book, work_ratings_count=work_ratings_count, average_rating=average_rating, comments=comments, user_check=user_check)

@app.route("/api/<string:isbn>")
def api_book(isbn):
    #check if isbn exists.
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn":isbn}).fetchone()
    if isbn is None:
        return jsonify({"error": "No book found with this code."}), 422

    #check if comments existed.
    if db.execute("SELECT * FROM user_comment WHERE isbn=:isbn", {"isbn":isbn}).rowcount == 0:
        return jsonify({
                "isbn": book.isbn,
                "title": book.title,
                "author": book.author,
                "year": book.year,
                "review_count": 0,
                "average_score": 0
        })
    review = db.execute("SELECT COUNT(*) AS review_count, AVG(rate_score) AS average_score FROM user_comment WHERE isbn=:isbn", {"isbn": isbn}).fetchone()
    review_count = review.review_count
    average_score = str(round(review.average_score, 1))
    return jsonify({
            "isbn": book.isbn,
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "review_count": review_count,
            "average_score": average_score
    })
