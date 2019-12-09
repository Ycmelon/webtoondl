import webtoondl
import os
import sys
from termcolor import colored, cprint
import table

version = "1.0.1"
sys.stdout.write(f"\x1b]2;{'Webtoondl v'}{version}\x07")


def clear():
    os.system("clear")
    os.system("cls")


def print_header():
    print(
        f"{colored(f'WEBTOONDL v{version}', 'green', attrs=['bold'])} by Ycmelon https://github.com/Ycmelon/webtoondl")
    print()


# Getting webtoon information
print_header()
print(colored("Webtoon name: ", "cyan"))
search_query = input()
print()

search_results = webtoondl.search_webtoon(search_query)
search_results["originals"].extend(search_results["canvas"])
search_results = search_results["originals"]
print_list = []
for index, result in enumerate(search_results):
    index = colored(index, 'yellow', attrs=['bold'])
    title = colored(result[2], 'white')
    author = colored(result[3], 'white')
    likes = colored(f"{result[4]} ♥", 'white', 'on_green')
    print_list.append([index, title, author, likes])
table.table(print_list)
selected_webtoon = search_results[int(input("Select: "))]
title_no = selected_webtoon[0]
if selected_webtoon[5] == "canvas":
    canvas = True
elif selected_webtoon[5] == "original":
    canvas = False

# Getting episode information
clear()
print_header()
print(colored("Webtoon name: ", "cyan"))
print(selected_webtoon[2])
print()

print(f"{colored('First episode to download:', 'cyan')} (e.g. first, 6)")
range_start = input()
print()
if range_start == "first":
    range_start = 1
else:
    range_start = int(range_start)

print(f"{colored('Last episode to download:', 'cyan')} (e.g. last, 37)")
range_end = input()
print()
if range_end == "last":
    range_end = int(webtoondl.get_last_episode(title_no, canvas))
else:
    range_end = int(range_end)
    if range_end > int(webtoondl.get_last_episode(title_no, canvas)):
        print("Last episode number too large! Defaulting to last episode")
        range_end = int(webtoondl.get_last_episode(title_no, canvas))

download_range = range(range_start, range_end+1)

# Getting output format
print(f"{colored('Output format:', 'cyan')} (combined, separate, images)")
output_format = input().lower()
print()

# Downloading
clear()
print_header()
print(colored("Downloading:", "cyan"))
print(f"{title} Episodes {download_range[0]}-{download_range[-1]}")
print()
print(colored("Output format:", "cyan"))
print(output_format)
print()
output_location = webtoondl.download(
    title_no, download_range, output=output_format, clean=False)

clear()
print_header()
print(colored("Downloading:", "cyan"))
print(f"{title} Episodes {download_range[0]}-{download_range[-1]}")
print()
print(colored("Output format:", "cyan"))
print(output_format)
print()
print(colored("Completed! Output location:", "cyan"))
print(output_location)
input()