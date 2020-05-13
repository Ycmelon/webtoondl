import os
import json
import logging

import img2pdf
import requests

# Constants
urls_key = "image_urls"

# Logging (WIP)
# log_format = "%(asctime)s::%(levelname)s::%(lineno)d::%(message)s"
# logging.basicConfig(filename='log.log', filemode='w',
#                     level=logging.INFO, format=log_format)


def output(project_name: str, project_path: str, output_folder: str, output_format: str, file_format: str):
    """Creates output from images downloaded

    Args:
        project_name(str)
        project_path(str)
        output_folder(str)
        output_format(str)
        file_format(str)

    Output:
        PDF: output_format == "combined"
    """
    with open(os.path.join(project_path, "image_urls.json"), "r") as file:
        chapters = json.load(file)
        logging.info("image_urls.json loaded!")

    if output_format == "combined":  # TODO: other methods
        logging.info("output_format: combined")
        image_list = []
        for chapter, info in chapters.items():
            logging.info(f"Adding chapter: {chapter}")
            for page in range(len(info[urls_key])):
                image_list.append(
                    os.path.join(project_path, chapter, f"{page+1}.{file_format}"))
                logging.info(f"Added image {str(page+1)}")

        with open(os.path.join(output_folder, f"{project_name}.pdf"), "wb") as file:
            file.write(img2pdf.convert(image_list))

    logging.info("Complete!")
