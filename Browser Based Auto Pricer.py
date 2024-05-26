#This file launches a chrome selenium browser, for me to browse through carousell listings of iPhones. Once i find an interesting listing,
#i press a key in the console, where the program parses the Listing's Details (Title, Battery Health, Price, etc.) and removes all the
#unnecessary information, such that only the phone's crucial info is parsed. This is passed to the getShopPrice_simpleInfo() function
#which then uses the info to automatically get the phone's buyback price on a buyback platform. The info is then all printed out nicely.

import re

colour_words = ['black', 'gold', 'rose', 'silver', 'space', 'gray', 'white', 'blue', 'yellow', 'coral', 'red', 'green', 'purple', 'midnight', 'graphite', 'pacific', 'pink', 'grey']
other_bl_words = ['for', 'sale', 'hk', 'nego', 'negotiable', 'read', 'description', 'mint', 'female', 'condition', 'iphone', 'apple', 'kensington', 'cracked', 'back', 'used', 'local', 'set', 'tempered', 'glass', 'battery', 'health', 'singapore', 'oxley', 'instantbuy', 'atome', 'box', 'without', 'wts', 'screen', 'canera', 'protector', 'dual', 'sim', 'export', 'bnib', 'camera', 'ring', 'paint', 'peel', 'light', 'dent', 'zp', 'a', 'installments', 'payment', 'monthly']

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import scrape_shopprices
driver = webdriver.Chrome()

while True:

    i = input('Press any key to analyze price.')
    if i == 'exit':
        break
    title = driver.find_element(By.XPATH, '//h1[@data-testid="new-listing-details-page-desktop-text-title"]').text

    notFound = True
    device_batt_health = 'N/A'
    while notFound:
        for word in title.split():
            if '%' in word and word.strip('%').isalnum() and len(word.strip('%')) == 2:
                device_batt_health = word
                break

        try:
            condition_card_text = driver.find_element(By.ID, 'FieldSetField-Container-field_condition_fields_card').text
            for word in condition_card_text.split():
                if '%' in word and word.strip('%').isalnum() and len(word.strip('%')) == 2:
                    device_batt_health = word
                    break
        except NoSuchElementException:
            pass

        desc = driver.find_element(By.ID, 'FieldSetField-Container-field_description').text
        for word in desc.split():
            if '%' in word and word.strip('%').isalnum() and len(word.strip('%')) == 2:
                device_batt_health = word
                break

        break

    device_model = 'N/A'
    device_model_found = False
    try:
        details_card_text = driver.find_element(By.ID, 'FieldSetField-Container-field_listing_details').text
        for word in details_card_text.split('\n'):
            if 'iphone' in word.lower():
                device_model = word.lower().replace('iphone', '').lstrip()
                device_model_found = True
    except NoSuchElementException:
        pass

    no_spec_char = re.sub(r"[^a-zA-Z0-9]+", ' ', title).lower()
    words = no_spec_char.split()
    for bl_list in [colour_words, other_bl_words]:
        for bl_word in bl_list:
            for word in words:
                if word == bl_word:
                    words.remove(word)
                if word.isdigit() and (len(word) > 2 or int(word) > 14):
                    words.remove(word)

    device_storage = 'N/A'
    if not device_model_found:
        device_model_temp = []
        # words = title.split(' ')
        for word in words:
            if (len(word) == 2 and word.isdigit()) or word == 'X':
                device_model_no = word
            if word in ['pro', 'max', 'mini']:
                device_model_temp.append(word)
            if 'gb' in word:
                device_storage = word.upper()
        if len(device_model_temp) > 0:
            device_model = (device_model_no + ' '.join(device_model_temp)).lstrip().capitalize()
        else:
            device_model = device_model_no.lstrip().capitalize()

    if device_storage == 'N/A':
        try:
            details_card_text = driver.find_element(By.ID, 'FieldSetField-Container-field_listing_details').text
            for word in details_card_text.split():
                if 'gb' in word.lower():
                    device_storage = word.upper()
        except NoSuchElementException:
            pass


    if device_storage == 'N/A':
        device_storage = input('Enter Device Storage: ') + 'GB'
    if device_batt_health == 'N/A':
        device_batt_health = input('Enter Battery Health: ') + '%'

    list_price = driver.find_element(By.ID, 'FieldSetField-Container-field_price').text


    vendorPrices = scrape_shopprices.getShopPrice_simpleInfo('iphone ' + device_model, device_storage, device_batt_health.replace('%', ''))
    faa_price = vendorPrices["FAA"]
    fba_price = vendorPrices["FBA"]
    print(f'''
    {'-'*32}
      Model: iPhone {device_model} 
    Storage: {device_storage}
         BH: {device_batt_health}
    L Price: {list_price}
        FAA: S${faa_price} ({int(list_price.replace('S$', '').replace(',', '')) - int(faa_price)})
        FBA: S${fba_price} ({int(list_price.replace('S$', '').replace(',', '')) - int(fba_price)})
    {'-'*32}''')
