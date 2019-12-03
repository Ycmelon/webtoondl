import os
import glob
import shutil
import pickle
import logging
import img2pdf
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup


output_folder = "output"
webtoon_filetype = "jpg"  # if changed in future (WEBP revolution???)
bs4_htmlparser = "html.parser"  # other os


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


def get_title(url, title_no, canvas):
    if not canvas:
        webpage = requests.get(url).content
        title = str(webpage).split('<title>')[1].split('</title>')[0]
        return title.split(" | ")[1]
    else:
        # TODO: get title name for canvas
        title = title_no
        return title


def get_full_url(title_no, episode_no, canvas):
    if not canvas:
        url = f"https://www.webtoons.com/en/fantasy/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no={episode_no}"
    else:
        url = f"https://www.webtoons.com/en/challenge/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no={episode_no}"

    return url


def download(title_no, download_range, pdf=True, working_dir=False, clean=True):
    download_range = list(download_range)
    canvas = is_canvas(title_no)
    title = get_title(get_full_url(title_no, "1", canvas), title_no, canvas)
    document_name = f"{title} Episodes {download_range[0]}-{download_range[-1]}"
    request_headers = {'User-agent': 'Mozilla/5.0',
                       "Referer": get_full_url(title_no, "1", canvas)}
    if not working_dir:
        working_dir = os.path.join(output_folder, document_name)

    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
        with open(os.path.join(working_dir, "latest.log"), "w") as file:
            pass

    logging.basicConfig(format='%(asctime)s - %(message)s',
                        filename=os.path.join(working_dir, "latest.log"), level=logging.INFO)
    logging.info("Started")

    # Getting image URLs
    if os.path.exists(os.path.join(working_dir, "image_urls.dat")):
        logging.info("Image URLs loaded")
        with open(os.path.join(working_dir, "image_urls.dat"), "rb") as file:
            image_urls = pickle.load(file)
    else:
        logging.info("Generating image URLs")
        image_urls = {}
        for episode_no in loading_bar(download_range, "links"):
            url = get_full_url(title_no, episode_no, canvas)
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
        with open(os.path.join(working_dir, "image_urls.dat"), "wb") as file:
            pickle.dump(image_urls, file)
        logging.info("Saved image URLs to file")

    # TODO: Check for old files (from an info file.)
    '''
    subdirectories = os.walk(working_dir)[0][1]
    for episode in subdirectories:
        if glob.glob(f"{working_dir}/{episode}/*.{webtoon_filetype}") != []:  # If old files found
            filenames = glob.glob(f"{working_dir}/*.{webtoon_filetype}")
            image_nos = [int(filename.split("\\")[1].split(".")[0])
                        for filename in filenames]
            image_nos.sort()
            last_downloaded_image = image_nos[-1]
            image_urls = image_urls[last_downloaded_image-1:]
            logging.info(f"Old files found, resuming from {last_downloaded_image}")
    '''

    # Saving files
    logging.info("Downloading images")
    for episode_no, image_urls in loading_bar(image_urls.items(), "images"):
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
                # TODO: tryagain//exception
                logging.warning("Request error")

    # Saving PDF
    if pdf:
        logging.info("Saving PDF")
        episode_folders = list(os.walk(working_dir))[0][1]
        episode_folders = sorted([int(episode) for episode in episode_folders])

        if pdf == "separate":
            for folder in loading_bar(episode_folders, "pdfs"):
                filenames = glob.glob(
                    f"{working_dir}/{folder}/*.{webtoon_filetype}")
                image_nos = [filename.split("\\")[-1].split(".")[0]
                             for filename in filenames]
                filenames = dict(zip(filenames, image_nos))
                sorted_filenames = list(
                    zip(*sorted(filenames.items(), key=lambda kv: kv[1])))[0]
                with open(os.path.join(working_dir, f"{folder}.pdf"), "wb") as file:
                    file.write(img2pdf.convert(sorted_filenames))
                    logging.info(f"Finished saving episode {folder} PDF")

        elif pdf == "combined":
            all_filenames = []
            all_image_nos = []
            for folder in episode_folders:
                filenames = glob.glob(
                    f"{working_dir}/{folder}/*.{webtoon_filetype}")
                image_nos = [filename.split("\\")[-1].split(".")[0]
                             for filename in filenames]
                all_filenames.extend(filenames)
                all_image_nos.extend(image_nos)
            with open(os.path.join(working_dir, f"{document_name}.pdf"), "wb") as file:
                file.write(img2pdf.convert(all_filenames))
                logging.info(f"Finished saving {document_name} PDF")

        else:
            logging.error("PDF option not recognised!")
            raise Exception("PDF option not recognised!")

    logging.info("Complete, exiting")
    logging.shutdown()

    if clean:
        # TODO: fix clean (dont remove pdfs :/)
        shutil.rmtree(working_dir)


download(70280, range(1, 13), clean=False, pdf="combined")
