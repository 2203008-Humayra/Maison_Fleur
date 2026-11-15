from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db_connection
from database.cart import get_cart_items
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo



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
# OFFICIAL PRODUCT PRICES
# =====================================

PRODUCT_PRICES = {

    # INDIVIDUAL FLOWERS

    "White Iris": 135,
    "Blue Cornflower": 115,
    "Red Carnation": 140,
    "White Carnation": 140,
    "Pink Carnation": 140,
    "Orange Gerbera": 95,
    "Yellow Gerbera": 95,
    "Red Gerbera": 95,
    "Pink Gerbera": 95,
    "Red Dahlia": 170,
    "White Dahlia": 170,
    "Pink Dahlia": 170,
    "Sunflower": 200,
    "White Lily": 425,
    "Pink Lily": 425,
    "Purple Tulip": 350,
    "Yellow Tulip": 350,
    "Red Tulip": 350,
    "White Tulip": 350,
    "Pink Tulip": 350,
    "White Peony": 650,
    "Pink Peony": 650,
    "White Orchid": 230,
    "Purple Orchid": 230,
    "Gypsophila": 270,
    "Red Rose": 150,
    "Pink Rose": 150,
    "Magenta Rose": 150,
    "Blue Rose": 150,
    "White Rose": 150,
    "Yellow Rose": 150,

    # SIGNATURE BOUQUETS

    "Rosewood & Berry": 4500,
    "Autumn Edition": 2600,
    "Scarlet Column": 4200,
    "Morning Mist": 2650,
    "Sorbet Swirl": 1700,
    "Solstice": 2000,
    "Othello": 3500,
    "Ballet Slippers": 10500,
    "Midnight Sun": 1700,
    "Porcelin & Dew": 5300,
    "Sacred Vow": 11000,
    "Linen & Bloom": 2500,
    "Wisteria Shadow": 5000,
    "Sage & Serif": 2275,
    "Eclipse": 1275,
    "Rosette": 10300,
    "Monochrome Plum": 4500,
    "Duskfall": 3400,
    "Velvet Dusk": 3575
}


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

    connection = get_db_connection()

    if connection is None:
        flash("Unable to load the product catalog.", "error")
        return redirect(url_for("home"))

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        # GET INDIVIDUAL FLOWERS
        cursor.execute("""
            SELECT id, name, image, price
            FROM products
            WHERE product_type = 'flower'
            AND is_active = 1
            ORDER BY id ASC
        """)

        flowers = cursor.fetchall()
        for flower in flowers:
            flower["price"] = float(flower["price"])

        # GET SIGNATURE BOUQUETS
        cursor.execute("""
            SELECT id, name, image, price
            FROM products
            WHERE product_type = 'bouquet'
            AND is_active = 1
            ORDER BY id ASC
        """)

        bouquets = cursor.fetchall()
        for bouquet in bouquets:
            bouquet["price"] = float(bouquet["price"])

        return render_template(
            "catalog.html",
            flowers=flowers,
            bouquets=bouquets
        )

    except Error as e:
        print("Catalog Loading Error:", e)
        flash("Unable to load the product catalog.", "error")
        return redirect(url_for("home"))

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


@app.route("/basket")
def basket():
    if "user_id" not in session:
        flash("Please sign in to view your basket.", "error")
        return redirect(url_for("login"))

    return render_template("basket.html")


# =====================================
# CHECKOUT PAGE
# =====================================

