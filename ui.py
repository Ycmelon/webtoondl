import os
import sys
import table
import webtoondl
from termcolor import colored, cprint

version = "1.1.1"
sys.stdout.write(f"\x1b]2;{'WEBTOONDL v'}{version}\x07")


def clear():
    os.system("cls")


def newline():
    print()


def print_header():
    print(
        f"{colored(f'WEBTOONDL v{version}', 'green', attrs=['bold'])} by Ycmelon https://github.com/Ycmelon/webtoondl")
    newline()


# Getting webtoon information
print_header()
search_results = False
while not search_results:
    print(colored("Webtoon name: ", "cyan"))
    search_query = input()
    newline()
    search_results = webtoondl.search_webtoon(search_query)
    if search_results == False:
        print(colored("No webtoons found! Try again.", "red"))

search_results["originals"].extend(search_results["canvas"])
search_results = search_results["originals"]
print_list = []
for index, result in enumerate(search_results):
    index = colored(index, 'yellow', attrs=['bold'])
    title = colored(result[2], 'white')
    author = colored(result[3], 'white')
    likes = colored(f"♥ {result[4]}", 'white', 'on_green')
    print_list.append([index, title, author, likes])
table.table(print_list)

input_valid = False
while input_valid == False:
    newline()
    selected_webtoon = input("Select: ")
    try:
        selected_webtoon = search_results[int(selected_webtoon)]
        input_valid = True
    except Exception:
        print(colored("Invalid input! Try again.", "red"))

title_no = selected_webtoon[0]
title = selected_webtoon[2]
if selected_webtoon[5] == "canvas":
    canvas = True
elif selected_webtoon[5] == "original":
    canvas = False

# Getting episode information
clear()
print_header()
print(colored("Webtoon name: ", "cyan"))
print(selected_webtoon[2])
newline()

input_valid = False
while input_valid == False:
    print(f"{colored('First episode to download:', 'cyan')} (e.g. first, 6)")
    range_start = input()
    newline()
    if range_start == "first":
        range_start = 1
        input_valid = True
    else:
        try:
            range_start = int(range_start)
            input_valid = True
        except Exception:
            print(colored("Invalid input! Try again.", "red"))


input_valid = False
while input_valid == False:
    print(f"{colored('Last episode to download:', 'cyan')} (e.g. last, 37)")
    range_end = input()
    newline()
    if range_end == "last":
        range_end = int(webtoondl.get_last_episode(title_no, canvas))
        input_valid = True
    else:
        try:
            range_end = int(range_end)
            input_valid = True
            if range_end > int(webtoondl.get_last_episode(title_no, canvas)):
                print("Last episode number too large! Defaulting to last episode")
                range_end = int(webtoondl.get_last_episode(title_no, canvas))
        except Exception:
            print(colored("Invalid input! Try again.", "red"))


download_range = range(range_start, range_end+1)

# Getting output format
print(f"{colored('Output format:', 'cyan')} (combined, separate, images)")
output_format = input().lower()
newline()

# Downloading
clear()
print_header()
print(colored("Downloading:", "cyan"))
print(f"{title} Episodes {download_range[0]}-{download_range[-1]}")
newline()
print(colored("Output format:", "cyan"))
print(output_format)
newline()
output_location = webtoondl.download(
    title_no, download_range, output=output_format, clean=False)

clear()
print_header()
print(colored("Downloading:", "cyan"))
print(f"{title} Episodes {download_range[0]}-{download_range[-1]}")
newline()
print(colored("Output format:", "cyan"))
print(output_format)
newline()
print(colored("Completed! Output location:", "cyan"))
print(output_location)
input()
