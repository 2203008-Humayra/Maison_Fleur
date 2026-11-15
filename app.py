from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db_connection

from flask import jsonify
from database.cart import (
    add_to_cart,
    get_cart_items,
    update_cart_quantity,
    remove_from_cart
)

# =====================================
# FLASK CONFIGURATION
# =====================================

app = Flask(__name__)

app.secret_key = "maison-fleur-development-key"


# =====================================
# DATABASE CONNECTION
# =====================================

def get_db_connection():

    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="maison_fleur"
        )

        return connection

    except Error as e:
        print("Database connection failed:", e)
        return None


# =====================================
# HOME PAGE
# =====================================

@app.route("/")
def home():
    return render_template("home.html")


# =====================================
# CATALOG PAGE
# =====================================

@app.route("/catalog")
def catalog():
    return render_template("catalog.html")


@app.route("/basket")
def basket():
    if "user_id" not in session:
        flash("Please sign in to view your basket.", "error")
        return redirect(url_for("login"))

    return render_template("basket.html")


# =====================================
# GET CUSTOMER BASKET
# =====================================

@app.route("/api/cart", methods=["GET"])
def api_get_cart():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    items = get_cart_items(session["user_id"])

    if items is None:
        return jsonify({
            "success": False,
            "message": "Unable to load basket."
        }), 500

    return jsonify({
        "success": True,
        "items": items
    })


# =====================================
# ADD PRODUCT TO BASKET
# =====================================

@app.route("/api/cart", methods=["POST"])
def api_add_to_cart():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid product information."
        }), 400

    name = data.get("name")
    image = data.get("image")
    product_type = data.get("type")

    try:
        price = float(data.get("price"))
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid price or quantity."
        }), 400

    if (
        not isinstance(name, str) or not name.strip()
        or not isinstance(image, str) or not image.strip()
        or product_type not in ["flower", "bouquet"]
        or price <= 0
        or quantity < 1
    ):
        return jsonify({
            "success": False,
            "message": "Invalid product information."
        }), 400

    product = {
        "name": name.strip(),
        "image": image.strip(),
        "price": price,
        "quantity": quantity,
        "type": product_type
    }

    success = add_to_cart(session["user_id"], product)

    if not success:
        return jsonify({
            "success": False,
            "message": "Unable to add product."
        }), 500

    return jsonify({
        "success": True,
        "message": "Product added to basket."
    })


# =====================================
# UPDATE BASKET QUANTITY
# =====================================

@app.route("/api/cart/<int:item_id>", methods=["PUT"])
def api_update_cart(item_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400

    try:
        quantity = int(data.get("quantity"))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid quantity."
        }), 400

    if quantity < 0:
        return jsonify({
            "success": False,
            "message": "Invalid quantity."
        }), 400

    success = update_cart_quantity(
        session["user_id"],
        item_id,
        quantity
    )

    if not success:
        return jsonify({
            "success": False,
            "message": "Unable to update basket."
        }), 400

    return jsonify({
        "success": True,
        "message": "Basket updated."
    })


# =====================================
# REMOVE PRODUCT FROM BASKET
# =====================================

@app.route("/api/cart/<int:item_id>", methods=["DELETE"])
def api_remove_from_cart(item_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    success = remove_from_cart(
        session["user_id"],
        item_id
    )

    if not success:
        return jsonify({
            "success": False,
            "message": "Unable to remove product."
        }), 400

    return jsonify({
        "success": True,
        "message": "Product removed."
    })



# =====================================
# LOGIN PAGE
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        flash("You are already logged in!", "success")
        return redirect(url_for("profile"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "error")
            return render_template("login.html")

        connection = get_db_connection()

        if connection is None:
            flash("Unable to connect to the database.", "error")
            return render_template("login.html")

        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):

                session.clear()

                session["user_id"] = user["id"]
                session["user_name"] = user["fullname"]
                session["user_email"] = user["email"]

                flash("Login successful!", "success")

                return redirect(url_for("profile"))

            else:
                flash("Invalid email or password.", "error")

        except Error as e:

            print("Login error:", e)
            flash("Something went wrong. Please try again.", "error")

        finally:

            cursor.close()
            connection.close()

    return render_template("login.html")


@app.route("/profile")
def profile():
    if "user_id" not in session:
        flash("Please sign in to access your profile.", "error")
        return redirect(url_for("login"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("home"))

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT fullname, email, phone FROM users WHERE id = %s",
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if user is None:
            session.clear()
            flash("Please sign in again.", "error")
            return redirect(url_for("login"))

        return render_template("profile.html", user=user)

    except Error as e:
        print("Profile error:", e)
        flash("Unable to load your profile.", "error")
        return redirect(url_for("home"))

    finally:
        cursor.close()
        connection.close()



@app.route("/logout")
def logout():
    session.clear()
    flash("You have signed out successfully.", "success")
    return redirect(url_for("home"))



# =====================================
# SIGNUP PAGE
# =====================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Check empty fields
        if not all([fullname, email, phone, password, confirm_password]):
            flash("Please fill in all the fields.", "error")
            return render_template("signup.html")

        # Check password length
        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return render_template("signup.html")

        # Check password confirmation
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        connection = get_db_connection()

        if connection is None:
            flash("Unable to connect to the database.", "error")
            return render_template("signup.html")

        cursor = connection.cursor()

        try:

            # Check whether email already exists
            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )

            existing_user = cursor.fetchone()

            if existing_user:
                flash("An account with this email already exists.", "error")
                return render_template("signup.html")

            # Hash password
            password_hash = generate_password_hash(password)

            # Save customer information
            cursor.execute(
                """
                INSERT INTO users
                (fullname, email, phone, password_hash)
                VALUES (%s, %s, %s, %s)
                """,
                (fullname, email, phone, password_hash)
            )

            connection.commit()

            flash("Your account has been created successfully! Please sign in.", "success")

            return redirect(url_for("login"))

        except Error as e:

            connection.rollback()
            print("Registration error:", e)

            flash("Something went wrong. Please try again.", "error")

            return render_template("signup.html")

        finally:

            cursor.close()
            connection.close()

    return render_template("signup.html")


# =====================================
# TEST DATABASE CONNECTION
# =====================================

@app.route("/test-db")
def test_db():

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed!"

    connection.close()

    return "Maison Fleur database connected successfully!"


# =====================================
# RUN APPLICATION
# =====================================

if __name__ == "__main__":
    app.run(debug=True)