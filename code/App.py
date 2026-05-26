from flask import Flask, render_template, request, redirect, session
import mysql.connector
import random
import bcrypt

app = Flask(__name__)
app.secret_key = "final_project_secret_key"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Shyamal123",
    database="student_onboarding"
)

cursor = db.cursor()

@app.route("/")
def home():
    return redirect("/login_page")

@app.route("/signup_page")
def signup_page():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    cursor.execute("SELECT email FROM students WHERE email=%s", (email,))
    if cursor.fetchone():
        return "Email already exists ❌"

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    otp = str(random.randint(1000, 9999))

    cursor.execute("""
        INSERT INTO students(name,email,password,role,status,otp)
        VALUES(%s,%s,%s,%s,%s,%s)
    """, (name, email, hashed_password, "student", "Pending", otp))

    db.commit()
    session["verify_email"] = email

    print("================================")
    print("Student Email:", email)
    print("Generated OTP:", otp)
    print("================================")

    return redirect("/verify_page")

@app.route("/verify_page")
def verify_page():
    return render_template("verify.html")

@app.route("/verify", methods=["POST"])
def verify():
    otp = request.form["otp"]
    email = session.get("verify_email")

    if not email:
        return redirect("/signup_page")

    cursor.execute("SELECT otp FROM students WHERE email=%s", (email,))
    data = cursor.fetchone()

    if data and data[0] == otp:
        cursor.execute("UPDATE students SET status='Approved' WHERE email=%s", (email,))
        db.commit()
        session.pop("verify_email", None)
        return redirect("/login_page")

    return "OTP Verification Failed ❌"

@app.route("/login_page")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    cursor.execute("""
        SELECT email,password,role,status,name
        FROM students
        WHERE email=%s
    """, (email,))

    user = cursor.fetchone()

    if not user:
        return "User not found ❌"

    db_password = user[1]
    role = user[2]
    status = user[3]
    name = user[4]

    if status != "Approved":
        return "Account Pending Approval ❌"

    if bcrypt.checkpw(password.encode(), db_password.encode()):
        session["user"] = email
        session["name"] = name
        session["role"] = role

        if role == "admin":
            return redirect("/admin_dashboard")

        return redirect("/student_dashboard")

    return "Incorrect Password ❌"

@app.route("/student_dashboard")
def student_dashboard():
    if "user" in session:
        email = session["user"]

        cursor.execute("""
            SELECT name,email,phone,course,department,address
            FROM students
            WHERE email=%s
        """, (email,))

        student = cursor.fetchone()

        message = session.pop("message", None)

        return render_template(
            "student_dashboard.html",
            student=student,
            message=message
        )

    return redirect("/login_page")

@app.route("/save_profile", methods=["POST"])
def save_profile():
    if "user" not in session:
        return redirect("/login_page")

    phone = request.form["phone"]
    course = request.form["course"]
    department = request.form["department"]
    address = request.form["address"]
    email = session["user"]

    cursor.execute("""
        UPDATE students
        SET phone=%s, course=%s, department=%s, address=%s
        WHERE email=%s
    """, (phone, course, department, address, email))

    db.commit()

    session["message"] = "Profile saved successfully ✅"

    return redirect("/student_dashboard")

@app.route("/admin_dashboard")
def admin_dashboard():
    if "user" in session and session["role"] == "admin":

        cursor.execute("""
            SELECT name,email,phone,course,department,address,status
            FROM students
        """)

        students = cursor.fetchall()

        return render_template("admin_dashboard.html", students=students)

    return redirect("/login_page")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login_page")

if __name__ == "__main__":
    app.run(debug=True)