@app.route("/checkout")
def checkout():

    # Check login status
    if "user_id" not in session:
        flash("Please sign in before proceeding to checkout.", "error")
        return redirect(url_for("login"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("basket"))

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        # Get customer information
        cursor.execute(
            """
            SELECT fullname, email, phone
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if user is None:
            session.clear()
            flash("Please sign in again.", "error")
            return redirect(url_for("login"))

        # Get basket items
        cart_items = get_cart_items(session["user_id"])

        if cart_items is None:
            flash("Unable to load your basket.", "error")
            return redirect(url_for("basket"))

        if len(cart_items) == 0:
            flash("Your basket is empty.", "error")
            return redirect(url_for("basket"))

        # Calculate subtotal
        subtotal = sum(
            float(item["product_price"]) * int(item["product_quantity"])
            for item in cart_items
        )

        # Delivery fee (currently free)
        delivery_fee = 0.00

        total_amount = subtotal + delivery_fee

        return render_template(
            "checkout.html",
            user=user,
            cart_items=cart_items,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total_amount
        )

    except Exception as e:
        print("Checkout Error:", e)
        flash("Something went wrong while loading checkout.", "error")
        return redirect(url_for("basket"))

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()

# =====================================
# PLACE CUSTOMER ORDER
# =====================================

@app.route("/place-order", methods=["POST"])
def place_order():

    if "user_id" not in session:
        flash("Please sign in before placing an order.", "error")
        return redirect(url_for("login"))

    fullname = request.form.get("fullname", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    delivery_address = request.form.get("delivery_address", "").strip()
    delivery_notes = request.form.get("delivery_notes", "").strip()
    payment_method = request.form.get("payment_method", "").strip()

    if not all([fullname, email, phone, delivery_address]):
        flash("Please complete all required delivery information.", "error")
        return redirect(url_for("checkout"))

    if payment_method != "Cash on Delivery":
        flash("Invalid payment method.", "error")
        return redirect(url_for("checkout"))

    # =====================================
    # CALCULATE ESTIMATED DELIVERY
    # =====================================

    dhaka_timezone = ZoneInfo("Asia/Dhaka")
    current_time = datetime.now(dhaka_timezone)

    if 9 <= current_time.hour < 19:

        # Orders between 9 AM and 7 PM
        estimated_delivery = current_time + timedelta(hours=3)

    elif current_time.hour >= 19:

        # Orders from 7 PM onward
        estimated_delivery = (
            current_time + timedelta(days=1)
        ).replace(hour=9, minute=0, second=0, microsecond=0)

    else:

        # Orders before 9 AM
        estimated_delivery = current_time.replace(
            hour=9,
            minute=0,
            second=0,
            microsecond=0
        )

    # MySQL DATETIME stores the local time without timezone information.
    estimated_delivery = estimated_delivery.replace(tzinfo=None)
    print("DELIVERY ESTIMATE:", estimated_delivery)

    # =====================================
    # DATABASE CONNECTION
    # =====================================

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("checkout"))

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM cart_items
            WHERE user_id = %s
            FOR UPDATE
            """,
            (session["user_id"],)
        )

        cart_items = cursor.fetchall()

        if not cart_items:
            flash("Your basket is empty.", "error")
            return redirect(url_for("basket"))

        subtotal = 0
        validated_items = []

        for item in cart_items:

            product_name = item["product_name"]
            product_type = item["product_type"]
            quantity = int(item["product_quantity"])

            if product_name not in PRODUCT_PRICES:
                raise ValueError("Invalid product in basket.")

            if product_type not in ["flower", "bouquet"]:
                raise ValueError("Invalid product category.")

            if quantity < 1:
                raise ValueError("Invalid product quantity.")

            official_price = PRODUCT_PRICES[product_name]

            subtotal += official_price * quantity

            validated_items.append({
                "name": product_name,
                "image": item["product_image"],
                "price": official_price,
                "quantity": quantity,
                "type": product_type
            })

        delivery_fee = 0
        total_amount = subtotal + delivery_fee

        # =====================================
        # INSERT ORDER
        # =====================================

        cursor.execute(
            """
            INSERT INTO orders
            (
                user_id,
                fullname,
                email,
                phone,
                delivery_address,
                delivery_notes,
                subtotal,
                delivery_fee,
                total_amount,
                order_status,
                estimated_delivery
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                fullname,
                email,
                phone,
                delivery_address,
                delivery_notes,
                subtotal,
                delivery_fee,
                total_amount,
                "Pending",
                estimated_delivery
            )
        )

        order_id = cursor.lastrowid
        print("ORDER INSERTED:", order_id)
        print("SAVED DELIVERY ESTIMATE:", estimated_delivery)

        # =====================================
        # INSERT ORDER ITEMS
        # =====================================

        for item in validated_items:

            cursor.execute(
                """
                INSERT INTO order_items
                (
                    order_id,
                    product_name,
                    product_image,
                    product_price,
                    product_quantity,
                    product_type
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    item["name"],
                    item["image"],
                    item["price"],
                    item["quantity"],
                    item["type"]
                )
            )

        # =====================================
        # CLEAR BASKET
        # =====================================

        cursor.execute(
            "DELETE FROM cart_items WHERE user_id = %s",
            (session["user_id"],)
        )

        connection.commit()

        flash("Your order has been placed successfully!", "success")

        return redirect(
            url_for("order_confirmation", order_id=order_id)
        )

    except (Error, ValueError, KeyError, TypeError) as e:

        connection.rollback()

        print("Place Order Error:", e)

        flash("Unable to place your order. Please try again.", "error")

        return redirect(url_for("checkout"))

    finally:

        if cursor is not None:
            cursor.close()

        connection.close()

# =====================================
# ORDER CONFIRMATION
# =====================================

@app.route("/order-confirmation/<int:order_id>")
def order_confirmation(order_id):

    if "user_id" not in session:
        flash("Please sign in to view your order.", "error")
        return redirect(url_for("login"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("home"))

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        # Get customer's order
        cursor.execute(
            """
            SELECT *
            FROM orders
            WHERE id = %s AND user_id = %s
            """,
            (order_id, session["user_id"])
        )

        order = cursor.fetchone()

        if order is None:
            flash("Order not found.", "error")
            return redirect(url_for("profile"))

        # Get ordered products
        cursor.execute(
            """
            SELECT *
            FROM order_items
            WHERE order_id = %s
            """,
            (order_id,)
        )

        order_items = cursor.fetchall()

        return render_template(
            "order_confirmation.html",
            order=order,
            order_items=order_items
        )

    except Error as e:

        print("Order Confirmation Error:", e)

        flash("Unable to load order confirmation.", "error")

        return redirect(url_for("profile"))

    finally:

        if cursor is not None:
            cursor.close()

        connection.close()



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


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if "admin_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "error")
            return render_template("admin_login.html")

        connection = get_db_connection()

        if connection is None:
            flash("Unable to connect to the database.", "error")
            return render_template("admin_login.html")

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM admins WHERE email = %s",
                (email,)
            )

            admin = cursor.fetchone()

            if admin and check_password_hash(
                admin["password_hash"], password
            ):

                session.clear()

                session["admin_id"] = admin["id"]
                session["admin_name"] = admin["fullname"]
                session["admin_email"] = admin["email"]

                flash("Admin login successful!", "success")

                return redirect(url_for("admin_dashboard"))

            else:
                flash("Invalid email or password.", "error")

        except Error as e:
            print("Admin login error:", e)
            flash("Something went wrong. Please try again.", "error")

        finally:
            if cursor is not None:
                cursor.close()

            connection.close()

    return render_template("admin_login.html")


@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        flash("Please log in as an administrator.", "error")
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("admin_login"))

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        # ALL ORDERS
        cursor.execute("""
            SELECT *
            FROM orders
            ORDER BY created_at DESC
        """)

        orders = cursor.fetchall()

        # STATISTICS
        cursor.execute("SELECT COUNT(*) AS total FROM orders")
        total_orders = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM orders
            WHERE order_status = 'Pending'
        """)
        pending_orders = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_customers = cursor.fetchone()["total"]

        # ALL PRODUCTS
        cursor.execute("""
            SELECT *
            FROM products
            ORDER BY product_type ASC, id DESC
        """)

        products = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM products
            WHERE is_active = 1
        """)
        active_products = cursor.fetchone()["total"]

        return render_template(
            "admin_dashboard.html",
            orders=orders,
            total_orders=total_orders,
            pending_orders=pending_orders,
            total_customers=total_customers,
            products=products,
            active_products=active_products
        )

    except Error as e:
        print("Admin Dashboard Error:", e)
        flash("Unable to load the admin dashboard.", "error")
        return redirect(url_for("admin_login"))

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()

