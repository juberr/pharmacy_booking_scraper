from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from urllib import parse
import csv
import re


def parse_url_data(url, avail):

    queries=parse.parse_qs(parse.urlparse(url).query)
    name = queries['location'][0].split(':')[0]
    address = queries['location'][0].split(':')[1]
    postal_code = re.search('[A-Z]{1}[0-9]{1}[A-Z]{1}\s[0-9]{1}[A-Z]{1}[0-9]{1}', address).group(0).replace(' ', '')
    province = address.split(',')[-1].split()[0]
    store_key = address.replace(' ', '').replace(',', '')
    row = [name, address, postal_code, province, store_key, avail, url]

    return row

def click(driver, item):

    select_field = WebDriverWait(driver, 5).until(ec.visibility_of_element_located((By.TAG_NAME, 'select')))
    select_field.send_keys(item)
    button = WebDriverWait(driver, 5).until(ec.visibility_of_element_located((By.CLASS_NAME, 'btn-cta')))
    button.click()

def get_options(driver, time, data):

    options = WebDriverWait(driver, time).until(ec.visibility_of_element_located((By.TAG_NAME, 'option')))
    options = driver.find_elements_by_tag_name('option')

    if data == 'value':
        options = [i.get_attribute('value') for i in options if i.get_attribute('value') not in ['','Select']]
        return options
    
    options = [i.text for i in options if i.text not in ['','Select']]

    return options

def scrape_pharm_booking():

    with open('list.csv', mode='w') as file:
        file_writer = csv.writer(file, delimiter=',')
        file_writer.writerow(['Name', 'Address', 'Postal Code', 'Province', 'Store_id', 'Availability', 'URL'])

        driver = webdriver.Chrome('./chromedriver')

        driver.get('https://www.pharmacybooking.com/')
        button = driver.find_element_by_class_name('btn-cta')
        button.click()
        provinces = get_options(driver, 5, 'value')

        for province in provinces:

            click(driver, province)

            try:

                WebDriverWait(driver, 3).until(ec.visibility_of_element_located((By.CLASS_NAME, 'error')))
                # not participating
                print(f'{province} not participating, skipping')
                backbutton = driver.find_element_by_class_name('btn')
                backbutton.click()
                continue

            except TimeoutException:

                options = driver.find_element_by_tag_name('select')
                options = options.find_elements_by_tag_name('option')
                # looks like they currently have one field for all covid-19 vaccination appointments
                try:
                    covid_options = [option.text for option in options if 'covid 19' in option.text.lower()]
                    covid_options[0]
                except IndexError:
                    print(f'{province} has no covid-19 vaccine offerings, skipping')
                    backbutton = driver.find_element_by_class_name('btn')
                    backbutton.click()
                    continue

                # for covid_option in covid_options:

                click(driver, covid_options[0])

                cities = get_options(driver, 5, 'value')

                for city in cities:

                    click(driver, city)

                    pharmacies = get_options(driver, 5, 'text')
                    print(pharmacies)

                    for pharmacy in pharmacies:

                        click(driver, pharmacy)

                        iframe = WebDriverWait(driver, 5).until(ec.visibility_of_element_located((By.TAG_NAME, 'iframe')))
                        url = iframe.get_attribute('src')
                        driver.get(url)
                        avail =  1 if driver.find_elements_by_xpath("//span[@data-qa='activeCalendarDay']") else 0
                        data = parse_url_data(url, avail)
                        file_writer.writerow(data)
                        driver.back()
                        driver.back()

                    driver.back()

                driver.back()

            driver.back()

        driver.quit()


            

