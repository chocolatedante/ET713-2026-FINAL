import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "student_secret_key"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_db():
    """
    Connects to the SQLite database.
    row_factory allows database rows to be used like dictionaries.
    """
    conn = sqlite3.connect("student_app.db")
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# DATABASE TABLE CREATION
# -----------------------------
def init_db():
    """
    Creates all database tables if they do not already exist.
    This runs when the app starts.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Stores user account information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Stores user tasks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            category TEXT,
            completed INTEGER DEFAULT 0
        )
    """)

    # Stores blog posts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)

    # Stores uploaded image filenames
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# HOME ROUTE
# -----------------------------
@app.route("/")
def home():
    """
    If the user is logged in, send them to the dashboard.
    If not, send them to the login page.
    """
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# -----------------------------
# REGISTER ROUTE
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Shows the register page.
    If the form is submitted, a new user account is created.
    """
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]

        # Hashes the password so the plain password is not stored
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
            flash("Account created successfully. Please log in.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Email already exists.")

        finally:
            conn.close()

    return render_template("register.html")


# -----------------------------
# LOGIN ROUTE
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Shows the login page.
    If the login form is submitted, it checks the email and password.
    """
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        conn.close()

        # Checks if the user exists and if the password matches
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# -----------------------------
# LOGOUT ROUTE
# -----------------------------
@app.route("/logout")
def logout():
    """
    Clears the session so the user is logged out.
    """
    session.clear()
    return redirect(url_for("login"))


# -----------------------------
# DASHBOARD ROUTE
# -----------------------------
@app.route("/dashboard")
def dashboard():
    """
    Main page after login.
    Only logged-in users can access this page.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")


# -----------------------------
# TASKS ROUTE
# -----------------------------
@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    """
    Shows the to-do list page.
    Users can add new tasks and view their current tasks.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # If the form is submitted, add a new task
    if request.method == "POST":
        title = request.form["title"]
        category = request.form["category"]

        cursor.execute(
            "INSERT INTO tasks (user_id, title, category) VALUES (?, ?, ?)",
            (session["user_id"], title, category)
        )
        conn.commit()

    # Get only the tasks that belong to the logged-in user
    cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (session["user_id"],))
    tasks = cursor.fetchall()

    conn.close()

    return render_template("tasks.html", tasks=tasks)


# -----------------------------
# COMPLETE TASK ROUTE
# -----------------------------
@app.route("/complete_task/<int:id>")
def complete_task(id):
    """
    Marks a task as completed.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("tasks"))


# -----------------------------
# DELETE TASK ROUTE
# -----------------------------
@app.route("/delete_task/<int:id>")
def delete_task(id):
    """
    Deletes a task from the database.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("tasks"))


# -----------------------------
# BLOG ROUTE
# -----------------------------
@app.route("/blogs", methods=["GET", "POST"])
def blogs():
    """
    Shows the blog page.
    Users can create and view their blog posts.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # If the form is submitted, add a blog post
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        cursor.execute(
            "INSERT INTO blogs (user_id, title, content) VALUES (?, ?, ?)",
            (session["user_id"], title, content)
        )
        conn.commit()

    # Get only the blog posts that belong to the logged-in user
    cursor.execute("SELECT * FROM blogs WHERE user_id = ?", (session["user_id"],))
    blogs = cursor.fetchall()

    conn.close()

    return render_template("blogs.html", blogs=blogs)


# -----------------------------
# DELETE BLOG ROUTE
# -----------------------------
@app.route("/delete_blog/<int:id>")
def delete_blog(id):
    """
    Deletes a blog post from the database.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM blogs WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("blogs"))


# -----------------------------
# IMAGE UPLOAD ROUTE
# -----------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    """
    Shows the upload page.
    Users can upload note images and view uploaded images.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # If the form is submitted, save the uploaded image
    if request.method == "POST":
        image = request.files["image"]

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            # Saves the actual image file into static/uploads
            image.save(image_path)

            # Saves the filename into the database
            cursor.execute(
                "INSERT INTO uploads (user_id, filename) VALUES (?, ?)",
                (session["user_id"], filename)
            )
            conn.commit()

    # Get only the uploads that belong to the logged-in user
    cursor.execute("SELECT * FROM uploads WHERE user_id = ?", (session["user_id"],))
    uploads = cursor.fetchall()

    conn.close()

    return render_template("upload.html", uploads=uploads)


# -----------------------------
# RUN THE APPLICATION
# -----------------------------
if __name__ == "__main__":
    # Creates uploads folder if it does not already exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Creates database tables
    init_db()

    app.run(debug=True)