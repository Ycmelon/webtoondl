import os
import json
from functools import lru_cache
from typing import Iterable

import cloudscraper
from tqdm import tqdm
from bs4 import BeautifulSoup
from requests_html import HTMLSession

import utils
from .source import Source

scraper = cloudscraper.create_scraper()
session = HTMLSession()

# Constants
html_parser = "html.parser"
base_url = "https://www.fashionlib.net"  # Reader site


class Mangago(Source):
    def get_url(self, series: str, range_: Iterable, project_path: str):
        """Gets image urls for given series and range

        Args:
            series(str)
            range_(iter)

        Output:
            image_urls.json in project_path
        """
        first_url = f"http://www.mangago.me/read-manga/{series}{self.get_url_structure(series)}"
        soup = BeautifulSoup(scraper.get(first_url).text, features=html_parser)
        print(first_url)
        chapters_element = soup.find("ul", class_="dropdown-menu chapter")
        chapters = {}
        for index, a in enumerate(chapters_element.find_all("a")):
            if not index + 1 in range_:
                break
            chapter_name = utils.pathsafe(f"{index + 1}. {a.text}")
            chapters[chapter_name] = {}
            chapters[chapter_name]["image_urls"] = []
            # Trim "1/" (first chapter)
            chapters[chapter_name]["sub_url"] = a["href"][:-2]

        # Get chapters, page count
        for chapter, info in tqdm(
            chapters.items(), desc="Getting chapter page counts", unit="chapters"
        ):
            full_url = base_url + info["sub_url"]
            soup = BeautifulSoup(scraper.get(full_url).text, features=html_parser)
            pages_element = soup.find("ul", class_="dropdown-menu page")
            chapters[chapter]["page_count"] = int(
                pages_element.find_all("a")[-1].text.split("Pg ")[-1]
            )

        # Get image urls
        for chapter, info in tqdm(
            chapters.items(), desc="Getting chapter image urls", unit="chapters"
        ):
            for page in range(1, info["page_count"] + 1):  # +1 so 5eps, range(1, 6)
                full_url = base_url + info["sub_url"] + str(page)
                r = session.get(full_url)
                r.html.render()
                soup = BeautifulSoup(r.html.html, features=html_parser)
                if soup.find("img", class_=f"page{str(page)}") == None:
                    # Skip <canvas> pages; TODO: implement
                    continue
                chapters[chapter]["image_urls"].append(
                    soup.find("img", class_=f"page{str(page)}")["src"]
                )
            del chapters[chapter]["page_count"]

        with open(os.path.join(project_path, "image_urls.json"), "w") as file:
            json.dump(chapters, file)

    def get_length(self, series: str) -> int:
        """Gets length (number of chapters) of given series

        Args:
            series(str)

        Returns:
            int: Length of given series
        """
        url = f"http://www.mangago.me/read-manga/{series}{self.get_url_structure(series)}"
        soup = BeautifulSoup(scraper.get(url).text, features=html_parser)
        chapters_element = soup.find("ul", class_="dropdown-menu chapter")
        return len(chapters_element.find_all("a"))

    @lru_cache
    def is_series(self, series: str) -> bool:
        """Returns whether given series exists

        Args:
            series(str)

        Returns:
            bool
        """
        url = f"http://www.mangago.me/read-manga/{series}"
        if scraper.get(url).status_code != 200:
            return False
        return True

    @lru_cache
    def get_url_structure(self, series: str) -> str:
        """Returns structure of URL

        Args:
            series(str)

        Returns:
            str
        """
        url = f"http://www.mangago.me/read-manga/{series}"
        soup = BeautifulSoup(scraper.get(url).text, features=html_parser)
        read_button = soup.find("a", class_="content-h1-btn yellow normal")
        # Stripping URL to just the end
        return read_button["href"].split(series)[1]

    def get_request_headers(self, series: str) -> str:
        """Get request headers for given series

        Args:
            series(str)

        Returns:
            str
        """
        return {"User-agent": "Mozilla/5.0"}

    @lru_cache
    def get_file_format(self, project_path: str) -> str:
        """Get file format of series (requires image_urls.json)

        Args:
            project_path(str)

        Returns:
            str
        """
        with open(os.path.join(project_path, "image_urls.json"), "r") as file:
            image_urls = json.load(file)

        # First image url
        image_url = list(image_urls.items())[0][1]["image_urls"][0]

        return image_url.split(".")[-1].split("?")[0]