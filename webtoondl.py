import os
import glob
import shutil
import pickle
import logging
import img2pdf
import requests
from tqdm import tqdm
from zipfile import ZipFile
from datetime import datetime
from bs4 import BeautifulSoup
from functools import lru_cache
from collections import defaultdict


output_folder = "output"
webtoon_filetype = "jpg"  # if changed in future
bs4_htmlparser = "html.parser"
image_urls_dat = "image_urls.dat"
progress_dat = "progress.dat"


@lru_cache
def is_canvas(title_no):
    """Returns whether given title number is CANVAS

    Args:
        title_no(str): Title number of series to check

    Returns:
        bool: Whether given title number is CANVAS

    Raises:
        ValueError: Webtoon title number is not found
    """

    url = f"https://www.webtoons.com/en/fantasy/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no=1"
    if requests.get(url).status_code == 200:
        return False

    url = f"https://www.webtoons.com/en/challenge/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no=1"
    if requests.get(url).status_code == 200:
        return True

    raise ValueError("Webtoon not found!")


def loading_bar(iterable, unit):
    """Generates loading bar for iterable

    Args:
        iterable(iterable): Iterable to generate a loading bar for
        unit(str): Unit of iterable to display

    Returns:
        TQDM loading bar
    """

    return tqdm(iterable, unit=unit, ncols=100)


def get_title(title_no):
    """Gets title for given title number

    Args:
        title_no(str): Title number of series to get title of

    Returns:
        str: Title of given series number
    """
    url = get_full_url(title_no)
    webpage = requests.get(url).content

    title = str(webpage).split('<title>')[1].split('</title>')[0]
    title = title.split(" | ")[0]

    return title


def get_full_url(title_no, episode_no=0):
    """Gets full URL for given title and episode numbers

    Args:
        title_no(str): Title number of series to get URL for
        episode_no(str): Episode number to get URL for

    Retuns:
        str: Full URL given the title and episode numbers
    """

    if is_canvas(title_no):
        genre = "challenge"
    else:
        genre = "fantasy"

    if not episode_no == 0:
        url = f"https://www.webtoons.com/en/{genre}/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no={episode_no}"
    else:
        url = f"https://www.webtoons.com/en/{genre}/castle-swimmer/list?title_no={title_no}"

    return url


def search_webtoon(query):
    """Searches Webtoon for given query to find series

    Args:
        query(str): Search query

    Returns:
        bool: False if there are no results
        dict: Dictionary containing the search results
    """

    url = requests.utils.requote_uri(
        f"https://www.webtoons.com/search?keyword={query}")
    soup = BeautifulSoup(requests.get(url).content, features=bs4_htmlparser)

    # No results
    if soup.find(class_="card_nodata"):
        return False

    links = []
    # If originals results present
    if soup.find(class_="card_lst"):
        links += soup.find(class_="card_lst").find_all("a")
    # If canvas results present
    if soup.find(class_="challenge_lst"):
        links += soup.find(class_="challenge_lst").find("ul").find_all("a")

    results = []
    for link in links:
        title_no = link["href"].split("=")[1]
        img_src = link.find("img")["src"]
        subj = link.find(class_="subj").text
        author = link.find(class_="author").text
        likes = link.find(class_="grade_num").text
        if likes == "Like":
            likes = 0
        results.append([title_no, img_src, subj, author, likes])

    return results


def get_last_episode(title_no):
    """Get last episode number

    Args:
        title_no(str): Title number of series

    Returns:
        str: Last episode number
    """

    url = get_full_url(title_no)
    soup = BeautifulSoup(requests.get(url).content, features=bs4_htmlparser)
    last_episode = soup.find(id="_listUl").find("li")["data-episode-no"]

    return last_episode


