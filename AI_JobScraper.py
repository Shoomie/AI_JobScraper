from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import datetime
import os
import json
from bs4 import BeautifulSoup

def create_driver(headless=True):
    """
    Creates and configures a Selenium WebDriver instance for Firefox.
    """
    firefox_options = FirefoxOptions()
    if headless:
        firefox_options.add_argument("--headless")
    firefox_options.add_argument("--window-size=1920x1080")
    return webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=firefox_options)

def save_data(data, company_name, data_dir):
    """
    Saves the scraped data to a JSON file.
    """
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = os.path.join(data_dir, f"{company_name}_{today}.json")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error: {filename} is not a valid JSON file. Creating a new file.")
                existing_data = {"data": []}
    else:
        existing_data = {"data": []}

    existing_data["data"].append(data)

    with open(filename, "w") as f:
        json.dump(existing_data, f, indent=4)

    print(f"Data appended to {filename} at {timestamp}")

def scrape_careers(url, company_name, data_dir, wait_condition, data_extractor, browser):
    """
    Generic function to scrape career data from a given URL.
    """
    start_time = datetime.datetime.now()
    print(f"Starting {company_name} scraping at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        browser.get(url)
        wait = WebDriverWait(browser, 20)
        wait.until(wait_condition)
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        data = data_extractor(soup, browser) # Pass browser instance if needed
        save_data(data, company_name, data_dir)
        print(f"Finished {company_name} scraping and data appended at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"{company_name} Scraper Error: {e}")

def anthropic_data_extractor(soup, browser):
    """
    Extracts career data from the Anthropic jobs page.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    job_areas = anthropic_data_extractor_internal(soup) # No browser needed here
    total_jobs = sum(job_areas.values())
    return {"time": now, "total_jobs": total_jobs, "job_areas": job_areas}

def anthropic_data_extractor_internal(soup): # Helper function for anthropic
    job_areas = {}
    job_area_elements = soup.find_all('label', class_='OpenRoles_role-label__tlmxy')
    for area_element in job_area_elements:
        area_title_element = area_element.find('h4', class_='OpenRoles_role-title__UjdUz')
        open_roles_element = area_element.find('span', class_='OpenRoles_role-count__SQbmz')
        if area_title_element and open_roles_element:
            area = area_title_element.text.strip()
            num_jobs = int(open_roles_element.text.split()[0])
            job_areas[area] = num_jobs
    return job_areas


def openai_data_extractor(soup, browser):
    """
    Extracts career data from the OpenAI jobs page.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_jobs = 0
    job_areas = {}

    total_jobs_element = soup.find('span', class_='text-p2', string=lambda text: text and 'job' in text.lower())
    total_jobs_text = total_jobs_element.text.split(' ')[0] if total_jobs_element else "0" # Extract number part
    total_jobs = int(total_jobs_text.replace(",", "")) # remove comma and to int

    job_listings_container = soup.find('div', class_='mb-xl')
    if job_listings_container:
        job_listings = job_listings_container.find_all('div', class_='w-full')
        for job in job_listings:
            area_element = job.find('span', class_='text-p2', string=lambda text: text and text.strip()) # More robust area selector
            if area_element:
                area = area_element.text.strip()
                job_areas[area] = job_areas.get(area, 0) + 1
    else:
        print("No job listings found on the page.")
    return {"time": now, "total_jobs": total_jobs, "job_areas": job_areas}


def xai_data_extractor(soup, browser):
    """
    Extracts career data from the xAI jobs page.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    job_areas = {}
    total_jobs = 0
    for i in range(2, 10):
        try:
            area_title_xpath = f"/html/body/div[4]/div/main/div[8]/div[{i}]/div[1]/div/h2"
            job_list_xpath = f"/html/body/div[4]/div/main/div[8]/div[{i}]/div[2]/ul"
            area_title_element = browser.find_element(By.XPATH, area_title_xpath)
            area = area_title_element.text.strip()
            job_list_element = browser.find_element(By.XPATH, job_list_xpath)
            num_jobs = len(job_list_element.find_elements(By.TAG_NAME, "li"))
            job_areas[area] = num_jobs
            total_jobs += num_jobs
        except:
            break
    return {"time": now, "total_jobs": total_jobs, "job_areas": job_areas}

if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    browser = create_driver()

    try:
        while True:
            scrape_careers(
                url="https://www.anthropic.com/jobs",
                company_name="anthropic",
                data_dir=data_dir,
                wait_condition=EC.presence_of_element_located((By.CSS_SELECTOR, "label.OpenRoles_role-label__tlmxy")),
                data_extractor=anthropic_data_extractor,
                browser=browser
            )

            scrape_careers(
                url="https://openai.com/careers/search/",
                company_name="openai",
                data_dir=data_dir,
                wait_condition=EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Careers')]")), # Wait for the main heading
                data_extractor=openai_data_extractor,
                browser=browser
            )

            scrape_careers(
                url="https://x.ai/careers#open-roles",
                company_name="xai",
                data_dir=data_dir,
                wait_condition=EC.presence_of_element_located((By.XPATH, "/html/body/div[4]/div/main/div[8]/div[2]/div[1]/div/h2")),
                data_extractor=lambda soup: xai_data_extractor(soup, browser),
                browser=browser
            )

            current_time = datetime.datetime.now()
            next_hour = (current_time + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            sleep_duration = (next_hour - current_time).total_seconds()
            print(f"Sleeping for {sleep_duration:.0f} seconds until {next_hour.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(sleep_duration)
    finally:
        browser.quit()