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


output_folder = "output"
webtoon_filetype = "jpg"  # if changed in future (WEBP revolution???)
bs4_htmlparser = "html.parser"
image_urls_savelocation = "image_urls.dat"
progress_savelocation = "progress.dat"


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
        raise ValueError("Webtoon not found!")

    return output


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

    url = f"https://www.webtoons.com/search?keyword={query}"
    url = requests.utils.requote_uri(url)

    soup = BeautifulSoup(requests.get(url).content, features=bs4_htmlparser)
    if soup.find(class_="card_nodata"):
        return False

    results = {"originals": [], "canvas": []}
    # If originals results present
    if soup.find(class_="card_lst"):
        for a in soup.find(class_="card_lst").find_all("a"):
            title_no_ = a["href"].split("=")[1]
            img_src = a.find("img")["src"]
            subj = a.find(class_="subj").text
            author = a.find(class_="author").text
            likes = a.find(class_="grade_num").text
            if likes == "Like":
                likes = 0
            results["originals"].append(
                [title_no_, img_src, subj, author, likes, "original"])

    # If canvas results present
    if soup.find(class_="challenge_lst"):
        for a in soup.find(class_="challenge_lst").find("ul").find_all("a"):
            title_no_ = a["href"].split("=")[1]
            img_src = a.find("img")["src"]
            subj = a.find(class_="subj").text
            author = a.find(class_="author").text
            likes = a.find(class_="grade_num").text
            if likes == "Like":
                likes = 0
            results["canvas"].append(
                [title_no_, img_src, subj, author, likes, "canvas"])

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


