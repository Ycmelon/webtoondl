# Webtoondl
Webtoondl is a Python script for Webtoon downloading.

## Usage
download(title_no, download_range, output="combined", clean=False, unique=False):
```python
import webtoondl
webtoondl.download(title_no=70280, download_range=range(1, 132), output="combined")
	# title_no: Webtoon ID
	# download_range: Episodes to download
	# output: Output format (combined, separate, images)
```

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
[GNU General Public License v3.0](https://choosealicense.com/licenses/gpl-3.0/)
