import random
import sqlite3
from datetime import datetime

scrap_reasons = ["foreign material", "smear", "chip", "burn", "light", "heavy", "crack", "no fill"]
part_numbers = ["780208", "780508", "780108", "780308", "780608"]


def init_database():
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrap_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_number INTEGER NOT NULL,
            part_number TEXT NOT NULL,
            order_number INTEGER NOT NULL,
            scrap_reason TEXT NOT NULL,
            scrap_count INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()


def save_scrap_entry(operator_number, part_number, order_number, scrap_reason, scrap_count):
    conn = sqlite3.connect('parts_tracker.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO scrap_entries 
        (operator_number, part_number, order_number, scrap_reason, scrap_count, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (operator_number, part_number, order_number, scrap_reason, scrap_count, timestamp))
    
    conn.commit()
    conn.close()
    print(f"Scrap entry saved: {scrap_count} parts for reason '{scrap_reason}'")


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

    def __init__(self, part_number, parts_per_order):
        self.order_number = Order._next_order_number
        Order._next_order_number += 1
        self.part_number = part_number
        self.parts_per_order = parts_per_order

    def summary(self):
        return (
            "Order "
            + str(self.order_number)
            + ": Part "
            + self.part_number
            + ", Parts per order: "
            + str(self.parts_per_order)
        )


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
            parts_made = int(input("Enter number of parts you have made: "))
            if parts_made < 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid non-negative integer for parts made.")
    
    return part_number, order_quantity, parts_made


def scrap_tracking(parts_made, part_number, order_number):
    while True:
        try:
            operator_number = int(input("Enter operator number (max 4 digits): "))
            if operator_number < 0 or operator_number > 9999:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid 4-digit integer (0-9999).")
    
    total_scrap = 0
    scrap_details = []
    
    print(f"\nTracking scrap for {parts_made} parts made")
    print("Enter each scrap reason and count. Enter 'done' when finished.")
    
    while True:
        reason_input = input("\nEnter scrap reason (or 'done' to finish): ").strip()
        
        if reason_input.lower() == 'done':
            break
            
        if reason_input not in scrap_reasons:
            print("Invalid scrap reason. Please enter a valid reason from the list: " + ", ".join(scrap_reasons))
            continue
        
        while True:
            try:
                scrap_count = int(input(f"Enter number of parts scrapped for '{reason_input}': "))
                if scrap_count < 0:
                    raise ValueError
                if total_scrap + scrap_count > parts_made:
                    print(f"Total scrap ({total_scrap + scrap_count}) cannot exceed parts made ({parts_made})")
                    continue
                break
            except ValueError:
                print("Please enter a valid non-negative integer.")
        
        if scrap_count > 0:
            total_scrap += scrap_count
            scrap_details.append((reason_input, scrap_count))
            save_scrap_entry(operator_number, part_number, order_number, reason_input, scrap_count)
            print(f"Recorded: {scrap_count} parts for '{reason_input}'. Total scrap so far: {total_scrap}")
    
    good_parts_made = parts_made - total_scrap
    
    print(f"\nScrap Summary:")
    for reason, count in scrap_details:
        print(f"  {reason}: {count} parts")
    print(f"Total scrap: {total_scrap}")
    print(f"Good parts made: {good_parts_made}")
    
    return good_parts_made, total_scrap


# Initialize database
init_database()

selected_part_number, order_quantity, parts_made = part_selection()
order = Order(selected_part_number, order_quantity)
print(order.summary())
good_parts, total_scrap = scrap_tracking(parts_made, selected_part_number, order.order_number)
remaining_parts = order_quantity - good_parts

print(f"Remaining parts to complete order: {remaining_parts}")

part = Part(selected_part_number)
rate_percentage = part.rate_percentage(good_parts)
print("Rate made: " + f"{rate_percentage:.1f}" + "% of expected " + str(part.expected_rate))
