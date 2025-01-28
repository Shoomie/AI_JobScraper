import json
import os
import time
import datetime
from curl_cffi import requests
from bs4 import BeautifulSoup

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
COMPANY_CONFIGS = [
    {
        "name": "anthropic",
        "url": "https://www.anthropic.com/jobs",
        "extractor": "anthropic",
        "headers": {
            'Authority': 'www.anthropic.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Dnt': '1',
            'Referer': 'https://www.anthropic.com/',
        }
    },
    {
        "name": "openai",
        "url": "https://openai.com/careers/search/",
        "extractor": "openai",
        "headers": {
            'Authority': 'openai.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Dnt': '1',
            'Referer': 'https://openai.com/',
        }
    },
    {
        "name": "xai",
        "url": "https://x.ai/careers",
        "extractor": "xai",
        "headers": {
            'Authority': 'x.ai',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Dnt': '1',
            'Referer': 'https://x.ai/',
        }
    }
]

def get_base_headers(company):
    """Generate common headers with platform spoofing"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        **company["headers"]
    }

def save_data(data, company_name):
    """Save results with timestamp"""
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = os.path.join(DATA_DIR, f"{company_name}_{today}.json")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                existing = json.load(f)
        else:
            existing = {"data": []}
    except json.JSONDecodeError:
        existing = {"data": []}

    existing["data"].append(data)
    
    with open(filename, "w") as f:
        json.dump(existing, f, indent=4)

    print(f"Data appended to {filename} at {timestamp}")

def anthropic_extractor(soup):
    """Optimized Anthropic data extractor with updated selectors"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    job_areas = {}
    total_jobs = 0
    
    # Updated selector for job category containers
    for category in soup.select('div[class*="JobCategory_container"]'):
        title = category.select_one('h3[class*="JobCategory_title"]')
        count = category.select_one('span[class*="JobCategory_count"]')
        if title and count:
            area_name = title.get_text(strip=True)
            jobs = int(count.get_text(strip=True).split()[0])
            job_areas[area_name] = jobs
            total_jobs += jobs
            
    return {"time": now, "total_jobs": total_jobs, "job_areas": job_areas}

def openai_extractor(soup):
    """Optimized OpenAI data extractor"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_jobs = 0
    job_areas = {}
    
    total_el = soup.find('span', class_='text-caption')
    if total_el:
        total_jobs = int(''.join(filter(str.isdigit, total_el.text)))
    
    container = soup.find('div', class_='mb-xl')
    if container:
        for job in container.select('div.w-full'):
            area = job.find('span', class_='text-copy-secondary')
            if area:
                area_name = area.get_text(strip=True)
                job_areas[area_name] = job_areas.get(area_name, 0) + 1
                
    return {"time": now, "total_jobs": total_jobs, "job_areas": job_areas}

def xai_extractor(soup):
    """Optimized xAI data extractor with updated selectors"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    job_areas = {}
    total_jobs = 0
    
    # Updated selector for section containers
    sections = soup.select('div[class*="CareerSection_container"]')
    
    for section in sections:
        title = section.select_one('h2')
        if title:
            area_name = title.get_text(strip=True)
            job_list = section.select_one('ul')
            if job_list:
                jobs = len(job_list.select('li'))
                job_areas[area_name] = jobs
                total_jobs += jobs
                
    return {"time": now, "total_jobs": total_jobs, "job_areas": job_areas}

def scrape_company(company_config):
    """Generic scraping function with retry logic"""
    print(f"Starting {company_config['name']} scraping...")
    start_time = time.time()
    
    for attempt in range(3):
        try:
            response = requests.get(
                company_config["url"],
                headers=get_base_headers(company_config),
                impersonate="chrome120",
                timeout=20
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if company_config["extractor"] == "anthropic":
                data = anthropic_extractor(soup)
            elif company_config["extractor"] == "openai":
                data = openai_extractor(soup)
            elif company_config["extractor"] == "xai":
                data = xai_extractor(soup)
                
            save_data(data, company_config["name"])
            print(f"Completed {company_config['name']} in {time.time()-start_time:.2f}s")
            return True
            
        except Exception as e:
            if attempt == 2:
                print(f"{company_config['name']} error: {str(e)}")
                return False
            time.sleep(0.5 * (attempt + 1))

def main_loop():
    """Main execution loop"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    while True:
        start_time = datetime.datetime.now()
        print(f"\n--- Starting scrape cycle at {start_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        for company in COMPANY_CONFIGS:
            scrape_company(company)
            
        # Calculate sleep time until next hour
        current_time = datetime.datetime.now()
        next_hour = (current_time + datetime.timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        sleep_duration = (next_hour - current_time).total_seconds()
        
        print(f"\nCycle completed. Sleeping {sleep_duration//60:.0f} minutes until next hour...")
        time.sleep(sleep_duration)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nScraping stopped by user")