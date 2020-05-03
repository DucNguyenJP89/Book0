import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('postgresql://localhost/ducnguyen')
db = scoped_session(sessionmaker(bind=engine))

def main():
    #Get input from user.
    user_input = str(input())
    search_str = '%'+user_input+'%'
    search_result = db.execute("SELECT * FROM books WHERE isbn LIKE :string OR author LIKE :string OR title LIKE :string", {"string": search_str}).fetchall()
    book_count = len(search_result)
    if search_result is None:
        print("No result. Please search again.")
    print(f"{book_count} books found.")
    for book in search_result:
        print(f"{book.isbn}: {book.title} of {book.author} written in {book.year}.")

if __name__ == "__main__":
    main()
