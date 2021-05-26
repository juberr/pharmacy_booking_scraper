from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from urllib import parse
import csv
import re

chrome_options = Options()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome('./chromedriver')


def parse_url_data(url, avail):

    queries=parse.parse_qs(parse.urlparse(url).query)
    name = queries['location'][0].split(':')[0]
    address = queries['location'][0].split(':')[1]
    postal_code = re.search('[A-Z]{1}[0-9]{1}[A-Z]{1}\s[0-9]{1}[A-Z]{1}[0-9]{1}', address).group(0)
    province = address.split(',')[-1].split()[0]
    uuid = queries['owner'][0]
    availability = bool(avail)
    row = [name, address, postal_code, province, uuid, availability]

    return row

def click(driver, item):
        driver.find_element_by_tag_name("select").send_keys(item)
        driver.find_element_by_class_name('btn-cta').click()
        driver.implicitly_wait(1)

def scrape_pharm_booking(driver):

    driver.get('https://www.pharmacybooking.com/')
    driver.find_element_by_class_name('btn-cta').click()
    provinces = driver.find_elements_by_tag_name('option')
    provinces = [i.get_attribute('value') for i in provinces if i.get_attribute('value') != '']

    for province in provinces:

        click(driver, province)

        try:

            error = driver.find_element_by_class_name('error').text # not participating
            print(f'{province} not participating, skipping')
            driver.back()
            continue

        except NoSuchElementException:

            options = driver.find_element_by_tag_name("select").find_elements_by_tag_name("option")
            # looks like they currently have one field for all covid-19 vaccination appointments
            try:
                covid_options = [option.text for option in options if 'covid 19' in option.text.lower()]
            except IndexError:
                print(f'{province} has no covid-19 vaccine offerings, skipping')
                continue

            for covid_option in covid_options:

                click(driver, covid_option)

                cities = driver.find_element_by_tag_name("select").find_elements_by_tag_name("option")
                cities = [city.text for city in cities if city.text != 'Select']

                for city in cities:

                    click(driver, city)

                    pharmacies = driver.find_element_by_tag_name("select").find_elements_by_tag_name("option")
                    pharmacies = [pharm.text for pharm in pharmacies if pharm.text != 'Select']

                    for pharmacy in pharmacies:

                        click(driver, pharmacy)

                        iframe = driver.find_element_by_tag_name('iframe')
                        driver.switch_to.frame(iframe)
                        avail =  driver.find_elements_by_class_name('activeday')
                        driver.switch_to.default_content()
                        url = iframe.get_attribute('src')
                        print(parse_url_data(url, avail))
                        driver.back()

                    driver.back()

                driver.back()

            driver.back()

            

                    
            
scrape_pharm_booking(driver)

driver.quit()