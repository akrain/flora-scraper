import csv
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from models import Flower

BASE_URL = "https://www.flowersofindia.net/"
FLOWER_LIST_URL = BASE_URL + "hwf/botanical.html"
SLIDE_PATH = "catalog/slides/"
EXTRAPICS = "extrapics/"
IMAGE_URL_TEXT = """<!-- Begin
 NewImg = new Array ("""

def extract_relative_url(href_js):
    """
    Extracts the relative URL from href="javascript:showFlower('/some/path.htm')"
    """
    m = re.search(r"javascript:popup\(\"\.\./(.*?)\"\)", href_js)
    return m.group(1) if m else None


def scrape_flower_links():
    """
    Scrapes the listing page and returns a list of Flower objects.
    """
    resp = requests.get(FLOWER_LIST_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    flowers = []
    for row in soup.select("table tr"):
        cells = row.find_all('td')
        botanical = cells[0].get_text(strip=True)
        family = cells[2].get_text(strip=True)
        a = row.find("a", href=True)
        if a:
            href_js = a['href']
            rel_url = extract_relative_url(href_js)
            if rel_url:
                full_url = urljoin(BASE_URL, rel_url)
                common_name = a.get_text(strip=True)
                flowers.append(Flower(botanical, family, full_url, common_name))

    print(f"Found {len(flowers)} flowers.")
    return flowers


def extract_image_names(soup) -> list | None:
    script_tags = soup.head.find_all("script")
    for script in script_tags:
        script_text = script.get_text(strip=True)
        if IMAGE_URL_TEXT in script_text:
            matches = re.findall(r"(([a-z]*/)?[A-Za-z0-9\- ']*\.jpg)", script_text)
            print(matches)
            return matches if matches else None
    return None


def construct_default_url(flower: Flower):
    """
    If slideshow is not present, then assume there is  a single image whose name
    can be constructed from the common name of the flower
    """
    return [BASE_URL + SLIDE_PATH + flower.common_name + ".jpg"]


def construct_all(matches):
    """
    There can be two types of image paths. Construct the full Url based on the
    type of Url present
    """
    urls = []
    for match in matches:
        filename = match[0]
        if EXTRAPICS in filename:
            urls.append(BASE_URL + filename)
        else:
            urls.append(BASE_URL + SLIDE_PATH + filename)
    return urls


def construct_image_urls(matches: list, flower: Flower) -> list :
    """
    Image Urls are present in the script tag only when there is more than 1 image.
    If not present, we can still construct 1 URl by convention
    """
    if matches:
        return construct_all(matches)
    else:
        return construct_default_url(flower)


def add_more_details(flower: Flower):
    """
    Given a Flower object, fetches the flower page content
    and adds the flower description and image urls from there.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Host': 'www.flowersofindia.net',
        }
        resp = requests.get(flower.url, headers=headers, timeout=30)
        resp.raise_for_status()
        ascii_text = resp.text.encode('ascii', errors='ignore').decode('ascii')
        soup = BeautifulSoup(ascii_text, "html.parser")
        desc_elem = soup.find("div", {"id": "descr"})
        if desc_elem is None:
            desc_elem = soup.find("div", {"align": "justify"})
        flower.description = desc_elem.get_text(strip=True)
        image_urls = construct_image_urls(extract_image_names(soup), flower)
        # At least 1 image url should always exist
        flower.image1_url = image_urls[0]
        flower.image2_url = image_urls[1] if len(image_urls) > 1 else None
        flower.image3_url = image_urls[2] if len(image_urls) > 2 else None
        flower.image4_url = image_urls[3] if len(image_urls) > 3 else None

    except Exception as e:
        print(f"Error scraping {flower.url}: {e}")


def main():
    flowers = scrape_flower_links()

    for i, flower in enumerate(flowers):
        print(f"[{i + 1}/{len(flowers)}] Scraping {flower.botanical_name} ...")
        add_more_details(flower)
        time.sleep(1)  # Be polite. Sleep some time between requests

    save_results(flowers)


def copy_details(details, flower):
    flower.description = details


def save_results(results):
    if not results:
        return
    # Save results to CSV
    with open("../data/foi_himalayan_flowers.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = list(vars(results[0]).keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for flower in results:
            writer.writerow(vars(flower))
    print("Scraping complete. Data saved to foi_himalayan_flowers.csv.")


if __name__ == "__main__":
    main()
