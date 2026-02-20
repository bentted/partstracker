
scrap_reasons = ["foreign material", "smear", "chip", "burn", "light", "heavy", "crack", "no fill"]


def part_selection():   
    part = input("Enter part number: ")
    mix = input("Enter mix number: ")
    part_number = part +  mix
    print("Part number: " + part_number)


part_selection()

