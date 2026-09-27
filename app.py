from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import re
import uuid
from datetime import datetime
from difflib import SequenceMatcher
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "lost_found_secret_key_123"

# -----------------------------
# Upload Settings
# -----------------------------

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------------
# Login Required
# -----------------------------

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# -----------------------------
# File Validation
# -----------------------------

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# -----------------------------
# Date Validation
# -----------------------------

def valid_date(date_text):

    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True

    except (TypeError, ValueError):
        return False


# -----------------------------
# Text Normalization
# -----------------------------

def normalize_text(text):

    text = text or ""

    text = text.lower().strip()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# -----------------------------
# Similarity Calculation
# -----------------------------

def similarity(text1, text2):

    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    if not text1 or not text2:
        return 0.0

    if text1 == text2:
        return 1.0

    sequence_score = SequenceMatcher(
        None,
        text1,
        text2
    ).ratio()

    words1 = set(text1.split())
    words2 = set(text2.split())

    common_words = words1.intersection(words2)
    all_words = words1.union(words2)

    if all_words:
        word_score = len(common_words) / len(all_words)
    else:
        word_score = 0

    return max(
        sequence_score,
        word_score
    )


# -----------------------------
# Match Score
# -----------------------------

def calculate_match_score(lost, found):

    item_name_score = (
        similarity(
            lost["item_name"],
            found["item_name"]
        ) * 40
    )

    category_score = (
        similarity(
            lost["category"],
            found["category"]
        ) * 25
    )

    location_score = (
        similarity(
            lost["location"],
            found["location"]
        ) * 20
    )

    description_score = (
        similarity(
            lost["description"],
            found["description"]
        ) * 15
    )

    total_score = (
        item_name_score
        + category_score
        + location_score
        + description_score
    )

    return round(total_score)


# -----------------------------
# Match Details
# -----------------------------

def calculate_match_details(lost, found):

    item_similarity = similarity(
        lost["item_name"],
        found["item_name"]
    )

    category_similarity = similarity(
        lost["category"],
        found["category"]
    )

    location_similarity = similarity(
        lost["location"],
        found["location"]
    )

    description_similarity = similarity(
        lost["description"],
        found["description"]
    )

    item_score = round(
        item_similarity * 40
    )

    category_score = round(
        category_similarity * 25
    )

    location_score = round(
        location_similarity * 20
    )

    description_score = round(
        description_similarity * 15
    )

    total_score = (
        item_score
        + category_score
        + location_score
        + description_score
    )

    return {

        "item_similarity":
            round(item_similarity * 100),

        "category_similarity":
            round(category_similarity * 100),

        "location_similarity":
            round(location_similarity * 100),

        "description_similarity":
            round(description_similarity * 100),

        "item_score":
            item_score,

        "category_score":
            category_score,

        "location_score":
            location_score,

        "description_score":
            description_score,

        "total_score":
            total_score
    }


# -----------------------------
# Match Label
# -----------------------------

def match_label(score):

    if score >= 90:

        return "Very Strong Match"

    elif score >= 75:

        return "Strong Match"

    else:

        return "Possible Match"


# -----------------------------
# Create Database
# -----------------------------

def create_database():

    conn = sqlite3.connect(
        "lost_found.db"
    )

    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.commit()

    # Check existing columns
    cursor.execute(
        "PRAGMA table_info(items)"
    )

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    # Add image column
    if "image" not in columns:

        cursor.execute(
            "ALTER TABLE items ADD COLUMN image TEXT"
        )

    # Add user_id column
    if "user_id" not in columns:

        cursor.execute(
            "ALTER TABLE items ADD COLUMN user_id INTEGER"
        )

    # Add report_id column
    if "report_id" not in columns:

        cursor.execute(
            "ALTER TABLE items ADD COLUMN report_id TEXT"
        )

    # Add status column
    if "status" not in columns:

        cursor.execute(
            "ALTER TABLE items ADD COLUMN status TEXT DEFAULT 'Open'"
        )

    conn.commit()

    # Update old records
    cursor.execute("""
        SELECT id, item_type, report_id, status
        FROM items
    """)

    old_items = cursor.fetchall()

    for item in old_items:

        item_id = item[0]
        item_type = item[1]
        report_id = item[2]
        status = item[3]

        if not report_id:

            if item_type == "Lost":

                new_report_id = f"L{item_id:03d}"

            else:

                new_report_id = f"F{item_id:03d}"

            cursor.execute(
                """
                UPDATE items
                SET report_id=?
                WHERE id=?
                """,
                (
                    new_report_id,
                    item_id
                )
            )

        if not status:

            cursor.execute(
                """
                UPDATE items
                SET status='Open'
                WHERE id=?
                """,
                (item_id,)
            )

    conn.commit()
    conn.close()