@app.route("/admin-logout")
def admin_logout():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    session.clear()

    flash("You have been logged out successfully.", "success")

    return redirect(url_for("admin_login"))       


@app.route("/admin-update-order-status/<int:order_id>", methods=["POST"])
def admin_update_order_status(order_id):

    if "admin_id" not in session:
        flash("Please log in as an administrator.", "error")
        return redirect(url_for("admin_login"))

    new_status = request.form.get("order_status", "").strip()

    allowed_statuses = [
        "Pending",
        "Processing",
        "Shipped",
        "Delivered",
        "Cancelled"
    ]

    if new_status not in allowed_statuses:
        flash("Invalid order status.", "error")
        return redirect(url_for("admin_dashboard"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("admin_dashboard"))

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE orders
            SET order_status = %s
            WHERE id = %s
            """,
            (new_status, order_id)
        )

        if cursor.rowcount == 0:
            flash("Order not found or status unchanged.", "error")
        else:
            connection.commit()
            flash(
                f"Order #{order_id} status updated to {new_status}.",
                "success"
            )

    except Error as e:
        connection.rollback()
        print("Order Status Update Error:", e)
        flash("Unable to update order status.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()

    return redirect(url_for("admin_dashboard"))



@app.route("/admin-order-details/<int:order_id>")
def admin_order_details(order_id):

    if "admin_id" not in session:
        flash("Please log in as an administrator.", "error")
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("admin_dashboard"))

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM orders WHERE id = %s",
            (order_id,)
        )

        order_details = cursor.fetchone()

        if order_details is None:
            flash("Order not found.", "error")
            return redirect(url_for("admin_dashboard"))

        cursor.execute(
            "SELECT * FROM order_items WHERE order_id = %s",
            (order_id,)
        )

        order_items = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM orders
            ORDER BY created_at DESC
        """)

        orders = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) AS total FROM orders")
        total_orders = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM orders
            WHERE order_status = 'Pending'
        """)

        pending_orders = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_customers = cursor.fetchone()["total"]

        # PRODUCTS
        cursor.execute("""
            SELECT *
            FROM products
            ORDER BY product_type ASC, id DESC
        """)

        products = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM products
            WHERE is_active = 1
        """)

        active_products = cursor.fetchone()["total"]

        return render_template(
            "admin_dashboard.html",
            orders=orders,
            total_orders=total_orders,
            pending_orders=pending_orders,
            total_customers=total_customers,
            products=products,
            active_products=active_products,
            order_details=order_details,
            order_items=order_items
        )

    except Error as e:
        print("Order Details Error:", e)
        flash("Unable to load order details.", "error")
        return redirect(url_for("admin_dashboard"))

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


