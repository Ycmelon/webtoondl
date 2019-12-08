import webtoondl
import os

version = "1.0.0"

print(f"WEBTOONDL v{version} by Ycmelon")
print("Github: https://github.com/Ycmelon/webtoondl")
# Getting webtoon information
search_query = input("Webtoon name: ")
search_results = webtoondl.search_webtoon(search_query)
search_results["originals"].extend(search_results["canvas"])
search_results = search_results["originals"]

for index, result in enumerate(search_results):
    print(f"{index}: {result[2]} by {result[3]} ({result[4]} likes)")

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