# -----------------------------
# Home
# -----------------------------

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# -----------------------------
# Register
# -----------------------------

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not name or not email or not password:

            return render_template(
                "register.html",
                error="Please fill all fields."
            )

        if len(password) < 6:

            return render_template(
                "register.html",
                error="Password must contain at least 6 characters."
            )

        hashed_password = generate_password_hash(
            password
        )

        conn = sqlite3.connect(
            "lost_found.db"
        )

        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    email,
                    hashed_password
                )
            )

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "register.html",
                error="Email already registered."
            )

        conn.close()

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# -----------------------------
# Login
# -----------------------------

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        conn = sqlite3.connect(
            "lost_found.db"
        )

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]

            return redirect(
                url_for("dashboard")
            )

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template(
        "login.html"
    )


# -----------------------------
# FORGOT PASSWORD
# -----------------------------

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # Check empty fields
        if (
            not email
            or not new_password
            or not confirm_password
        ):

            return render_template(
                "forgot_password.html",
                error="Please fill all fields."
            )

        # Check password length
        if len(new_password) < 6:

            return render_template(
                "forgot_password.html",
                error="Password must contain at least 6 characters."
            )

        # Check password confirmation
        if new_password != confirm_password:

            return render_template(
                "forgot_password.html",
                error="Passwords do not match."
            )

        conn = sqlite3.connect(
            "lost_found.db"
        )

        cursor = conn.cursor()

        # Check email
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user:

            conn.close()

            return render_template(
                "forgot_password.html",
                error="No account found with this email."
            )

        # Hash new password
        hashed_password = generate_password_hash(
            new_password
        )

        # Update password
        cursor.execute(
            """
            UPDATE users
            SET password = ?
            WHERE email = ?
            """,
            (
                hashed_password,
                email
            )
        )

        conn.commit()
        conn.close()

        return render_template(
            "forgot_password.html",
            success="Password reset successfully. You can now login."
        )

    return render_template(
        "forgot_password.html"
    )


# -----------------------------
# Logout
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# -----------------------------
# Save Uploaded Image
# -----------------------------

def save_uploaded_image():

    image = request.files.get(
        "image"
    )

    if not image or not image.filename:

        return None

    if not allowed_file(
        image.filename
    ):

        return None

    original_filename = secure_filename(
        image.filename
    )

    unique_filename = (
        uuid.uuid4().hex
        + "_"
        + original_filename
    )

    image_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        unique_filename
    )

    image.save(
        image_path
    )

    return unique_filename


# -----------------------------
# Lost Item
# -----------------------------

