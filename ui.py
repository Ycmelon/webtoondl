import webtoondl
import os
from termcolor import colored, cprint

version = "1.0.1"

# Header
print(
    f"{colored(f'WEBTOONDL v{version}', 'green', attrs=['bold'])} by Ycmelon https://github.com/Ycmelon/webtoondl")
print()

# Getting webtoon information
print(colored("Webtoon name: ", "cyan"))
search_query = input()
print()
search_results = webtoondl.search_webtoon(search_query)
search_results["originals"].extend(search_results["canvas"])
search_results = search_results["originals"]

for index, result in enumerate(search_results):
    index = colored(index, 'yellow', attrs=['bold'])
    title = colored(result[2], 'white')
    author = colored(result[3], 'white')
    likes = colored(f"{result[4]} ♥", 'white', 'on_green')
    print(f"{index}: {title} by {author} ({likes})")

selected_webtoon = search_results[int(input("Select: "))]

title_no = selected_webtoon[0]
if selected_webtoon[5] == "canvas":
    canvas = True
elif selected_webtoon[5] == "original":
    canvas = False

# Getting range of episodes to download
range_start = input("First episode to download (e.g. first, 6): ")
if range_start == "first":
    range_start = 1
else:
    range_start = int(range_start)

range_end = input("Last episode to download (e.g. last, 37): ")
if range_end == "last":
    range_end = int(webtoondl.get_last_episode(title_no, canvas))
else:
    range_end = int(range_end)
    if range_end > int(webtoondl.get_last_episode(title_no, canvas)):
        print("Last episode number too large! Defaulting to last episode")
        range_end = int(webtoondl.get_last_episode(title_no, canvas))

download_range = range(range_start, range_end+1)

# Getting output format
output_format = input("Output format (combined, separate, images): ")

# Downloading
output_location = webtoondl.download(
    title_no, download_range, output=output_format, clean=False)

input(f"Completed! Output location: {output_location}")
