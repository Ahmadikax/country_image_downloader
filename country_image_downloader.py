#!/usr/bin/env python3
"""
Country Image Downloader

This script downloads high-quality images of countries using Selenium WebDriver
to automate a real browser. It reads country names from a text file and downloads
images for each country, saving them to an 'images' directory.

Usage:
    python country_image_downloader.py
    python country_image_downloader.py --headless
    python country_image_downloader.py --help
"""

import os
import sys
import re
import time
import json
import argparse
import logging
import urllib.parse
import urllib.request
import zipfile
import random
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set

try:
    import requests
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, WebDriverException,
        ElementNotInteractableException, StaleElementReferenceException
    )
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    from PIL import Image
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Required package not found: {e.name}")
    print("Please install the required packages using: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("country_image_downloader.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CountryImageDownloader:
    """
    A class to download high-quality images of countries using Selenium WebDriver.
    """
    
    def __init__(self, options: argparse.Namespace):
        """
        Initialize the downloader with the given options.
        
        Args:
            options: Command-line arguments parsed by argparse
        """
        self.options = options
        self.driver = None
        self.base_output_dir = Path(options.output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging level
        if options.debug:
            logger.setLevel(logging.DEBUG)
            # Also set the root logger to DEBUG
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info(f"Country Image Downloader v1.0.0")
        logger.info(f"Output directory: {self.base_output_dir}")
        
        # Initialize the WebDriver
        self._init_webdriver()
    
    def _init_webdriver(self):
        """Initialize the WebDriver based on the selected browser."""
        browser = self.options.browser.lower()
        
        try:
            if browser == "chrome":
                logger.info("Initializing Chrome WebDriver...")
                options = ChromeOptions()
                
                if self.options.headless:
                    options.add_argument("--headless=new")
                
                # Common Chrome options for better performance and stability
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-notifications")
                options.add_argument("--disable-infobars")
                options.add_argument("--disable-extensions")
                
                # Set user agent to avoid detection
                options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
                
                # Initialize Chrome WebDriver
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                
            elif browser == "firefox":
                logger.info("Initializing Firefox WebDriver...")
                options = FirefoxOptions()
                
                if self.options.headless:
                    options.add_argument("--headless")
                
                # Common Firefox options
                options.add_argument("--width=1920")
                options.add_argument("--height=1080")
                
                # Initialize Firefox WebDriver
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=options)
                
            else:
                logger.error(f"Unsupported browser: {browser}")
                raise ValueError(f"Unsupported browser: {browser}")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(self.options.timeout)
            
            logger.info(f"WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise
    
    def download_images_for_country(self, country_name: str, country_id: str) -> int:
        """
        Download images for the given country.
        
        Args:
            country_name: The name of the country
            country_id: The ID of the country
            
        Returns:
            The number of images downloaded
        """
        logger.info(f"Downloading images for country: {country_name} (ID: {country_id})")
        
        # Create a search URL for the country
        search_url = self._create_search_url(country_name)
        
        # Create output directory for this country
        output_dir = self.base_output_dir / f"{country_id}_{self._sanitize_filename(country_name)}"
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Images will be saved to: {output_dir}")
        
        try:
            # Load the search page
            logger.info(f"Loading search page for {country_name}...")
            self.driver.get(search_url)
            
            # Wait for the page to load
            logger.info(f"Waiting for page to load...")
            self._wait_for_page_load()
            
            # Extract images using multiple methods
            logger.info(f"Extracting images...")
            image_urls = set()
            
            # Method 1: Extract images from the search results
            logger.info(f"Method 1: Extracting images from search results...")
            search_results_images = self._extract_images_from_search_results()
            image_urls.update(search_results_images)
            logger.info(f"Found {len(search_results_images)} images in search results")
            
            # Method 2: Extract images from the page content
            logger.info(f"Method 2: Extracting images from page content...")
            page_content_images = self._extract_images_from_page_content()
            image_urls.update(page_content_images)
            logger.info(f"Found {len(page_content_images)} images in page content")
            
            # Method 3: Extract images from JSON-LD data
            logger.info(f"Method 3: Extracting images from JSON-LD data...")
            jsonld_images = self._extract_images_from_jsonld()
            image_urls.update(jsonld_images)
            logger.info(f"Found {len(jsonld_images)} images in JSON-LD data")
            
            # Method 4: Extract images from embedded JSON data
            logger.info(f"Method 4: Extracting images from embedded JSON data...")
            embedded_json_images = self._extract_images_from_embedded_json()
            image_urls.update(embedded_json_images)
            logger.info(f"Found {len(embedded_json_images)} images in embedded JSON data")
            
            # Filter and limit the number of images
            image_urls = self._filter_image_urls(image_urls)
            if self.options.max_images > 0 and len(image_urls) > self.options.max_images:
                logger.info(f"Limiting to {self.options.max_images} images")
                image_urls = list(image_urls)[:self.options.max_images]
            
            # Download the images
            logger.info(f"Downloading {len(image_urls)} images...")
            downloaded_images = self._download_images(image_urls, output_dir, country_id, country_name)
            
            # Create a ZIP file if requested
            if not self.options.no_zip:
                logger.info(f"Creating ZIP file...")
                zip_path = self._create_zip_file(output_dir, f"{country_id}_{country_name}")
                logger.info(f"ZIP file created: {zip_path}")
                
                # Remove individual images if requested
                if self.options.zip_only:
                    logger.info(f"Removing individual image files...")
                    for image_path in downloaded_images:
                        os.remove(image_path)
            
            logger.info(f"Download completed. {len(downloaded_images)} images downloaded for {country_name}.")
            return len(downloaded_images)
            
        except Exception as e:
            logger.error(f"Error downloading images for {country_name}: {str(e)}")
            logger.debug("Exception details:", exc_info=True)
            return 0
    
    def _create_search_url(self, country_name: str) -> str:
        """
        Create a Google search URL for the country.
        
        Args:
            country_name: The name of the country
            
        Returns:
            The search URL
        """
        # Use only the country name for the search query
        query = country_name
        
        # Encode the query for URL
        encoded_query = urllib.parse.quote(query)
        
        # Create the search URL
        search_url = f"https://www.google.com/search?q={encoded_query}&tbm=isch&tbs=isz:l"
        
        logger.debug(f"Created search URL: {search_url}")
        return search_url
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string to be used as a filename or folder name.
        
        Args:
            name: The string to sanitize
            
        Returns:
            A sanitized string suitable for filenames
        """
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[\\/*?:"<>|]', "_", name)
        # Replace multiple spaces with a single space
        sanitized = re.sub(r'\s+', " ", sanitized)
        # Trim to a reasonable length
        if len(sanitized) > 50:
            sanitized = sanitized[:47] + "..."
        # Ensure it's not empty
        if not sanitized or sanitized.isspace():
            sanitized = "unnamed_country"
        return sanitized.strip()
    
    def _wait_for_page_load(self):
        """Wait for the page to load completely."""
        try:
            # Wait for images to be visible
            WebDriverWait(self.driver, self.options.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img"))
            )
            
            # Wait a bit more for dynamic content
            time.sleep(2)
            
            # Scroll down to load more content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            
            logger.debug("Page loaded successfully")
            
        except TimeoutException:
            logger.warning("Timeout waiting for page to load")
        except Exception as e:
            logger.warning(f"Error waiting for page to load: {str(e)}")
    
    def _extract_images_from_search_results(self) -> Set[str]:
        """
        Extract images from the Google image search results.
        
        Returns:
            A set of image URLs
        """
        image_urls = set()
        
        try:
            # Find all image elements in the search results
            image_elements = self.driver.find_elements(By.CSS_SELECTOR, "img.rg_i, img.Q4LuWd")
            
            logger.debug(f"Found {len(image_elements)} image elements in search results")
            
            # Click on some images to load higher resolution versions
            for i, img in enumerate(image_elements[:min(10, len(image_elements))]):
                try:
                    # Try to click the image to open the larger version
                    logger.debug(f"Clicking on image {i+1}...")
                    img.click()
                    
                    # Wait for the larger image to load
                    time.sleep(1)
                    
                    # Try to find the larger image
                    large_images = self.driver.find_elements(By.CSS_SELECTOR, "img.r48jcc, img.n3VNCb, img.KAlRDb")
                    for large_img in large_images:
                        src = large_img.get_attribute("src")
                        if src and "http" in src and not any(x in src for x in ["data:image", "gstatic.com", "googleusercontent.com/gadgets"]):
                            # Get the highest resolution version
                            high_res_src = self._get_high_res_image_url(src)
                            image_urls.add(high_res_src)
                            logger.debug(f"Found large image: {high_res_src}")
                    
                    # Close the image viewer if it's open
                    close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Close'], a.hm60ue")
                    if close_buttons:
                        close_buttons[0].click()
                        time.sleep(0.5)
                    
                except (ElementNotInteractableException, StaleElementReferenceException):
                    continue
                except Exception as e:
                    logger.debug(f"Error clicking on image: {str(e)}")
                    continue
            
            # Also collect all image sources directly from the search results
            for img in image_elements:
                try:
                    src = img.get_attribute("src")
                    if src and "http" in src and not any(x in src for x in ["data:image", "gstatic.com", "googleusercontent.com/gadgets"]):
                        # Get the highest resolution version
                        high_res_src = self._get_high_res_image_url(src)
                        image_urls.add(high_res_src)
                        logger.debug(f"Found image in search results: {high_res_src}")
                except (StaleElementReferenceException, WebDriverException):
                    continue
                except Exception as e:
                    logger.debug(f"Error processing image: {str(e)}")
                    continue
            
        except Exception as e:
            logger.warning(f"Error extracting images from search results: {str(e)}")
        
        return image_urls
    
    def _extract_images_from_page_content(self) -> Set[str]:
        """
        Extract images from the main page content.
        
        Returns:
            A set of image URLs
        """
        image_urls = set()
        
        try:
            # Find all images on the page
            images = self.driver.find_elements(By.TAG_NAME, "img")
            
            for img in images:
                try:
                    src = img.get_attribute("src")
                    if not src:
                        continue
                    
                    # Skip small icons, maps, and other non-photo images
                    if any(x in src for x in ["maps.googleapis.com", "maps.gstatic.com", "googleusercontent.com/gadgets"]):
                        continue
                    
                    # Skip very small images (likely icons)
                    width = img.get_attribute("width")
                    height = img.get_attribute("height")
                    if width and height:
                        try:
                            if int(width) < 100 or int(height) < 100:
                                continue
                        except ValueError:
                            pass
                    
                    # Get the highest resolution version
                    high_res_src = self._get_high_res_image_url(src)
                    image_urls.add(high_res_src)
                    logger.debug(f"Found image in page content: {high_res_src}")
                    
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    logger.debug(f"Error processing image: {str(e)}")
            
        except Exception as e:
            logger.warning(f"Error extracting images from page content: {str(e)}")
        
        return image_urls
    
    def _extract_images_from_jsonld(self) -> Set[str]:
        """
        Extract images from JSON-LD data in the page.
        
        Returns:
            A set of image URLs
        """
        image_urls = set()
        
        try:
            # Find JSON-LD script tags
            script_elements = self.driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
            
            for script in script_elements:
                try:
                    json_text = script.get_attribute("innerHTML")
                    if not json_text:
                        continue
                    
                    json_data = json.loads(json_text)
                    
                    # Extract image URLs from the JSON-LD data
                    self._extract_images_from_json_object(json_data, image_urls)
                    
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.debug(f"Error processing JSON-LD: {str(e)}")
            
        except Exception as e:
            logger.warning(f"Error extracting images from JSON-LD: {str(e)}")
        
        return image_urls
    
    def _extract_images_from_embedded_json(self) -> Set[str]:
        """
        Extract images from embedded JSON data in the page.
        
        Returns:
            A set of image URLs
        """
        image_urls = set()
        
        try:
            # Get the page source
            page_source = self.driver.page_source
            
            # Look for JSON data in the page source
            json_matches = re.findall(r'(\{.*?"images":\s*\[.*?\].*?\})', page_source)
            
            for json_text in json_matches:
                try:
                    # Try to parse the JSON
                    json_data = json.loads(json_text)
                    
                    # Extract image URLs from the JSON data
                    self._extract_images_from_json_object(json_data, image_urls)
                    
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.debug(f"Error processing embedded JSON: {str(e)}")
            
            # Look for image URLs in the page source
            img_matches = re.findall(r'(https://[^"\']+\.(jpg|jpeg|png|webp))', page_source)
            
            for img_match in img_matches:
                url = img_match[0]
                # Skip small icons, maps, and other non-photo images
                if any(x in url for x in ["maps.googleapis.com", "maps.gstatic.com", "googleusercontent.com/gadgets"]):
                    continue
                
                # Get the highest resolution version
                high_res_url = self._get_high_res_image_url(url)
                image_urls.add(high_res_url)
                logger.debug(f"Found image URL in page source: {high_res_url}")
            
        except Exception as e:
            logger.warning(f"Error extracting images from embedded JSON: {str(e)}")
        
        return image_urls
    
    def _extract_images_from_json_object(self, json_data: Any, image_urls: Set[str]):
        """
        Extract image URLs from a JSON object.
        
        Args:
            json_data: The JSON object to extract images from
            image_urls: A set to add the extracted image URLs to
        """
        if isinstance(json_data, dict):
            # Check for image or photo properties
            for key in ["image", "images", "photo", "photos", "thumbnail", "thumbnailUrl", "contentUrl"]:
                if key in json_data:
                    value = json_data[key]
                    
                    if isinstance(value, str) and (value.startswith("http") and any(ext in value.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"])):
                        # Get the highest resolution version
                        high_res_url = self._get_high_res_image_url(value)
                        image_urls.add(high_res_url)
                        logger.debug(f"Found image URL in JSON: {high_res_url}")
                    
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and (item.startswith("http") and any(ext in item.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"])):
                                # Get the highest resolution version
                                high_res_url = self._get_high_res_image_url(item)
                                image_urls.add(high_res_url)
                                logger.debug(f"Found image URL in JSON array: {high_res_url}")
                            elif isinstance(item, dict):
                                self._extract_images_from_json_object(item, image_urls)
                    
                    elif isinstance(value, dict):
                        self._extract_images_from_json_object(value, image_urls)
            
            # Recursively process all properties
            for value in json_data.values():
                if isinstance(value, (dict, list)):
                    self._extract_images_from_json_object(value, image_urls)
        
        elif isinstance(json_data, list):
            for item in json_data:
                self._extract_images_from_json_object(item, image_urls)
    
    def _get_high_res_image_url(self, url: str) -> str:
        """
        Get the highest resolution version of an image URL.
        
        Args:
            url: The original image URL
            
        Returns:
            The highest resolution version of the URL
        """
        # Google often uses parameters like =w100-h100 to specify image dimensions
        # Remove or increase these parameters to get higher resolution
        
        # Check if it's a Google photo URL
        if "googleusercontent.com" in url and ("=w" in url or "=s" in url or "=h" in url):
            # Extract the base URL without size parameters
            base_url = url.split("=")[0]
            
            # Add a large size parameter
            high_res_url = f"{base_url}=w2048-h2048"
            return high_res_url
        
        return url
    
    def _filter_image_urls(self, urls: Set[str]) -> Set[str]:
        """
        Filter and deduplicate image URLs.
        
        Args:
            urls: A set of image URLs
            
        Returns:
            A filtered set of image URLs
        """
        filtered_urls = set()
        
        for url in urls:
            # Skip very small images and icons
            if "=w" in url and "=h" in url:
                try:
                    width_match = re.search(r"=w(\d+)", url)
                    height_match = re.search(r"=h(\d+)", url)
                    
                    if width_match and height_match:
                        width = int(width_match.group(1))
                        height = int(height_match.group(1))
                        
                        if width < 100 or height < 100:
                            continue
                except Exception:
                    pass
            
            # Skip Google icons and thumbnails
            if any(x in url for x in [
                "maps.googleapis.com",
                "maps.gstatic.com",
                "googleusercontent.com/gadgets",
                "google.com/images",
                "gstatic.com/images"
            ]):
                continue
            
            # Skip non-image URLs
            if not any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]) and not "=w" in url and not "=h" in url:
                continue
            
            filtered_urls.add(url)
        
        return filtered_urls
    
    def _download_images(self, urls: Set[str], output_dir: Path, country_id: str, country_name: str) -> List[str]:
        """
        Download images from the given URLs.
        
        Args:
            urls: A set of image URLs
            output_dir: The directory to save the images to
            country_id: The ID of the country
            country_name: The name of the country
            
        Returns:
            A list of paths to the downloaded images
        """
        downloaded_images = []
        
        # Create a progress bar
        with tqdm(total=len(urls), desc=f"Downloading images for {country_name}", unit="img") as pbar:
            for i, url in enumerate(urls):
                try:
                    # Generate a filename
                    filename = f"{country_id}_{self._sanitize_filename(country_name)}_{i+1:03d}.jpg"
                    output_path = output_dir / filename
                    
                    # Download the image
                    response = requests.get(url, stream=True, timeout=10)
                    response.raise_for_status()
                    
                    # Check if it's actually an image
                    content_type = response.headers.get("Content-Type", "")
                    if not content_type.startswith("image/"):
                        logger.debug(f"Skipping non-image URL: {url} (Content-Type: {content_type})")
                        continue
                    
                    # Save the image
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Verify the image
                    try:
                        with Image.open(output_path) as img:
                            # Get the actual image format
                            img_format = img.format.lower() if img.format else "jpeg"
                            
                            # If the format is not JPEG, convert and save with the correct extension
                            if img_format != "jpeg":
                                new_filename = f"{country_id}_{self._sanitize_filename(country_name)}_{i+1:03d}.{img_format.lower()}"
                                new_output_path = output_dir / new_filename
                                img.save(new_output_path)
                                os.remove(output_path)
                                output_path = new_output_path
                            
                            # Skip very small images
                            width, height = img.size
                            if width < 100 or height < 100:
                                os.remove(output_path)
                                logger.debug(f"Skipping small image: {url} ({width}x{height})")
                                continue
                    except Exception as e:
                        logger.debug(f"Error verifying image: {str(e)}")
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        continue
                    
                    # Add to the list of downloaded images
                    downloaded_images.append(str(output_path))
                    logger.debug(f"Downloaded image: {url} -> {output_path}")
                    
                except Exception as e:
                    logger.debug(f"Error downloading image: {str(e)}")
                
                # Update the progress bar
                pbar.update(1)
        
        logger.info(f"Downloaded {len(downloaded_images)} images for {country_name} to {output_dir}")
        return downloaded_images
    
    def _create_zip_file(self, image_dir: Path, country_name: str) -> str:
        """
        Create a ZIP file containing all images in the given directory.
        
        Args:
            image_dir: The directory containing the images
            country_name: The name of the country (used for the ZIP filename)
            
        Returns:
            The path to the created ZIP file
        """
        # Create the ZIP filename
        zip_filename = f"{country_name}_images.zip"
        zip_path = self.base_output_dir / zip_filename
        
        # Create the ZIP file
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in image_dir.glob("*.*"):
                if file.is_file() and file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                    zipf.write(file, arcname=file.name)
        
        return str(zip_path)
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {str(e)}")

def get_countries_from_file(file_path: str) -> List[Dict[str, str]]:
    """
    Read country names from the country_list.txt file.
    
    Args:
        file_path: Path to the country list file
        
    Returns:
        A list of dictionaries containing country IDs and names
    """
    countries = []
    
    try:
        logger.info(f"Reading country list from file: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"Country list file not found: {file_path}")
            return []
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        logger.info(f"Found {len(lines)} lines in the country list file.")
        
        # Process each line
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse the line (expected format: "ID: Country Name")
            parts = line.split(':', 1)
            if len(parts) == 2:
                country_id = parts[0].strip()
                country_name = parts[1].strip()
                
                countries.append({
                    'id': country_id,
                    'name': country_name
                })
                logger.debug(f"Processed country: ID={country_id}, Name={country_name}")
            else:
                logger.warning(f"Could not parse line: {line}")
        
        logger.info(f"Processed {len(countries)} countries from the file.")
        return countries
        
    except Exception as e:
        logger.error(f"Error reading country list file: {str(e)}")
        logger.debug("Exception details:", exc_info=True)
        return []

def main():
    """Main function to run the country image downloader."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Download high-quality images of countries using Selenium WebDriver")
    
    # Input/output options
    parser.add_argument("--country-list", type=str, default="country_list.txt",
                        help="Path to the country list file (default: country_list.txt)")
    parser.add_argument("--output-dir", type=str, default="images",
                        help="Path to the output directory (default: images)")
    
    # Browser options
    parser.add_argument("--browser", type=str, default="chrome", choices=["chrome", "firefox"],
                        help="Browser to use for downloading images (default: chrome)")
    parser.add_argument("--headless", action="store_true",
                        help="Run the browser in headless mode")
    
    # Download options
    parser.add_argument("--max-images", type=int, default=10,
                        help="Maximum number of images to download per country (default: 10, 0 for no limit)")
    parser.add_argument("--timeout", type=int, default=30,
                        help="Timeout for page loading in seconds (default: 30)")
    parser.add_argument("--no-zip", action="store_true",
                        help="Do not create ZIP files for each country")
    parser.add_argument("--zip-only", action="store_true",
                        help="Create ZIP files and remove individual image files")
    
    # Country selection options
    parser.add_argument("--country-id", type=str,
                        help="Download images for a specific country ID")
    parser.add_argument("--country-name", type=str,
                        help="Download images for a specific country name")
    
    # Debug options
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if both country ID and name are specified
    if args.country_id and args.country_name:
        logger.error("Cannot specify both --country-id and --country-name")
        sys.exit(1)
    
    try:
        # Initialize the downloader
        downloader = CountryImageDownloader(args)
        
        # Get the list of countries
        if args.country_id or args.country_name:
            # Download images for a specific country
            if args.country_id:
                countries = [{'id': args.country_id, 'name': args.country_name or args.country_id}]
            else:
                countries = [{'id': args.country_name, 'name': args.country_name}]
        else:
            # Download images for all countries in the list
            countries = get_countries_from_file(args.country_list)
        
        if not countries:
            logger.error("No countries found to process")
            sys.exit(1)
        
        logger.info(f"Found {len(countries)} countries to process")
        
        # Download images for each country
        total_images = 0
        for country in countries:
            country_id = country['id']
            country_name = country['name']
            
            # Download images for the country
            num_images = downloader.download_images_for_country(country_name, country_id)
            total_images += num_images
        
        logger.info(f"Download completed. Total images downloaded: {total_images}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.debug("Exception details:", exc_info=True)
        sys.exit(1)
    finally:
        # Close the WebDriver
        if 'downloader' in locals() and downloader:
            downloader.close()

if __name__ == "__main__":
    main()