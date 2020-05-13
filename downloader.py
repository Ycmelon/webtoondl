import os
import json
import logging

import requests
from tqdm import tqdm

# Constants
urls_key = "image_urls"

# Logging (WIP)


def download(project_path: str, request_headers: dict, file_format: str):
    """Downloads images from given image urls

    Args:
        project_path(str)
        request_headers(dict)

    Output:
        Image files
    """
    with open(os.path.join(project_path, "image_urls.json"), "r") as file:
        chapters = json.load(file)
        logging.info("image_urls.json loaded!")

    for chapter, info in tqdm(chapters.items(), desc="Downloading chapters", unit="chapters"):
        logging.info(f"Downloading chapter: {chapter}")
        chapter_path = os.path.join(project_path, chapter)
        if not os.path.exists(chapter_path):
            os.makedirs(chapter_path)
        for index, url in enumerate(info[urls_key]):
            # index + 1: 0th --> 1.jpeg
            with open(os.path.join(chapter_path, f"{index+1}.{file_format}"), "wb") as file:
                file.write(requests.get(url, headers=request_headers).content)
            logging.info(f"Downloaded image {str(index+1)}")

    logging.info("Complete!")