@app.route("/admin-add-product", methods=["POST"])
def admin_add_product():

    if "admin_id" not in session:
        flash("Please log in as an administrator.", "error")
        return redirect(url_for("admin_login"))

    name = request.form.get("name", "").strip()
    image = request.form.get("image", "").strip()
    price = request.form.get("price", "").strip()
    product_type = request.form.get("product_type", "").strip()

    if not name or not image or not price:
        flash("Please complete all product fields.", "error")
        return redirect(url_for("admin_dashboard") + "#products")

    if product_type not in ["flower", "bouquet"]:
        flash("Invalid product type.", "error")
        return redirect(url_for("admin_dashboard") + "#products")

    # Only accept a filename, not a directory path.
    if image != image.split("/")[-1] or image != image.split("\\")[-1]:
        flash("Please enter only the image filename.", "error")
        return redirect(url_for("admin_dashboard") + "#products")

    if not image.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        flash("Unsupported image format.", "error")
        return redirect(url_for("admin_dashboard") + "#products")

    try:
        price = float(price)

        if price <= 0:
            raise ValueError

    except ValueError:
        flash("Please enter a valid positive price.", "error")
        return redirect(url_for("admin_dashboard") + "#products")

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("admin_dashboard"))

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO products
            (name, image, price, product_type, is_active)
            VALUES (%s, %s, %s, %s, 1)
        """, (name, image, price, product_type))

        connection.commit()

        flash("Product added successfully.", "success")

    except Error as e:
        connection.rollback()
        print("Add Product Error:", e)
        flash("Unable to add the product.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()

    return redirect(url_for("admin_dashboard") + "#products")        


@app.route("/admin-update-product/<int:product_id>", methods=["POST"])
def admin_update_product(product_id):

    if "admin_id" not in session:
        flash("Please log in as an administrator.", "error")
        return redirect(url_for("admin_login"))

    name = request.form.get("name", "").strip()
    image = request.form.get("image", "").strip()
    price = request.form.get("price", "").strip()

    if not name or not image or not price:
        flash("Please complete all product fields.", "error")
        return redirect(url_for("admin_dashboard") + "#products")

    if image != image.split("/")[-1] or image != image.split("\\")[-1]:
        flash("Please enter only the image filename.", "error")
        return redirect(url_for("admin_dashboard") + "#products")

    if not image.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        flash("Unsupported image format.", "error")
        return redirect(url_for("admin_dashboard") + "#products")

    try:
        price = float(price)

        if price <= 0:
            raise ValueError

    except ValueError:
        flash("Please enter a valid positive price.", "error")
        return redirect(url_for("admin_dashboard") + "#products")

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("admin_dashboard"))

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE products
            SET name = %s,
                image = %s,
                price = %s
            WHERE id = %s
        """, (name, image, price, product_id))

        if cursor.rowcount == 0:
            flash("Product not found or no changes were made.", "error")
        else:
            connection.commit()
            flash("Product updated successfully.", "success")

    except Error as e:
        connection.rollback()
        print("Update Product Error:", e)
        flash("Unable to update the product.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()

    return redirect(url_for("admin_dashboard") + "#products")



@app.route("/admin-toggle-product/<int:product_id>", methods=["POST"])
def admin_toggle_product(product_id):

    if "admin_id" not in session:
        flash("Please log in as an administrator.", "error")
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("admin_dashboard"))

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT is_active
            FROM products
            WHERE id = %s
        """, (product_id,))

        product = cursor.fetchone()

        if product is None:
            flash("Product not found.", "error")
        else:
            new_status = 0 if product["is_active"] else 1

            cursor.execute("""
                UPDATE products
                SET is_active = %s
                WHERE id = %s
            """, (new_status, product_id))

            connection.commit()

            if new_status:
                flash("Product restored successfully.", "success")
            else:
                flash("Product hidden successfully.", "success")

    except Error as e:
        connection.rollback()
        print("Toggle Product Error:", e)
        flash("Unable to change product visibility.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()

    return redirect(url_for("admin_dashboard") + "#products")


@app.route("/profile")
def profile():

    if "user_id" not in session:
        flash("Please sign in to access your profile.", "error")
        return redirect(url_for("login"))

    connection = get_db_connection()

    if connection is None:
        flash("Unable to connect to the database.", "error")
        return redirect(url_for("home"))

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        # GET USER INFORMATION
        cursor.execute(
            """
            SELECT fullname, email, phone
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if user is None:
            session.clear()
            flash("Please sign in again.", "error")
            return redirect(url_for("login"))

        # GET CUSTOMER ORDERS
        cursor.execute(
            """
            SELECT
                id,
                created_at,
                total_amount,
                order_status,
                estimated_delivery
            FROM orders
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        )

        orders = cursor.fetchall()

        # GET PRODUCTS FOR EACH ORDER
        for order in orders:

            cursor.execute(
                """
                SELECT
                    product_name,
                    product_image,
                    product_price,
                    product_quantity,
                    product_type
                FROM order_items
                WHERE order_id = %s
                """,
                (order["id"],)
            )

            order["items"] = cursor.fetchall()

        return render_template(
            "profile.html",
            user=user,
            orders=orders
        )

    except Error as e:

        print("Profile error:", e)

        flash("Unable to load your profile.", "error")
        return redirect(url_for("home"))

    finally:

        if cursor is not None:
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