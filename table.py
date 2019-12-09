def table(vars):
    width = len(vars[0])
    max_lengths = [0 for _ in range(width)]
    for row in vars:
        for index in range(width):
            if len(row[index]) > max_lengths[index]:
                max_lengths[index] = len(row[index])

    for row in vars:
        to_print = ""
        for index in range(width):
            spaces = max_lengths[index] - len(row[index])
            to_print = to_print + f"{row[index]}{' '*spaces} "
        print(to_print)
