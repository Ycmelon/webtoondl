import os
import json
from functools import lru_cache
from typing import Iterable

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup

import utils
from .source import Source

# Constants
html_parser = "html.parser"  # TODO: remove


class Webtoon(Source):
    @lru_cache
    def is_canvas(self, series: str):
        """Returns whether given series is CANVAS

        Args:
            series(str)

        Returns:
            bool
        """

        url = f"https://www.webtoons.com/en/fantasy/castle-swimmer/extra-episode-3/viewer?title_no={series}&episode_no=1"
        if requests.get(url).status_code == 200:
            return False

        url = f"https://www.webtoons.com/en/challenge/castle-swimmer/extra-episode-3/viewer?title_no={series}&episode_no=1"
        if requests.get(url).status_code == 200:
            return True

    @lru_cache
    def is_series(self, series: str) -> bool:
        """Returns whether given series exists

        Args:
            series(str)

        Returns:
            bool
        """
        url = f"https://www.webtoons.com/en/fantasy/castle-swimmer/extra-episode-3/viewer?title_no={series}&episode_no=1"
        if requests.get(url).status_code == 200:
            return True
        url = f"https://www.webtoons.com/en/challenge/castle-swimmer/extra-episode-3/viewer?title_no={series}&episode_no=1"
        if requests.get(url).status_code == 200:
            return True

        return False

    def get_full_url(self, series: str, episode_no: int = None):
        """Gets full URL for given title and episode numbers

        Args:
            title_no(str): Title number of series to get URL for
            episode_no(str): Episode number to get URL for

        Returns:
            str
        """
        if self.is_canvas(series):
            genre = "challenge"
        else:
            genre = "fantasy"

        if episode_no == None:  # Series page
            url = f"https://www.webtoons.com/en/{genre}/castle-swimmer/list?title_no={series}"
        else:
            url = f"https://www.webtoons.com/en/{genre}/castle-swimmer/extra-episode-3/viewer?title_no={series}&episode_no={episode_no}"

        return url

    def get_url(self, series: str, range_: Iterable, project_path: str):
        """Gets image URLs for given series and range

        Args:
            series(str)
            range_(iter)

        Output:
            image_urls.json in project_path
        """
        range_ = list(range_)
        chapters = {}

        for chapter in tqdm(range_, desc="Getting chapter image URLs", unit="chapters"):
            url = self.get_full_url(series, chapter)
            request = requests.get(url)
            if request.status_code == 404:  # Deleted episode
                range_.append(range_[-1] + 1)  # Compensate
                continue

            soup = BeautifulSoup(request.content, features=html_parser)

            chapter_name = utils.pathsafe(
                f"{chapter}. {soup.find('h1', class_='subj_episode').text}"
            )
            chapters[chapter_name] = {}
            chapters[chapter_name]["image_urls"] = []
            for img in soup.find(id="_imageList").find_all("img"):
                chapters[chapter_name]["image_urls"].append(img.get("data-url"))

        with open(os.path.join(project_path, "image_urls.json"), "w") as file:
            json.dump(chapters, file)

    def get_length(self, series: str) -> int:
        """Gets length (number of chapters) of given series

        Args:
            series(str)

        Returns:
            int: Length of given series
        """
        url = self.get_full_url(series, None)  # Series page
        soup = BeautifulSoup(requests.get(url).content, features=html_parser)
        # First (latest) episode on page's episode number
        return int(soup.find("span", class_="tx").text.replace("#", ""))

    def get_request_headers(self, series: str) -> str:
        """Get request headers for given series

        Args:
            series(str)

        Returns:
            str
        """
        return {"User-agent": "Mozilla/5.0", "Referer": self.get_full_url(series, episode_no=1)}

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

        # First image URL
        image_url = list(image_urls.items())[0][1]["image_urls"][0]

        return image_url.split(".")[-1].split("?")[0]
