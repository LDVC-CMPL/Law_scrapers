from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import csv
import time

def scrape_lovdata(year=2016):
    driver = webdriver.Chrome()

    url = f"https://lovdata.no/register/lovtidend?avdeling=LTI&ministry=*&year={year}&kunngjortDato=*&search=#doclistheader"
    driver.get(url)

    all_links = []

    # Gather all links containing the url for laws ("dokument/LTI/lov/"). Then loop through them and extract the amendments.
    while True:
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'dokument/LTI/lov/')]")
        all_links.extend([link.get_attribute('href') for link in links])

        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "next"))
            )
            next_button.click()
            time.sleep(2)
        except (NoSuchElementException, TimeoutException):
            break

    results = []

    for link in all_links:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                driver.get(link)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "metaTitleText"))
                )
                break
            except (TimeoutException, StaleElementReferenceException):
                if attempt == max_attempts - 1:
                    print(f"Failed to load {link}. Skipping.")
                    continue
                time.sleep(2)

        try:
            title = driver.find_element(By.CLASS_NAME, "metaTitleText").text
        except NoSuchElementException:
            title = "NA"

        try:
            amendments_elements = driver.find_elements(By.ID, "metaField_endrer")
            amendments = ", ".join([elem.text for elem in amendments_elements if elem.text])
            if not amendments:
                amendments = "NA"
        except NoSuchElementException:
            amendments = "NA"

        results.append([link, title, amendments])

    driver.quit()

    filename = f"lovdata_results_{year}.csv"
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Link", "Title", "Amendments"])
        writer.writerows(results)

    return results


if __name__ == "__main__":
    year_to_scrape = input("Enter year to scrape (e.g. 2016): ")
    
    try:
        year_to_scrape = int(year_to_scrape)
    except ValueError:
        year_to_scrape = 2016

    data = scrape_lovdata(year=year_to_scrape)
    print(data[:5])