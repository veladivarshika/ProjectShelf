
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "projectshelf-demo-secret-change-this"
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "zip", "docx", "pptx"}
def init_db():
    conn = sqlite3.connect("projectshelf.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        domain TEXT NOT NULL,
        description TEXT NOT NULL,
        technologies TEXT NOT NULL,
        github_link TEXT,
        file_name TEXT,
        original_file_name TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/projects")
def projects():
    return render_template("index.html")


@app.route("/project-details.html")
def project_details():
    return render_template("project-details.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 8:
            return "Please enter valid details. Password must be at least 8 characters."

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("projectshelf.db")
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )
            conn.commit()
            return "Registration successful! Your account has been saved."

        except sqlite3.IntegrityError:
            return "This email is already registered. Please use another email."

        finally:
            conn.close()

    return render_template("register.html")

    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = sqlite3.connect("projectshelf.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, password FROM users WHERE email = ?",
            (email,)
        )
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect(url_for("dashboard"))

        return "Invalid email or password. Please try again."

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["user_name"]
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/upload-project", methods=["GET", "POST"])
def upload_project():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        domain = request.form.get("domain", "").strip()
        description = request.form.get("description", "").strip()
        technologies = request.form.get("technologies", "").strip()
        github_link = request.form.get("github_link", "").strip()
        uploaded_file = request.files.get("project_file")

        if not all([title, domain, description, technologies]):
            return "Please fill in all required fields."

        if github_link and not (
            github_link.startswith("https://github.com/")
            or github_link.startswith("http://github.com/")
        ):
            return "Please enter a valid GitHub repository URL."

        if not github_link and (
            not uploaded_file or not uploaded_file.filename
        ):
            return "Please provide a GitHub link or upload a project file."

        saved_name = None
        original_name = None

        if uploaded_file and uploaded_file.filename:
            if not allowed_file(uploaded_file.filename):
                return "Allowed files: PDF, ZIP, DOCX and PPTX."

            original_name = secure_filename(uploaded_file.filename)
            if not original_name:
                return "Invalid filename."

            saved_name = secure_filename(
                f"{session['user_id']}_{os.urandom(8).hex()}_{original_name}"
            )

            uploaded_file.save(
                os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
            )

        conn = sqlite3.connect("projectshelf.db")
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects
                (user_id, title, domain, description, technologies,
                 github_link, file_name, original_file_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                title,
                domain,
                description,
                technologies,
                github_link or None,
                saved_name,
                original_name
            ))
            conn.commit()
        finally:
            conn.close()

        return redirect(url_for("my_projects"))

    return render_template("upload-project.html")


@app.route("/my-projects")
def my_projects():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("projectshelf.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM projects
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],))
    projects = cursor.fetchall()
    conn.close()

    return render_template("my-projects.html", projects=projects)





if __name__ == "__main__":
    app.run(debug=True)
