import os
import logging
from importlib import import_module

import click

# Sources
import output
import downloader
import sources

import utils

sources_list = sources.__all__
# Logging (WIP)
# log_format = "%(asctime)s::%(levelname)s::%(lineno)d::%(message)s"


# Utilities
def is_int(input):
    try:
        int(input)
        return True
    except ValueError:
        return False


# CLI commands
@click.group()
def cli():
    pass


@click.command()
@click.argument("source")
@click.argument("series")
@click.option("--output_format", help="Format to output in", default="combined")
@click.option("--output_folder", help="Downloads folder.", default="./downloads")
@click.option("--range_start", help="Start of range of chapters to download.", default="start")
@click.option(
    "--range_end", help="End of range of chapters to download (inclusive).", default="end"
)
def download(source, series, output_format, output_folder, range_start, range_end):
    # Input validation
    if source == "mangago":
        utils.cloudscraper_check()
        source_class = sources.Mangago()
    elif source == "webtoon":
        source_class = sources.Webtoon()
    else:
        raise ValueError(f'Unrecognised source "{source}"')

    if not source_class.is_series(series):
        raise ValueError(f'Unrecognised series "{series}"')
    if range_start != "start":
        if not is_int(range_start):
            raise TypeError("Range values must be int")
    if range_end != "end":
        if not is_int(range_end):
            raise TypeError("Range values must be int")
    if range_start != "start" and range_end != "end":
        if int(range_start) > int(range_end):
            raise ValueError("Invalid range")

    # Paths
    project_name = f"{source} {series} "
    if range_start == "start":
        range_start = 1
    if range_end == "end":
        range_end = source_class.get_length(series)

    range_ = range(int(range_start), int(range_end) + 1)  # Inclusive
    project_name += f"{range_[0]}-{range_[-1]}"
    project_path = os.path.join(output_folder, project_name)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    # logging.info("Paths created!")

    # Downloading
    source_class.get_url(series=series, range_=range_, project_path=project_path)
    downloader.download(
        project_path=project_path,
        request_headers=source_class.get_request_headers(series),
        file_format=source_class.get_file_format(project_path),
    )
    output.output(
        project_name=project_name,
        project_path=project_path,
        output_folder=output_folder,
        output_format=output_format,
        file_format=source_class.get_file_format(project_path),
    )


cli.add_command(download)

if __name__ == "__main__":
    cli()
