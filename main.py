import os
import glob
import shutil
import pickle
import logging
import img2pdf
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup

# TODO: make into module, web api
# TODO: account for deleted eps (https://github.com/devsnek/webtoondl/issues/3)


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
        return title.split(" | ")[1]
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
download_range = list(range(1, 132))
pdf = True
title_no = "70280"
canvas = is_canvas(title_no)
title = get_title(get_full_url(title_no, "1"))
document_name = f"{title} Episodes {download_range[0]}-{download_range[-1]}"
working_dir = os.path.join("output/", document_name)
webtoon_filetype = "jpg"  # if changed in future
bs4_htmlparser = "html.parser"
request_headers = {'User-agent': 'Mozilla/5.0',
                   "Referer": get_full_url(title_no, "1")}


if not os.path.exists(working_dir):
    os.makedirs(working_dir)
    with open(os.path.join(working_dir, "latest.log"), "w") as file:
        pass
logging.basicConfig(format='%(asctime)s - %(message)s',
                    filename=os.path.join(working_dir, "latest.log"), level=logging.INFO)
logging.info("Started")

# Getting image URLs
if os.path.exists(os.path.join(working_dir, "image_urls.txt")):
    logging.info("Image URLs loaded")
    with open(os.path.join(working_dir, "image_urls.txt"), "rb") as file:
        image_urls = pickle.load(file)
else:
    logging.info("Generating image URLs")
    image_urls = []
    for episode_no in loading_bar(download_range, "links"):
        url = get_full_url(title_no, episode_no)
        if requests.get(url).status_code == 404:
            logging.info(f"404 for episode {episode_no}")
            download_range.append(download_range[-1]+1)
            continue
        soup = BeautifulSoup(requests.get(url).content,
                             features=bs4_htmlparser)
        for img in soup.find(id="_imageList").find_all("img"):
            image_urls.append(img.get("data-url"))
    image_urls = list(enumerate(image_urls))
    logging.info("Finished generating image URLs")
    with open(os.path.join(working_dir, "image_urls"), "wb") as file:
        pickle.dump(image_urls, file)
    logging.info("Saved image URLs to file")


# Saving files
if glob.glob(f"{working_dir}/*.{webtoon_filetype}") != []:  # If old files found
    filenames = glob.glob(f"{working_dir}/*.{webtoon_filetype}")
    image_nos = [int(filename.split("\\")[1].split(".")[0])
                 for filename in filenames]
    image_nos.sort()
    last_downloaded_image = image_nos[-1]
    image_urls = image_urls[last_downloaded_image-1:]
    logging.info(f"Old files found, resuming from {last_downloaded_image}")

logging.info("Downloading images")
for index, image_url in loading_bar(image_urls, "images"):
    filename = f"{index}.{webtoon_filetype}"
    request = requests.get(image_url, stream=True, headers=request_headers)
    if request.status_code == 200:
        with open(os.path.join(working_dir, filename), 'wb') as file:
            request.raw.decode_content = True
            shutil.copyfileobj(request.raw, file)
            logging.info(f"File {filename} downloaded successfully")
    else:
        # TODO: tryagain//exception
        logging.warning("Request error")


# Saving PDF
if pdf:
    logging.info("Saving PDF")
    # TODO: individual PDFs for each ep
    filenames = glob.glob(f"{working_dir}/*.{webtoon_filetype}")
    image_nos = [int(filename.split("\\")[1].split(".")[0])
                 for filename in filenames]
    filenames = dict(zip(filenames, image_nos))
    sorted_filenames = list(
        zip(*sorted(filenames.items(), key=lambda kv: kv[1])))[0]
    with open(os.path.join(working_dir, f"{document_name}.pdf"), "wb") as file:
        file.write(img2pdf.convert(sorted_filenames))
    logging.info("Finished saving PDF")

logging.info("Complete, exiting")
