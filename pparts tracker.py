
scrap_reasons = ["foreign material", "smear", "chip", "burn", "light", "heavy", "crack", "no fill"]
part_numbers = ["780208", "780508", "780108", "780308", "780608"]

def part_selection():
    part_number = input("Enter part number: ")
    mix = input("Enter mix number: ")
    if part_number not in part_numbers:
        print("Invalid part number. Please enter a valid part number from the list: " + ", ".join(part_numbers))
        return part_selection()
    else:
        part_number = part_number + mix
    while True:
        try:
            numparts = int(input("Enter number of parts: "))
            if numparts < 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid non-negative integer for number of parts.")
    print("Part number: " + part_number + ", Number of parts: " + str(numparts))
    return numparts


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

    totalparts = numparts - scrap_parts
    print("Total good parts: " + str(totalparts))
    return totalparts


selected_parts = part_selection()
scrap_reason(selected_parts)