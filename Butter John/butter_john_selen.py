import csv
import json
import time

import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import re
from auction_scraper_base import get_property_type, prepare_price, get_bedroom, get_tenure, parse_postal_code


class ButterAuction:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def property_scraper(self, property_link):
        self.driver.get(property_link)

        house_image = self.driver.find_element(By.XPATH, "(//div[contains(@class,'slide__image')])[1]").get_attribute(
            'style')
        image_link = re.search(r'url\("?(.+)"?\)', house_image).group(1)
        print(image_link)

        guidePrice = self.driver.find_element(By.XPATH, "//span[2]//span[2]").text
        price, currency = prepare_price(guidePrice)

        description = self.driver.find_element(By.XPATH, "//div[contains(@class,'col-md-8')]").text

        partial_description = self.driver.find_element(By.XPATH, "(//div[contains(@class,'col-md-8')]/p)[1]").text
        # postal_code = parse_postal_code(description)

        address = self.driver.find_element(By.XPATH, "//h1[contains(@class,'section__title')]").text

        try:
            number_of_bedroom = self.driver.find_element(By.XPATH,
                                                         "//li[contains(text(),'Bedroom')] | "
                                                         "//li[contains(text(),'BEDROOM')]").text
            number_of_bedrooms = get_bedroom(number_of_bedroom)

        except:
            print(None)

        title = self.driver.find_element(By.XPATH, "//div[@class='section__meta']").text
        property_type = get_property_type(title)

        if number_of_bedrooms is None:
            number_of_bedrooms = get_bedroom(partial_description)

        if property_type == "other" and "land" in address.lower():
            property_type = "land"
        if "land" in address.lower():
            address = re.search(r"(?<= to ).*|(?<= of ).*|(?<= at ).*", address, re.IGNORECASE)
            if address:
                address = address.group().strip()
        tenure = get_tenure(description)

        data_hash = {
            "price": price,
            "currency_type": currency,
            "picture_link": image_link,
            "property_description": description,
            "property_link": property_link,
            "address": address,
            # "postal_code": postal_code,
            "auction_venue": "online",
            "source": "buttersjohnbee",
            "property_type": property_type,
            "number_of_bedrooms": number_of_bedrooms,
            "tenure": tenure,
            "title": title
        }
        return data_hash

    def properties_scraper(self):
        max_retries = 6
        button_clicking = 0
        while button_clicking < max_retries:
            try:
                self.driver.execute_script("""
                   window.scrollTo(0, document.body.scrollHeight);
                    """)

                time.sleep(2)
                show_more_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'Show More')]")))
                self.driver.execute_script("""
                                                    arguments[0].scrollIntoView({
                                                        behavior: 'auto',
                                                        block: 'center',
                                                        inline: 'center'
                                                    });
                                                    """, show_more_button)
                self.driver.implicitly_wait(2)
                if show_more_button.is_displayed():
                    show_more_button.click()
                    time.sleep(1)
                    button_clicking += 1
                else:
                    break
            except:
                break

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        csv_fh = open('butter_john_selen.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("butter_john_selen.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)

        list_dict = []

        auction_divs = []

        for auction_divs_href in self.driver.find_elements(By.XPATH,
                                                           "//div[contains(@class,'item infinite')]//a"):
            auction_property = auction_divs_href.get_attribute('href')
            print(auction_property)
            auction_divs.append(auction_property)

        for property_link in auction_divs:

            result_dict = self.property_scraper(property_link)
            result_list = list(result_dict.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            list_dict.append(result_dict)
            workbook.save("butter_john_selen.xlsx")

        json_result = json.dumps(list_dict)
        json_fh.write(json_result)
        json_fh.close()

    def run(self):
        self.driver.get(
            "https://www.buttersjohnbee.com/auction-properties/properties-for-sale-in-staffordshire-and-cheshire")
        self.properties_scraper()


auction = ButterAuction()
auction.run()
