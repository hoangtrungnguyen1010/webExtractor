from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def fetch_and_parse(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        # Retrieve the page content
        html_content = page.content()
        # Parse the HTML content with Beautiful Soup
        soup = BeautifulSoup(html_content, 'html.parser')
        browser.close()
        return soup
