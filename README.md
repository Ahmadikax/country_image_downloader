# Country Image Downloader

This tool downloads high-quality images of countries using Selenium WebDriver to automate a real browser. It reads country names from a text file and downloads images for each country, saving them to an output directory.

## Features

- Downloads high-quality country images from Google Images
- Uses multiple extraction methods to maximize results
- Filters images by size and quality
- Creates ZIP files for easy distribution
- Supports both Chrome and Firefox browsers
- Headless mode for server environments
- Detailed logging for troubleshooting

## Requirements

- Python 3.6 or higher
- Chrome or Firefox browser installed
- Required Python packages (see requirements.txt)

## Installation

1. Clone or download this repository
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

To download images for all countries in the country_list.txt file:

```bash
python country_image_downloader.py
```

### Command-line Options

```
usage: country_image_downloader.py [-h] [--country-list COUNTRY_LIST]
                                  [--output-dir OUTPUT_DIR]
                                  [--browser {chrome,firefox}] [--headless]
                                  [--max-images MAX_IMAGES]
                                  [--timeout TIMEOUT] [--no-zip]
                                  [--zip-only] [--country-id COUNTRY_ID]
                                  [--country-name COUNTRY_NAME] [--debug]
```

#### Input/Output Options

- `--country-list`: Path to the country list file (default: country_list.txt)
- `--output-dir`: Path to the output directory (default: images)

#### Browser Options

- `--browser`: Browser to use for downloading images (choices: chrome, firefox; default: chrome)
- `--headless`: Run the browser in headless mode

#### Download Options

- `--max-images`: Maximum number of images to download per country (default: 10, 0 for no limit)
- `--timeout`: Timeout for page loading in seconds (default: 30)
- `--no-zip`: Do not create ZIP files for each country
- `--zip-only`: Create ZIP files and remove individual image files

#### Country Selection Options

- `--country-id`: Download images for a specific country ID
- `--country-name`: Download images for a specific country name

#### Debug Options

- `--debug`: Enable debug logging

### Country List Format

The country list file should contain one country per line in the format:

```
ID: Country Name
```

Example:
```
1: United States
2: United Kingdom
3: France
```

## Examples

Download images for all countries using Chrome in headless mode:

```bash
python country_image_downloader.py --headless
```

Download images for a specific country:

```bash
python country_image_downloader.py --country-name "Japan"
```

Download up to 20 images per country and save to a custom directory:

```bash
python country_image_downloader.py --max-images 20 --output-dir "my_country_images"
```

## Troubleshooting

If you encounter issues:

1. Enable debug logging with the `--debug` flag
2. Check the country_image_downloader.log file for detailed error messages
3. Make sure your browser is up to date
4. Try increasing the timeout value if pages are loading slowly

## License

This project is open source and available under the MIT License.