import csv
import requests
from bs4 import BeautifulSoup
from time import sleep
from typing import List, Dict, Optional

BASE_URL = "https://quotes.toscrape.com"


def get_page_soup(url: str) -> BeautifulSoup:
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def parse_quotes_from_soup(soup: BeautifulSoup) -> List[Dict[str, str]]:
    quotes_data = []
    quote_blocks = soup.select("div.quote")
    for quote in quote_blocks:
        text = quote.select_one("span.text").get_text(strip=True)
        author = quote.select_one("small.author").get_text(strip=True)
        author_link = (
            BASE_URL + quote.select_one("span a")["href"]
        )
        tags = [
            tag.get_text(strip=True)
            for tag in quote.select("div.tags a.tag")
        ]
        quotes_data.append({
            "text": text,
            "author": author,
            "author_link": author_link,
            "tags": ", ".join(tags),
        })
    return quotes_data


def get_next_page_url(soup: BeautifulSoup) -> Optional[str]:
    next_button = soup.select_one("li.next > a")
    if next_button:
        return BASE_URL + next_button["href"]
    return None


def get_author_bio(
    author_url: str,
    cache: Dict[str, str]
) -> str:
    if author_url in cache:
        return cache[author_url]
    soup = get_page_soup(author_url)
    bio = soup.select_one("div.author-description").get_text(strip=True)
    cache[author_url] = bio
    sleep(1)  # пауза, щоб не навантажувати сервер
    return bio


def main(
    output_quotes_csv_path: str,
    output_authors_csv_path: str
) -> None:
    url = BASE_URL
    all_quotes: List[Dict[str, str]] = []
    authors_bio_cache: Dict[str, str] = {}

    while url:
        print(f"Parsing page: {url}")
        soup = get_page_soup(url)
        quotes = parse_quotes_from_soup(soup)
        all_quotes.extend(quotes)
        url = get_next_page_url(soup)
        sleep(1)  # пауза між запитами

    unique_authors = {}
    for quote in all_quotes:
        if quote["author"] not in unique_authors:
            unique_authors[quote["author"]] = quote["author_link"]

    authors_data = []
    for author, link in unique_authors.items():
        bio = get_author_bio(link, authors_bio_cache)
        authors_data.append({
            "author": author,
            "bio": bio,
        })

    with open(
            output_quotes_csv_path, "w", newline="", encoding="utf-8"
    ) as csvfile:
        fieldnames = ["text", "author", "tags"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for quote in all_quotes:
            writer.writerow({
                "text": quote["text"],
                "author": quote["author"],
                "tags": quote["tags"],
            })

    with open(
            output_authors_csv_path, "w", newline="", encoding="utf-8"
    ) as csvfile:
        fieldnames = ["author", "bio"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for author in authors_data:
            writer.writerow(author)


if __name__ == "__main__":
    main("quotes.csv", "authors.csv")
