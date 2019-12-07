import os
import glob
import shutil
import pickle
import logging
import img2pdf
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from zipfile import ZipFile


output_folder = "output"
webtoon_filetype = "jpg"  # if changed in future (WEBP revolution???)
bs4_htmlparser = "html.parser"  # other os
image_urls_savelocation = "image_urls.dat"
progress_savelocation = "progress.dat"


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
    webpage = requests.get(url).content
    if not canvas:
        title = str(webpage).split('<title>')[1].split('</title>')[0]
        title = title.split(" | ")[1]
    else:
        soup = BeautifulSoup(webpage, features=bs4_htmlparser)
        title = soup.select("a.subj")[0].text
    return title


def get_full_url(title_no, episode_no, canvas):
    if not canvas:
        url = f"https://www.webtoons.com/en/fantasy/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no={episode_no}"
    else:
        url = f"https://www.webtoons.com/en/challenge/castle-swimmer/extra-episode-3/viewer?title_no={title_no}&episode_no={episode_no}"

    return url


def download(title_no, download_range, output="combined", working_dir=False, clean=True):
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
                    # TODO: tryagain//exception
                    logging.warning("Request error")
            progress_file.write(f"\n{episode_no}")

    # Saving
    logging.info("Saving files")
    episode_folders = list(os.walk(working_dir))[0][1]
    episode_folders = sorted([int(episode) for episode in episode_folders])

    if output == "separate":
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
        raise Exception("Output option not recognised!")

    logging.info("Complete, exiting")
    logging.shutdown()

    if clean:
        # TODO: fix clean (dont remove pdfs :/)
        shutil.rmtree(working_dir)

    return return_output


download(1499, range(1, 20), clean=False, output="separate")
