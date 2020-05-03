import os
import requests

from flask import Flask, flash, render_template, request, redirect, session, abort
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

engine = create_engine('postgresql://localhost/ducnguyen')
db = scoped_session(sessionmaker(bind=engine))

app.secret_key = b'7\xfeI\xc8\xf1g\xb2\xc4=\xe1b\xad~\xf8\xe6\xa9'

@app.route("/<string:isbn>/<string:username>", methods=["POST", "GET"])
def comment(isbn, username):
    #Check if isbn code exists.
    comments = db.execute("SELECT * FROM user_comment WHERE isbn=:isbn", {"isbn": isbn}).fetchall()
    commented_flag = False
    if db.execute("SELECT * FROM user_comment WHERE isbn=:isbn AND username=:username", {"isbn":isbn, "username": username}).rowcount == 1:
        commented_flag = True
    if request.method=="POST":
        comment_content = request.form.get("comment_content")
        db.execute("INSERT INTO user_comment (isbn, username, comment_content) VALUES (:isbn, :username, :comment_content)", {"isbn":isbn, "username": username, "comment_content": comment_content})
        db.commit()
    return render_template("user_comment.html", comments=comments, commented_flag=commented_flag)
