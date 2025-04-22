from flask import Flask, render_template, request, redirect, url_for, session
import subprocess
import tempfile
import os

from models import db, init_app, User

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize DB
init_app(app)

@app.route("/")
def home():
    if 'user' in session:
        return render_template("home.html", username=session['user'])
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match!")

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template("signup.html", error="Username or email already exists!")

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return render_template("signup.html", message="User registered successfully! Please login.")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user'] = username
            return redirect(url_for("editor"))
        else:
            return render_template("login.html", error="Invalid credentials!")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for("login"))

@app.route("/editor")
def editor():
    if 'user' in session:
        return render_template("editor.html", username=session['user'], code="", language="python", output="")
    return redirect(url_for("login"))

@app.route("/run_code", methods=["POST"])
def run_code():
    if 'user' not in session:
        return redirect(url_for("login"))

    code = request.form['code']
    language = request.form['language']
    output = ""

    try:
        if language == "python":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode='w') as temp:
                temp.write(code)
                temp.close()
                result = subprocess.run(["python", temp.name], capture_output=True, text=True, timeout=5)
                output = result.stdout + result.stderr
                os.remove(temp.name)

        elif language == "c":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".c", mode='w') as temp:
                temp.write(code)
                temp.close()
                exe_file = temp.name + ".exe"
                compile_process = subprocess.run(["gcc", temp.name, "-o", exe_file], capture_output=True, text=True)
                if compile_process.returncode != 0:
                    output = compile_process.stderr
                else:
                    run_process = subprocess.run([exe_file], capture_output=True, text=True, timeout=5)
                    output = run_process.stdout + run_process.stderr
                os.remove(temp.name)
                if os.path.exists(exe_file):
                    os.remove(exe_file)

        elif language == "javascript":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".js", mode='w') as temp:
                temp.write(code)
                temp.close()
                result = subprocess.run(["node", temp.name], capture_output=True, text=True, timeout=5)
                output = result.stdout + result.stderr
                os.remove(temp.name)

        else:
            output = "Unsupported language selected."

    except Exception as e:
        output = f"Error: {str(e)}"

    return render_template("editor.html", code=code, language=language, output=output, username=session['user'])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
