# flora-scraper

A Python web scraper for extracting flower information from flowersofindia.net.

## Features

- Scrapes botanical name, family, common name, and description for flowers
- Extracts multiple image URLs for each flower
- Exports data to CSV format

## Usage

```bash
python scraper/scrape.py
```

The scraper will:
1. Fetch the flower listing page
2. Extract details for each flower including images
3. Save results to `flowers.csv`

## Requirements

- Python 3.7+
- requests
- beautifulsoup4