@app.route(
    "/lost",
    methods=["POST"]
)
@login_required
def lost_item():

    item_name = request.form.get(
        "item_name",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    date = request.form.get(
        "date",
        ""
    ).strip()

    if not all([
        item_name,
        description,
        category,
        location,
        date
    ]):

        return redirect(
            url_for("home")
        )

    if not valid_date(date):

        return redirect(
            url_for("home")
        )

    image_filename = save_uploaded_image()

    conn = sqlite3.connect(
        "lost_found.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO items
        (
            item_type,
            item_name,
            description,
            category,
            location,
            date,
            image,
            user_id,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Lost",
            item_name,
            description,
            category,
            location,
            date,
            image_filename,
            session["user_id"],
            "Open"
        )
    )

    item_id = cursor.lastrowid

    report_id = f"L{item_id:03d}"

    cursor.execute(
        """
        UPDATE items
        SET report_id=?
        WHERE id=?
        """,
        (
            report_id,
            item_id
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("dashboard")
    )


# -----------------------------
# Found Item
# -----------------------------

@app.route(
    "/found",
    methods=["POST"]
)
@login_required
def found_item():

    item_name = request.form.get(
        "item_name",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    date = request.form.get(
        "date",
        ""
    ).strip()

    if not all([
        item_name,
        description,
        category,
        location,
        date
    ]):

        return redirect(
            url_for("home")
        )

    if not valid_date(date):

        return redirect(
            url_for("home")
        )

    image_filename = save_uploaded_image()

    conn = sqlite3.connect(
        "lost_found.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO items
        (
            item_type,
            item_name,
            description,
            category,
            location,
            date,
            image,
            user_id,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Found",
            item_name,
            description,
            category,
            location,
            date,
            image_filename,
            session["user_id"],
            "Open"
        )
    )

    item_id = cursor.lastrowid

    report_id = f"F{item_id:03d}"

    cursor.execute(
        """
        UPDATE items
        SET report_id=?
        WHERE id=?
        """,
        (
            report_id,
            item_id
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("dashboard")
    )


# -----------------------------
# Matches
# -----------------------------

@app.route("/matches")
def matches():

    search = normalize_text(
        request.args.get(
            "search",
            ""
        )
    )

    category = request.args.get(
        "category",
        ""
    )

    location = normalize_text(
        request.args.get(
            "location",
            ""
        )
    )

    conn = sqlite3.connect(
        "lost_found.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM items
        WHERE item_type='Lost'
        AND status != 'Returned'
        """
    )

    lost_items = cursor.fetchall()

    cursor.execute(
        """
        SELECT *
        FROM items
        WHERE item_type='Found'
        AND status != 'Returned'
        """
    )

    found_items = cursor.fetchall()

    conn.close()

    matches = []

    for lost in lost_items:

        for found in found_items:

            score = calculate_match_score(
                lost,
                found
            )

            if score < 50:

                continue

            if search:

                lost_name = normalize_text(
                    lost["item_name"]
                )

                found_name = normalize_text(
                    found["item_name"]
                )

                if (
                    search not in lost_name
                    and search not in found_name
                ):

                    continue

            if category:

                if lost["category"] != category:

                    continue

            if location:

                lost_location = normalize_text(
                    lost["location"]
                )

                found_location = normalize_text(
                    found["location"]
                )

                if (
                    location not in lost_location
                    and location not in found_location
                ):

                    continue

            details = calculate_match_details(
                lost,
                found
            )

            matches.append({

                "lost": lost,

                "found": found,

                "score": score,

                "label": match_label(score),

                "details": details

            })

    matches.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return render_template(
        "matches.html",
        matches=matches
    )


# -----------------------------
# Dashboard
# -----------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    conn = sqlite3.connect(
        "lost_found.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    user_id = session["user_id"]

    # Total lost
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM items
        WHERE item_type='Lost'
        AND user_id=?
        """,
        (user_id,)
    )

    total_lost = cursor.fetchone()[0]

    # Total found
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM items
        WHERE item_type='Found'
        AND user_id=?
        """,
        (user_id,)
    )

    total_found = cursor.fetchone()[0]

    # Open
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM items
        WHERE status='Open'
        AND user_id=?
        """,
        (user_id,)
    )

    total_open = cursor.fetchone()[0]

    # Matched
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM items
        WHERE status='Matched'
        AND user_id=?
        """,
        (user_id,)
    )

    total_matched = cursor.fetchone()[0]

    # Returned
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM items
        WHERE status='Returned'
        AND user_id=?
        """,
        (user_id,)
    )

    total_returned = cursor.fetchone()[0]

    # Recent lost
    cursor.execute(
        """
        SELECT *
        FROM items
        WHERE item_type='Lost'
        AND user_id=?
        ORDER BY id DESC
        LIMIT 5
        """,
        (user_id,)
    )

    recent_lost = cursor.fetchall()

    # Recent found
    cursor.execute(
        """
        SELECT *
        FROM items
        WHERE item_type='Found'
        AND user_id=?
        ORDER BY id DESC
        LIMIT 5
        """,
        (user_id,)
    )

    recent_found = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_lost=total_lost,
        total_found=total_found,
        total_open=total_open,
        total_matched=total_matched,
        total_returned=total_returned,
        recent_lost=recent_lost,
        recent_found=recent_found
    )


# -----------------------------
# Open Reports
# -----------------------------

@app.route("/open-reports")
def open_reports():

    category = request.args.get(
        "category",
        ""
    )

    location = normalize_text(
        request.args.get(
            "location",
            ""
        )
    )

    conn = sqlite3.connect(
        "lost_found.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    query = """
        SELECT *
        FROM items
        WHERE status='Open'
    """

    parameters = []

    if category:

        query += " AND category=?"

        parameters.append(
            category
        )

    if location:

        query += """
            AND LOWER(location) LIKE ?
        """

        parameters.append(
            "%" + location + "%"
        )

    query += """
        ORDER BY id DESC
    """

    cursor.execute(
        query,
        parameters
    )

    reports = cursor.fetchall()

    conn.close()

    return render_template(
        "open_reports.html",
        reports=reports
    )


# -----------------------------
# Update Status
# -----------------------------

@app.route(
    "/update-status/<int:item_id>",
    methods=["POST"]
)
@login_required
def update_status(item_id):

    status = request.form.get(
        "status",
        ""
    )

    allowed_statuses = {
        "Open",
        "Matched",
        "Returned"
    }

    if status not in allowed_statuses:

        return redirect(
            url_for("dashboard")
        )

    conn = sqlite3.connect(
        "lost_found.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE items
        SET status=?
        WHERE id=?
        AND user_id=?
        """,
        (
            status,
            item_id,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        request.referrer
        or url_for("dashboard")
    )


# -----------------------------
# Migrate Old Items
# -----------------------------

@app.route("/migrate-old-items")
@login_required
def migrate_old_items():

    conn = sqlite3.connect(
        "lost_found.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE items
        SET user_id=?
        WHERE user_id IS NULL
        """,
        (session["user_id"],)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("dashboard")
    )


# -----------------------------
# Run Application
# -----------------------------

if __name__ == "__main__":

    create_database()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
    