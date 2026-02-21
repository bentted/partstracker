import random
import json

scrap_reasons = ["foreign material", "smear", "chip", "burn", "light", "heavy", "crack", "no fill"]
part_numbers = ["780208", "780508", "780108", "780308", "780608"]


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
    while True:
        try:
            numparts = int(input("Enter number of parts made: "))
            if numparts < 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid non-negative integer for number of parts made.")
    print("Part number: " + part_number + ", Number of parts made: " + str(numparts))
    return part_number, numparts


def scrap_reason(numparts):
    while True:
        reason = input("Enter scrap reason: ")
        if reason in scrap_reasons:
            break
        print("Invalid scrap reason. Please enter a valid reason from the list: " + ", ".join(scrap_reasons))

    while True:
        try:
            scrap_parts = int(input("Enter number of scrap parts: "))
            if scrap_parts < 0 or scrap_parts > numparts:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid number between 0 and " + str(numparts) + ".")

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