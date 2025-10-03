from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

from flask_migrate import Migrate

migrate = Migrate(app, db)

# モデル定義
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text,nullable=True)
    review = db.Column(db.Text, nullable=True)
    read_date = db.Column(db.Date, default=datetime.utcnow)

    price = db.Column(db.Integer,nullable=True)
    publisher = db.Column(db.String(100),nullable=True)
    source = db.Column(db.String(100),nullable=True)
    rating = db.Column(db.Integer,nullable=True)
    genre = db.Column(db.String(50),nullable=True)
    knowledge = db.Column(db.Text,nullable=True)
    vocabulary = db.Column(db.Text,nullable=True)

class Insight(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    book_id = db.Column(db.Integer,db.ForeignKey("book.id"),nullable=False)
    content = db.Column(db.Text, nullable=False)

    book = db.relationship("Book", backref="insights")

class Vocabulary(db.Model):  # 語彙
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    word = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.Text, nullable=True)

    book = db.relationship("Book", backref="vocabularies")

# 初期化用
with app.app_context():
    db.create_all()

# 一覧表示と検索機能
@app.route("/",methods=["GET"])
def index():
    query = request.args.get("p")
    sort = request.args.get("sort")

    books_query = Book.query

    #検索
    if query:
        books = Book.query.filter(
            (Book.title.ilike(f"%{query}%")) | (Book.author.ilike(f"%{query}%"))
        ).order_by(Book.read_date.desc()).all()
    else:
        books = Book.query.order_by(Book.read_date.desc()).all()

    #ソート条件判定
    if sort == "date_asc":
        books_query = books_query.order_by(Book.read_date.asc())
    elif sort == "date_desc":
        books_query = books_query.order_by(Book.read_date.desc())
    elif sort == "price_asc":
        books_query = books_query.order_by(Book.price.asc())
    elif sort == "price_desc":
        books_query = books_query.order_by(Book.price.desc())
    elif sort == "rating_asc":
        books_query = books_query.order_by(Book.rating.asc())
    elif sort == "rating_desc":
        books_query = books_query.order_by(Book.rating.desc())
    else:
        books_query = books_query.order_by(Book.read_date.desc())
    
    books = books_query.all()

    #一覧表示
    return render_template("index.html",books=books,query=query,sort=sort)


# 登録フォーム
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        publisher = request.form["publisher"]
        price = request.form["price"]
        source = request.form["source"]
        summary = summary.form["summary"]
        review = request.form["review"]
        rating = request.form["rating"]
        genre = request.form["genre"]

        read_date_str = request.form["read_date"]
        if read_date_str:
            read_date = datetime.strptime(read_date_str,"%Y-%m-%d")
        else:
            read_date = datetime.utcnow()

        book = Book(
            title=title,
            author=author,
            publisher=publisher if publisher else None,
            price=int(price) if price else None,
            source=source if source else None,
            summary=summary if summary else None,
            review=review if review else None,
            rating=int(rating) if rating else None,
            read_date=read_date,
            genre=genre if genre else None,
            )
        
        
        
        db.session.add(book)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("add.html")


@app.route("/delete/<int:book_id>",methods=["POST"])
def delete(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/book/<int:book_id>",methods=["GET","POST"])
def detail(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == "POST":
        book.title = request.form["title"]
        book.author = request.form["author"]
        book.publisher = request.form["publisher"]
        book.genre = request.form["genre"] if request.form["genre"] else None
        book.price = request.form["price"]if request.form["price"]else None
        book.source = request.form["source"]
        book.summary = request.form["summary"] if request.form["summary"]else None
        book.review = request.form["review"]
        book.rating = int(request.form["rating"]) if request.form["rating"]else None
        book.read_date = datetime.strptime(request.form["read_date"],"%Y-%m-%d")if request.form["read_date"]else datetime.utcnow()
        
            # --- 知見を更新 ---
        db.session.query(Insight).filter_by(book_id=book.id).delete()
        insights_lines = request.form["insights_text"].splitlines()
        for line in insights_lines:
            line = line.strip()
            if line:
                db.session.add(Insight(content=line, book_id=book.id))

        # --- 語彙を更新 ---
        db.session.query(Vocabulary).filter_by(book_id=book.id).delete()
        vocab_lines = request.form["vocab_text"].splitlines()
        for line in vocab_lines:
            if ":" in line:
                word, meaning = line.split(":", 1)
                db.session.add(Vocabulary(word=word.strip(), meaning=meaning.strip(), book_id=book.id))

        
        db.session.commit()
        return redirect(url_for("detail",book_id=book.id))
    
    if request.method == "POST" and "insight" in request.form:
        new_insight = Insight(content=request.form["insight"], book=book)
        db.session.add(new_insight)
        db.session.commit()
        return redirect(url_for("detail", book_id=book.id))
    
    if request.method == "POST" and "word" in request.form:
        new_vocab = Vocabulary(word=request.form["word"], meaning=request.form["meaning"], book=book)
        db.session.add(new_vocab)
        db.session.commit()
        return redirect(url_for("detail", book_id=book.id))


    return render_template("detail.html",book=book)

# 知見一覧
@app.route("/insights")
def insights():
    insights = Insight.query.all()
    return render_template("insights.html", insights=insights)

 #語彙一覧
@app.route("/vocabularies")
def vocabularies():
    vocabularies = Vocabulary.query.all()
    return render_template("vocabularies.html", vocabularies=vocabularies)



#統計データ
@app.route("/stats")
def stats():
    #総数と合計費用
    total_books = Book.query.count()
    total_cost = db.session.query(db.func.sum(Book.price)).scalar() or 0

    #月別の集計
    monthly_data = (
        db.session.query(
            db.func.strftime("%Y-%m",Book.read_date).label("month"),
            db.func.count(Book.id),
            db.func.sum(Book.price)
        )
        .group_by("month")
        .order_by("month")
        .all()
    )

    return render_template("stats.html",total_books=total_books,total_cost=total_cost,monthly_data=monthly_data)


if __name__ == "__main__":
    app.run(debug=True)
