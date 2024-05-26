#This file parses every Carousell listing automatically and organises it into a csv, for further (and easier) data analysis via filtering.
#Main purpose is to find cheap phone listings quickly instead of browsing every listing manually.
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
driver = webdriver.Chrome()

search_query = 'iPhone 14'
load_count = 15

listing_params = ['seller', 'duration', '']

driver.get(f"https://www.carousell.sg/search/{search_query}?addRecent=true")
for x in range(load_count):
    ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
    show_more_btn = WebDriverWait(driver, 10, ignored_exceptions=ignored_exceptions) \
        .until(expected_conditions.presence_of_element_located((By.XPATH, '//button[normalize-space()="Show more results"]')))
    show_more_btn.click()
    time.sleep(2)

c = driver.find_elements(By.CLASS_NAME, 'D_yj')
listings = []
for x in c:
    listing_link = 'https://www.carousell.sg/p/' + x.get_attribute('data-testid').split('-')[2]
    listing = x.text.split('\n')[:-1]
    if 'InstantBuy' in listing:
        listing.remove('InstantBuy')
    if 'Protection' in listing:
        listing.remove('Protection')
    if 'Free shipping' in listing:
        listing.remove('Free shipping')
    listing.append(listing_link)
    listings.append(listing)

csv_text = str(listings).replace("'", '').replace("], [", '\n')
filename = datetime.now().strftime("%d %b %I:%M %p")
with open(f'{filename} | {search_query}.csv', 'w') as inFile:
    inFile.write(csv_text)