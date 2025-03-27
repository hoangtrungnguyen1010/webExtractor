import time
import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from googlesearch import search

class WebScraper:
    def __init__(self, headless=False, user_agent=None):
        self.headless = headless
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.driver = None

    def _create_driver(self):
        # Create a temporary directory for Firefox profile
        profile_dir = tempfile.mkdtemp()

        # Set up Firefox options
        options = Options()
        options.headless = self.headless  # Run Firefox in headless mode
        options.add_argument('--width=10')  # Set window width
        options.add_argument('--height=10')  # Set window height
        options.add_argument('-profile')
        options.add_argument(profile_dir)  # Point to the temporary profile
        options.set_preference("general.useragent.override", self.user_agent)

        # Initialize the WebDriver with the options
        self.driver = webdriver.Firefox(options=options)

    def perform_google_search(self, query, num_results=10):
        try:
            # Perform the search (you can expand this with Google search functionality if needed)
            search_results = list(search(query, num_results=num_results))
            return search_results
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def scrape_page(self, url):
        try:
            if self.driver is None:
                self._create_driver()

            # Navigate to the webpage
            self.driver.get(url)

            # Wait for the page to load (adjust as needed)
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

            # Scroll until the end of the page
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Get the full HTML content of the page
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
        except Exception as e:
            print(f"Error while scraping page: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()

