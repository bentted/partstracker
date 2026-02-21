import random
<<<<<<< Updated upstream
import json
=======
import sqlite3
from datetime import datetime
>>>>>>> Stashed changes

scrap_reasons = ["foreign material", "smear", "chip", "burn", "light", "heavy", "crack", "no fill"]
part_numbers = ["780208", "780508", "780108", "780308", "780608"]


def init_database():
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrap_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_number INTEGER NOT NULL,
            part_number TEXT NOT NULL,
            order_number INTEGER NOT NULL,
            scrap_reason TEXT NOT NULL,
            scrap_parts INTEGER NOT NULL,
            parts_made INTEGER NOT NULL,
            good_parts INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()


def save_scrap_data(operator_number, part_number, order_number, scrap_reason, scrap_parts, parts_made, good_parts):
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO scrap_data 
        (operator_number, part_number, order_number, scrap_reason, scrap_parts, parts_made, good_parts, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (operator_number, part_number, order_number, scrap_reason, scrap_parts, parts_made, good_parts, timestamp))
    
    conn.commit()
    conn.close()
    print("Scrap data saved to database.")


class Part:
    expected_rate = 248

    def __init__(self, part_number):
        self.part_number = part_number

    def rate_percentage(self, made_parts):
        if self.expected_rate <= 0:
            return 0.0
        return (made_parts / self.expected_rate) * 100


class Order:
    _next_order_number = 1
    orders_data_file = "orders_data.json"

    def __init__(self, part_number):
        self.order_number = Order._next_order_number
        Order._next_order_number += 1
        self.part_number = part_number
        self.parts_per_order = random.randint(100, 5000)
        self.parts_made = 0
        self.scrap_made = 0

    def update_order(self, good_parts, scrap_parts):
        self.parts_made += good_parts
        self.scrap_made += scrap_parts

    def parts_remaining(self):
        return self.parts_per_order - self.parts_made - self.scrap_made

    def summary(self):
        return (
            f"Order {self.order_number}: Part {self.part_number}, Parts per order: {self.parts_per_order}, "
            f"Parts made: {self.parts_made}, Scrap made: {self.scrap_made}, Parts remaining: {self.parts_remaining()}"
        )

    @staticmethod
    def save_orders(orders):
        with open(Order.orders_data_file, "w") as file:
            json.dump([order.__dict__ for order in orders], file)

    @staticmethod
    def load_orders():
        try:
            with open(Order.orders_data_file, "r") as file:
                orders_data = json.load(file)
                orders = []
                for data in orders_data:
                    order = Order(data["part_number"])
                    order.order_number = data["order_number"]
                    order.parts_per_order = data["parts_per_order"]
                    order.parts_made = data["parts_made"]
                    order.scrap_made = data["scrap_made"]
                    orders.append(order)
                Order._next_order_number = max(order.order_number for order in orders) + 1
                return orders
        except FileNotFoundError:
            return []


def part_selection():
    while True:
        part_number = input("Enter part number: ")
        if part_number in part_numbers:
            break
        print("Invalid part number. Please enter a valid part number from the list: " + ", ".join(part_numbers))

    mix = input("Enter mix number: ")
    part_number = part_number + mix
    order_quantity = random.randint(110, 5000)
    print("Part number: " + part_number + ", Order quantity: " + str(order_quantity) + " (randomly generated)")
    
    while True:
        try:
<<<<<<< Updated upstream
            numparts = int(input("Enter number of parts made: "))
            if numparts < 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid non-negative integer for number of parts made.")
    print("Part number: " + part_number + ", Number of parts made: " + str(numparts))
    return part_number, numparts
=======
            parts_made = int(input("Enter number of parts you have made: "))
            if parts_made < 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid non-negative integer for parts made.")
    
    return part_number, order_quantity, parts_made
>>>>>>> Stashed changes


def scrap_reason(order_quantity, parts_made, part_number, order_number):
    while True:
        try:
            operator_number = int(input("Enter operator number (max 4 digits): "))
            if operator_number < 0 or operator_number > 9999:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid 4-digit integer (0-9999).")
    
    while True:
        reason = input("Enter scrap reason: ")
        if reason in scrap_reasons:
            break
        print("Invalid scrap reason. Please enter a valid reason from the list: " + ", ".join(scrap_reasons))

    while True:
        try:
            scrap_parts = int(input("Enter number of scrap parts: "))
            if scrap_parts < 0 or scrap_parts > parts_made:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid number between 0 and " + str(parts_made) + ".")

<<<<<<< Updated upstream
    good_parts = numparts - scrap_parts
    print("Total good parts: " + str(good_parts))
    return good_parts, scrap_parts


def main():
    orders = Order.load_orders()

    selected_part_number, _ = part_selection()
    order = Order(selected_part_number)
    orders.append(order)
    print(order.summary())

    while order.parts_remaining() > 0:
        print(f"Total parts to be made: {order.parts_per_order}")
        good_parts, scrap_parts = scrap_reason(order.parts_remaining())
        order.update_order(good_parts, scrap_parts)
        print(f"Parts remaining: {order.parts_remaining()}")

    Order.save_orders(orders)
    print("Order data saved.")


if __name__ == "__main__":
    main()
=======
    good_parts_made = parts_made - scrap_parts
    remaining_parts = order_quantity - good_parts_made
    
    # Save scrap data to database
    save_scrap_data(operator_number, part_number, order_number, reason, scrap_parts, parts_made, good_parts_made)
    
    print("Good parts made: " + str(good_parts_made))
    print("Remaining parts to complete order: " + str(remaining_parts))
    
    return good_parts_made, remaining_parts


# Initialize database
init_database()

selected_part_number, order_quantity, parts_made = part_selection()
order = Order(selected_part_number, order_quantity)
print(order.summary())
good_parts, remaining_parts = scrap_reason(order_quantity, parts_made, selected_part_number, order.order_number)
part = Part(selected_part_number)
rate_percentage = part.rate_percentage(good_parts)
print("Rate made: " + f"{rate_percentage:.1f}" + "% of expected " + str(part.expected_rate))
>>>>>>> Stashed changes
