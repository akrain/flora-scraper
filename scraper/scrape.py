import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import csv
from models import Flower
import re

BASE_URL = "https://www.flowersofindia.net/"
FLOWER_LIST_URL = BASE_URL + "hwf/botanical.html"


def extract_relative_url(js_string):
    """
    Extracts the relative URL from href="javascript:showFlower('/some/path.htm')"
    """
    m = re.search(r"javascript:popup\(\"\.\./(.*?)\"\)", js_string)
    return m.group(1) if m else None


def scrape_flower_links():
    """
    Scrapes the main page and returns a list of Flower objects.
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
                flowers.append(Flower(botanical_name=botanical, family=family, url=full_url, common_name=common_name,
                                      description=""))

    print(f"Found {len(flowers)} flowers.")
    return flowers


def scrape_flower_page(flower: Flower) -> Flower:
    """
    Given a Flower object, fetches the flower page content
    and extracts additional information, returning a new Flower object.
    """
    try:
        resp = requests.get(flower.url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        description = ""
        desc_elem = soup.find("div", {"id": "descr"})
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        flower.description = description
    except Exception as e:
        print(f"Error scraping {flower.url}: {e}")
    return flower

def main():
    flowers = scrape_flower_links()[:10]
    results = []

    for i, flower in enumerate(flowers,):
        print(f"[{i + 1}/{len(flowers)}] Scraping {flower.botanical_name} ...")
        data = scrape_flower_page(flower)
        results.append(data)
        time.sleep(1)  # be polite and avoid hammering the server

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
