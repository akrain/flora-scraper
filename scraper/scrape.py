from operator import contains

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import csv
from models import Flower
import re

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
    urls = []
    for match in matches:
        filename = match[0]
        if EXTRAPICS in filename:
            urls.append(BASE_URL + filename)
        else:
            urls.append(BASE_URL + SLIDE_PATH + filename)
    return urls


def construct_image_urls(matches: list, flower: Flower) -> list :
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
        resp = requests.get(flower.url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        desc_elem = soup.find("div", {"id": "descr"})
        flower.description = desc_elem.get_text(strip=True) if desc_elem is not None else None
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

    for i, flower in enumerate(flowers,):
        print(f"[{i + 1}/{len(flowers)}] Scraping {flower.botanical_name} ...")
        add_more_details(flower)
        time.sleep(1)  # Be polite. Sleep few secs between requests

    save_results(flowers)


def copy_details(details, flower):
    flower.description = details


def save_results(results):
    # Save results to CSV
    with open("flowers_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["botanical_name", "common_name", "url", "description"])
        writer.writeheader()
        for flower in results:
            writer.writerow({
                "botanical_name": flower.botanical_name,
                "common_name": flower.common_name,
                "url": flower.url,
                "description": flower.description
            })
    print("Scraping complete. Data saved to flowers_dataset.csv.")


if __name__ == "__main__":
    main()