def download(title_no, download_range, output="combined", working_dir=False, clean=True, unique=False):
    """Download webtoons

    Args:
        title_no(str): Title number of series to download
        download_range(iterable): Range of episodes to download
        output(str): Output format
            "combined": Combined PDF
            "separate": Zipped separate PDFs
            "images": Zipped image files
        working_dir(str): Custom working directory
        clean(bool): Whether to cleanup working files
        unique(bool): Whether to create custom ID for unique filename

    Returns:
        str: Path to output file

    Raises:
        ValueError: Output format not recognised
        Exception: Status code 200 for request
    """

    download_range = list(download_range)
    canvas = is_canvas(title_no)
    title = get_title(title_no)
    document_name = f"{title} Episodes {download_range[0]}-{download_range[-1]}"
    if unique:
        id_ = datetime.now().strftime("%d%m%Y%H%M%S%f")
        document_name = f"{document_name} {id_}"
    request_headers = {'User-agent': 'Mozilla/5.0',
                       "Referer": get_full_url(title_no, "1")}

    if not working_dir:
        working_dir = os.path.join(output_folder, document_name)

    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
        with open(os.path.join(working_dir, "latest.log"), "w") as file:
            pass

    logging.basicConfig(format='%(asctime)s - %(levelname)s:%(message)s',
                        filename=os.path.join(working_dir, "latest.log"), level=logging.INFO)
    logging.info("Started")

    # Getting image URLs
    if os.path.exists(os.path.join(working_dir, image_urls_savelocation)):
        logging.info("Image URLs loaded")
        with open(os.path.join(working_dir, image_urls_savelocation), "rb") as file:
            image_urls = pickle.load(file)
    else:
        logging.info("Generating image URLs")
        image_urls = {}
        for episode_no in loading_bar(download_range, "links"):
            url = get_full_url(title_no, episode_no)
            if requests.get(url).status_code == 404:
                logging.info(f"404 for episode {episode_no}")
                download_range.append(download_range[-1]+1)
                continue
            image_urls[episode_no] = []
            soup = BeautifulSoup(requests.get(url).content,
                                 features=bs4_htmlparser)
            for img in soup.find(id="_imageList").find_all("img"):
                image_urls[episode_no].append(img.get("data-url"))
        logging.info("Finished generating image URLs")
        with open(os.path.join(working_dir, image_urls_savelocation), "wb") as file:
            pickle.dump(image_urls, file)
        logging.info("Saved image URLs to file")

    # Saving files
    if os.path.exists(os.path.join(working_dir, progress_savelocation)):
        with open(os.path.join(working_dir, progress_savelocation), "r") as progress_file:
            progress = progress_file.read().split("\n")
            progress.remove("")
            progress = [int(episode_no) for episode_no in progress]
            if not progress == None:
                for finished_ep in progress:
                    del image_urls[finished_ep]

    logging.info("Downloading images")
    with open(os.path.join(working_dir, progress_savelocation), "a+") as progress_file:
        for episode_no, image_urls in loading_bar(image_urls.items(), "episodes"):
            # Create episode folder
            if not os.path.exists(os.path.join(working_dir, str(episode_no))):
                os.makedirs(os.path.join(working_dir, str(episode_no)))

            for index, image_url in enumerate(image_urls):
                filename = f"{episode_no}-{index}.{webtoon_filetype}"

                request = requests.get(
                    image_url, stream=True, headers=request_headers)
                if request.status_code == 200:
                    with open(os.path.join(working_dir, str(episode_no), filename), 'wb') as file:
                        request.raw.decode_content = True
                        shutil.copyfileobj(request.raw, file)

                        logging.info(
                            f"File {filename} downloaded successfully")
                else:
                    logging.warning("Request error: 200")
                    raise Exception("Request error: 200")
            progress_file.write(f"\n{episode_no}")

    # Saving
    logging.info("Saving files")
    episode_folders = list(os.walk(working_dir))[0][1]
    episode_folders = sorted([int(episode) for episode in episode_folders])

    if output == "separate":
        for folder in loading_bar(episode_folders, "pdfs"):
            filenames = glob.glob(
                f"{working_dir}/{folder}/*.{webtoon_filetype}")
            image_nos = [int(filename.split("\\")[-1].split(".")[0].split("-")[1])
                         for filename in filenames]
            filenames = dict(zip(filenames, image_nos))

            # Sorting
            temp = list(zip(image_nos, filenames))
            temp = sorted(temp, key=lambda kv: kv[0])
            temp = list(zip(*temp))[1]

            with open(os.path.join(working_dir, f"{folder}.pdf"), "wb") as file:
                file.write(img2pdf.convert(temp))
                logging.info(f"Finished saving episode {folder} PDF")

        # Returning
        output_path = os.path.join(output_folder, f"{document_name}.zip")
        with ZipFile(output_path, "w") as output_archive:
            for pdf in glob.glob(f"{working_dir}/*.pdf"):
                output_archive.write(pdf, pdf.split(working_dir)[1])
        return_output = output_path
        logging.info("Zipped archive")

    elif output == "combined":
        all_filenames = []
        for folder in episode_folders:
            filenames = glob.glob(
                f"{working_dir}/{folder}/*.{webtoon_filetype}")
            image_nos = [int(filename.split("\\")[-1].split(".")[0].split("-")[1])
                         for filename in filenames]

            # Sorting
            temp = list(zip(image_nos, filenames))
            temp = sorted(temp, key=lambda kv: kv[0])
            temp = list(zip(*temp))[1]

            all_filenames.extend(temp)

        output_path = os.path.join(output_folder, f"{document_name}.pdf")
        with open(output_path, "wb") as file:
            file.write(img2pdf.convert(all_filenames))
            logging.info(f"Finished saving {document_name} PDF")
        return_output = output_path

    elif output == "images":
        output_path = os.path.join(output_folder, f"{document_name}.zip")
        with ZipFile(output_path, "w") as output_archive:
            for jpg in glob.glob(f"{working_dir}/**/*.{webtoon_filetype}"):
                output_archive.write(jpg, jpg.split(document_name)[1])
        return_output = output_path
        logging.info("Zipped archive")

    else:
        logging.error("Output option not recognised!")
        raise ValueError("Output option not recognised!")

    logging.info("Complete, exiting")
    logging.shutdown()

    if clean:
        shutil.rmtree(working_dir)

    return return_output
