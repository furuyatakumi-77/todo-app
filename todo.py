from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_NAME = "todo.db"

# --- データベース初期化 ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            done INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# --- データ取得 ---
def get_todos():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, task, done FROM todos")
    todos = c.fetchall()
    conn.close()
    return todos

# --- データ追加 ---
def add_todo(task):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO todos (task) VALUES (?)", (task,))
    conn.commit()
    conn.close()

# --- データ削除 ---
def delete_todo(task_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM todos WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# --- データ更新 ---
def update_todo(task_id,new_task):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE todos SET task = ? WHERE id = ?", (new_task,task_id))
    conn.commit()
    conn.close()

#-----完了プラグ切り替え--------
def toggle_done(task_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        UPDATE todos
        SET done = CASE done WHEN 0 THEN 1 ELSE 0 END
        WHERE id = ?
    """,(task_id,))
    conn.commit()
    conn.close()

# --- ルーティング ---
@app.route("/")
def index():
    todos = get_todos()
    return render_template("index.html", todos=todos)

@app.route("/add", methods=["POST"])
def add():
    task = request.form.get("task")
    if task:
        add_todo(task)
    return redirect(url_for("index"))

@app.route("/edit/<int:task_id>",methods=["GET","POST"])
def edit(task_id):
    if request.method== "POST":
        new_task = request.form.get("task")
        if new_task:
            update_todo(task_id,new_task)
        return redirect(url_for("index"))
    else:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id,task FROM todos WHERE id = ?",(task_id,))
        todo = c.fetchone()
        conn.close()
        return render_template("edit.html",todo=todo)



@app.route("/delete/<int:task_id>")
def delete(task_id):
    delete_todo(task_id)
    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>", methods=['POST'])
def toggle(task_id):
    toggle_done(task_id)
    return redirect(url_for("index"))


# --- アプリ起動時に必ずDBを初期化 ---
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # RenderではPORTが自動設定される
    app.run(debug=True, host="0.0.0.0", port=port)