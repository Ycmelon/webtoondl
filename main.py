import os
import glob
import shutil
import img2pdf
import requests
import urllib.parse as urlparse
from tqdm import tqdm
from bs4 import BeautifulSoup

# TODO: log
# TODO: make into module, web api


def is_canvas(title_no):
    # Not canvas
    output = False
    url = f"https://www.webtoons.com/en/fantasy/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no=1"

    # Canvas
    if requests.get(url).status_code == 404:
        url = f"https://www.webtoons.com/en/challenge/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no=1"
        output = True

    # Error
    if requests.get(url).status_code == 404:
        output = False
        raise Exception("Webtoon not found!")

    return output


def loading_bar(iterable, unit):
    return tqdm(iterable, unit=unit, ncols=100)


def get_title(url):
    if not canvas:
        webpage = requests.get(url).content
        title = str(webpage).split('<title>')[1].split('</title>')[0]
        return title
    else:
        # TODO: get title name for canvas
        title = title_no
        return title


def get_full_url(title_no, episode_no):
    if not canvas:
        url = f"https://www.webtoons.com/en/fantasy/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no={episode_no}"
    else:
        url = f"https://www.webtoons.com/en/challenge/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no={episode_no}"

    return url


# Variables
download_range = list(range(1, 3))
pdf = True
title_no = "1499"
canvas = is_canvas(title_no)
title = get_title(get_full_url(title_no, "1")).split(" | ")[1]
document_name = f"{title} Episodes {download_range[0]}-{download_range[-1]}"
working_dir = os.path.join("output/", document_name)
webtoon_filetype = "jpg"  # if changed in future
bs4_htmlparser = "html.parser"
request_headers = {'User-agent': 'Mozilla/5.0',
                   "Referer": get_full_url(title_no, "1")}


if os.path.exists(working_dir):
    # Resume progress
    # TODO: progress saving info file
    pass
else:
    os.makedirs(working_dir)


# Getting image URLs
image_urls = []
for episode_no in loading_bar(download_range, "links"):
    url = get_full_url(title_no, episode_no)
    soup = BeautifulSoup(requests.get(url).content, features=bs4_htmlparser)

    for img in soup.find(id="_imageList").find_all("img"):
        image_urls.append(img.get("data-url"))
# TODO: save progress


# Saving files
for index, image_url in loading_bar(enumerate(image_urls), "images"):
    filename = f"{index}.{webtoon_filetype}"

    request = requests.get(image_url, stream=True, headers=request_headers)
    if request.status_code == 200:
        with open(os.path.join(working_dir, filename), 'wb') as file:
            request.raw.decode_content = True
            shutil.copyfileobj(request.raw, file)
    else:
        # TODO: error handling, tryagain
        pass


# Saving PDF
if pdf:
    # TODO: individual PDFs for each ep
    file_paths = glob.glob(f"{working_dir}/*.{webtoon_filetype}")
    with open(os.path.join(working_dir, f"{document_name}.pdf"), "wb") as file:
        file.write(img2pdf.convert(file_paths))