def download(title_no, download_range, output="combined", clean=False, unique=False):
    """Download webtoons

    Args:
        title_no(str): Title number of series to download
        download_range(iterable): Range of episodes to download
        output(str): Output format
            "combined": Combined PDF
            "separate": Zipped separate PDFs
            "images": Zipped image files
        clean(bool): Whether to cleanup working files
        unique(bool): Whether to create custom ID for unique filename

    Returns:
        str: Path to output file

    Raises:
        ValueError: Output format not recognised
        Exception: Status code 200 for request
    """

    if not type(download_range) == list:
        download_range = list(download_range)

    id_ = datetime.now().strftime(" %d%m%Y%H%M%S%f") if unique else ""
    document_name = f"{get_title(title_no)} Episodes {download_range[0]}-{download_range[-1]}{id_}"
    image_urls = defaultdict(list)
    progress = 0
    request_headers = {'User-agent': 'Mozilla/5.0',
                       "Referer": get_full_url(title_no, episode_no="1")}

    working_dir = os.path.join(output_folder, document_name)
    os.makedirs(working_dir, exist_ok=True)

    # Check for progress
    if os.path.exists(os.path.join(working_dir, progress_dat)):
        with open(os.path.join(working_dir, progress_dat), "r") as f:
            progress = f.read().split("\n")
            progress.remove("")
            progress = int(progress[-1])

    if os.path.exists(os.path.join(working_dir, image_urls_dat)):
        with open(os.path.join(working_dir, image_urls_dat), "rb") as f:
            image_urls = pickle.load(f)

    # Get image urls
    if image_urls == defaultdict(list):
        for episode_no in loading_bar(download_range, "links"):
            url = get_full_url(title_no, episode_no)
            request = requests.get(url)
            if request.status_code == 404:
                download_range.append(download_range[-1]+1)
                continue
            soup = BeautifulSoup(request.content, features=bs4_htmlparser)
            for img in soup.find(id="_imageList").find_all("img"):
                image_urls[episode_no].append(img.get("data-url"))

        # Save progress
        with open(os.path.join(working_dir, image_urls_dat), "wb") as file:
            pickle.dump(image_urls, file)

    episode_lengths = {}
    for episode, urls in image_urls.items():
        episode_lengths[episode] = len(urls)

    # Get images
    if not progress == 0:
        for key in range(1, progress+1):
            image_urls.pop(key, None)
    with open(os.path.join(working_dir, progress_dat), "a+") as f:
        for episode_no, urls in image_urls.items():
            os.makedirs(os.path.join(
                working_dir, str(episode_no)), exist_ok=True)
            for index, image_url in enumerate(urls):
                filename = f"{index}.{webtoon_filetype}"
                request = requests.get(
                    image_url, stream=True, headers=request_headers)
                if request.status_code == 200:
                    with open(os.path.join(working_dir, str(episode_no), filename), 'wb') as file:
                        request.raw.decode_content = True
                        shutil.copyfileobj(request.raw, file)
                else:
                    raise Exception(f"Request error: {request.status_code}")
            f.write(str(episode_no)+"\n")

    # Output
    if output == "images":
        output_path = os.path.join(output_folder, f"{document_name}.zip")
        with ZipFile(output_path, "w") as output_archive:
            for episode, length in episode_lengths.items():
                for image in range(length):
                    output_archive.write(os.path.join(working_dir, str(episode), f"{image}.{webtoon_filetype}"),
                                         os.path.join(str(episode), f"{image}.{webtoon_filetype}"))
        return_output = output_path

    elif output == "separate":
        for episode, length in episode_lengths.items():
            image_list = []
            for image in range(length):
                image_list.append(os.path.join(working_dir, str(
                    episode), f"{image}.{webtoon_filetype}"))
            with open(os.path.join(working_dir, f"{episode}.pdf"), "wb") as file:
                file.write(img2pdf.convert(image_list))

        # Returning
        output_path = os.path.join(output_folder, f"{document_name}.zip")
        with ZipFile(output_path, "w") as output_archive:
            for episode in episode_lengths.keys():
                output_archive.write(os.path.join(
                    working_dir, f"{episode}.pdf"), f"{episode}.pdf")

    elif output == "combined":
        image_list = []
        for episode, length in episode_lengths.items():
            for image in range(length):
                image_list.append(os.path.join(working_dir, str(
                    episode), f"{image}.{webtoon_filetype}"))

        output_path = os.path.join(output_folder, f"{document_name}.pdf")
        with open(output_path, "wb") as file:
            file.write(img2pdf.convert(image_list))
    else:
        raise ValueError("Unrecognised output type!")

    if clean:
        shutil.rmtree(working_dir)

    return output_path


download(70280, range(1, 10), output="combined")
