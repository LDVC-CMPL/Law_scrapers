import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import cloudscraper
import pandas as pd

def random_delay():
    time.sleep(random.uniform(1, 3))

chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
service = Service()

scraper = cloudscraper.create_scraper()
driver = webdriver.Chrome(service=service, options=chrome_options)
df = pd.DataFrame(columns=['Links', 'Title_Law', 'Pub_Date', 'Laws_Mod'])

try:
    driver.get("https://gzk.rks-gov.net/LawInForceList.aspx")
    
    click_count = 0
    max_clicks = 62

    while click_count < max_clicks:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        random_delay()
        all_links = driver.find_elements(By.TAG_NAME, 'a')

        random_delay()

        # Filter links containing the word "AcDetail" to find titles of the laws, then add them to the dataframe
        actdetail_links = [link.get_attribute('href') for link in all_links if link.get_attribute('href') and "ActDetail" in link.get_attribute('href')]
        for link in actdetail_links:
            df = pd.concat([df, pd.DataFrame({'Links': [link], 'Title_Law': [None], 'Pub_Date': [None], 'Laws_Mod': [None]})], ignore_index=True)

        # To find the "Next" button and click on it to switch page. When the button is no longer present, break the loop
        try:
            next_button = driver.find_element(By.ID, "MainContent_gvLawInForce_lbNext")
            if next_button.is_displayed():
                next_button.click()
                random_delay()
                click_count += 1
            else:
                break
        except:
            print("No more 'Next' button found, exiting.")
            break

    # After collecting all links, visit each link to gather the additional data on publication dates and amendments
    for index, row in df.iterrows():
        driver.get(row['Links'])
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        random_delay()

        # Gather the information on titles ('An_Data') from id="MainContent_rAktet_lblAn_0"
        try:
            an_element = driver.find_element(By.ID, "MainContent_rAktet_lblAn_0")
            an_data = an_element.text
        except:
            an_data = None  # If the element is not found, store None

        # Gather the publication date ('Pub_Date' from id="MainContent_lblDPubDate")
        try:
            pub_date_element = driver.find_element(By.ID, "MainContent_lblDPubDate")
            pub_date = pub_date_element.text
        except:
            pub_date = None

        # Gather amendments to laws (all class="span_margin") and join them
        try:
            span_margin_elements = driver.find_elements(By.CLASS_NAME, "span_margin")
            span_margin_texts = [element.text for element in span_margin_elements]
            span_margin = "/".join(span_margin_texts)
        except:
            span_margin = None

        df.at[index, 'Title_Law'] = an_data
        df.at[index, 'Pub_Date'] = pub_date
        df.at[index, 'Laws_Mod'] = span_margin

finally:
    driver.quit()

print(df)
df.to_csv('XKV_leg_stab.csv', index=False)
