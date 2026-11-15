from database.db import get_db_connection
from mysql.connector import Error


# =====================================
# ADD PRODUCT TO CART
# =====================================

def add_to_cart(user_id, product):

    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO cart_items
            (
                user_id,
                product_name,
                product_image,
                product_price,
                product_quantity,
                product_type
            )
            VALUES (%s, %s, %s, %s, %s, %s)

            ON DUPLICATE KEY UPDATE
            product_quantity = product_quantity + VALUES(product_quantity)
            """,
            (
                user_id,
                product["name"],
                product["image"],
                product["price"],
                product["quantity"],
                product["type"]
            )
        )

        connection.commit()
        return True

    except (Error, KeyError, ValueError, TypeError) as e:
        connection.rollback()
        print("Add to cart error:", e)
        return False

    finally:
        cursor.close()
        connection.close()


# =====================================
# GET CUSTOMER CART
# =====================================

def get_cart_items(user_id):

    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                product_name,
                product_image,
                product_price,
                product_quantity,
                product_type
            FROM cart_items
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (user_id,)
        )

        return cursor.fetchall()

    except Error as e:
        print("Get cart error:", e)
        return None

    finally:
        cursor.close()
        connection.close()


# =====================================
# UPDATE PRODUCT QUANTITY
# =====================================

def update_cart_quantity(user_id, item_id, quantity):

    if quantity <= 0:
        return remove_from_cart(user_id, item_id)

    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE cart_items
            SET product_quantity = %s
            WHERE id = %s AND user_id = %s
            """,
            (quantity, item_id, user_id)
        )

        connection.commit()
        return cursor.rowcount > 0

    except Error as e:
        connection.rollback()
        print("Update cart error:", e)
        return False

    finally:
        cursor.close()
        connection.close()


# =====================================
# REMOVE PRODUCT FROM CART
# =====================================

def remove_from_cart(user_id, item_id):

    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM cart_items
            WHERE id = %s AND user_id = %s
            """,
            (item_id, user_id)
        )

        connection.commit()
        return cursor.rowcount > 0

    except Error as e:
        connection.rollback()
        print("Remove cart error:", e)
        return False

    finally:
        cursor.close()
        connection.close()