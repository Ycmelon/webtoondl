import json
import requests
from pkg_resources import parse_version


def get_latest_version(package_name: str) -> str:
    """Get latest version of given pypi package

    Args:
        package_name(str)

    Returns:
        str
    """
    url = f"https://pypi.python.org/pypi/{package_name}/json"
    releases = json.loads(requests.get(url).text)["releases"]
    return sorted(releases, key=parse_version, reverse=True)[0]


def pathsafe(path: str) -> str:
    """Makes path safe/allowed

    Args:
        path(str)

    Returns:
        str
    """
    return "".join(c for c in path if c.isalnum() or c in [" "]).rstrip()


def cloudscraper_check():
    import cloudscraper

    latest_version = get_latest_version("cloudscraper")
    installed_version = cloudscraper.__version__
    if installed_version == latest_version:
        pass
    else:
        # TODO: print --> logging.warn
        print(
            f"Warning: Latest version of cloudscraper is {latest_version} but installed version is {installed_version}"
        )
