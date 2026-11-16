from functools import wraps
from flask import session, flash, redirect, url_for


class Flower(dict):
    def __init__(self, product):
        super().__init__(product)
        self.category = "flower"


class Bouquet(dict):
    def __init__(self, product):
        super().__init__(product)
        self.category = "bouquet"


class ProductFactory:
    @staticmethod
    def create_product(product):
        product_type = product.get("product_type")

        if product_type == "flower":
            return Flower(product)

        elif product_type == "bouquet":
            return Bouquet(product)

        raise ValueError("Invalid product type.")



def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view    



class OrderStatusObserver:
    def update(self, order_id, new_status):
        pass


class OrderStatusLogger(OrderStatusObserver):
    def update(self, order_id, new_status):
        print(
            f"Order #{order_id} status changed to: {new_status}"
        )


class OrderStatusSubject:
    def __init__(self):
        self.observers = []

    def attach(self, observer):
        self.observers.append(observer)

    def notify(self, order_id, new_status):
        for observer in self.observers:
            observer.update(order_id, new_status)


# Create subject and register observer
order_status_subject = OrderStatusSubject()
order_status_subject.attach(OrderStatusLogger())