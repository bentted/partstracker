
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
            numparts = int(input("Enter number of parts: "))
            if numparts < 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid non-negative integer for number of parts.")
    print("Part number: " + part_number + ", Number of parts: " + str(numparts))
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

    totalparts = numparts - scrap_parts
    print("Total good parts: " + str(totalparts))
    return totalparts


selected_part_number, selected_parts = part_selection()
good_parts = scrap_reason(selected_parts)
part = Part(selected_part_number)
rate_percentage = part.rate_percentage(good_parts)
print("Rate made: " + f"{rate_percentage:.1f}" + "% of expected " + str(part.expected_rate))