# ===========================================================
# [ SCRAPING JOB LISTING from JobKorea ]
# 
# Author: Yoshima Putri
# GitHub: https://github.com/yoshimaputri
# If you are interested in more projects or repositories, 
# feel free to visit the GitHub link above.
# ===========================================================
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 10)

# Search for 'Data Scientist' job
search = "Data Scientist"
job_search_url = f'https://www.jobkorea.co.kr/Search/?stext={search}'
driver.get(job_search_url) 
time.sleep(1)  # Let the page load
# to see what we can scrap or not --> jobkorea.co.kr/robots.txt

job_count = len(driver.find_elements(By.CLASS_NAME, 'list-item'))
print(f'[INIT...] There is {job_count} JOBS')
jobs_listing = []
total_filtered_jobs = 0

# Iterate through job postings and scrape relevant data
for idx in range(job_count):
    driver.get(job_search_url) 
    time.sleep(3)
    job_elements = driver.find_elements(By.CLASS_NAME, 'list-item')
    job = job_elements[idx]
    info = job.get_attribute('data-gainfo')
    try:
        data_info = json.loads(info)
        title = data_info['dimension45']
        company = data_info['dimension48']
        location = data_info['dimension46']
        corp_section = job.find_element(By.CLASS_NAME, 'list-section-corp')
        link = corp_section.find_element(By.TAG_NAME, 'a').get_attribute('href')
        corp_web, job_details, due_date, check = '', '', '', False

        driver.get(link)
        time.sleep(2)
        try:
            corp_web = driver.find_element(By.CLASS_NAME, 'devCoHomepageLink').get_attribute('href')
            try:
                dt_elements = driver.find_element(By.CLASS_NAME, 'date').find_elements(By.TAG_NAME, 'dt')
                dd_elements = driver.find_element(By.CLASS_NAME, 'date').find_elements(By.TAG_NAME, 'dd')
                for i, dt in enumerate(dt_elements):
                    if '마감일' in dt.text:
                        due_date = dd_elements[i].text
            except Exception as e:
                due_date = 'always open'

            try:
                iframe = driver.find_element(By.TAG_NAME, 'iframe')
                driver.switch_to.frame('gib_frame')
                check = driver.find_element(By.CLASS_NAME, 'recruitment-items')
            except Exception as e:
                print(f"[Error No Job Description, might be poster] {str(e)[:120]}")

            if check:
                job_details = check.text

        except Exception as e:
            print(f"[Error Job Details] {str(e)[:120]}")

        if job_details:
            total_filtered_jobs += 1
            job_info = {
                "Job Title": title,
                "Company": company,
                "Location": location,
                "Job Link": link,
                "Corp Web": corp_web,
                "Job Details": job_details,  # Save first 50 characters of job details
                "Due Date": due_date
            }
            # Append the dictionary to the jobs_data list
            jobs_listing.append(job_info)

            print(f"======== Job Information {total_filtered_jobs} ======")
            print(f"Job Title: {title}")
            print(f"Company: {company}")
            print(f"Location: {location}")
            print(f"Job Link: {link}")
            print(f"Corp Web: {corp_web}")
            print(f"Job Details: {job_details[:50]}")
            print(f"Due Date: {due_date}")
            print("="*40)

    except Exception as e:
        print(f"[Error] {e}")

file_name = f"jobs_listing_{search.replace(' ','')}.json"
with open(file_name, 'w', encoding='utf-8') as json_file:
    json.dump(jobs_listing, json_file, ensure_ascii=False, indent=4)

print(f"Job data successfully saved to {file_name} \nTotal {total_filtered_jobs} Filtered Jobs")

# input("Press any key to quit the browser...")
driver.quit()
