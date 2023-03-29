import csv
import time

import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from auction_scraper_base import *


class AuctionHouse:
    driver: webdriver.Chrome

    def __init__(self):
        driver_path = ChromeDriverManager().install()
        service = Service(executable_path=driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def run(self):
        self.driver.get("https://www.auctionhouse.co.uk/auction/search-results?searchType=0")

    def auction_house_scraper(self):
        self.run()
        auction_house_cards = []
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        csv_fh = open('auctionhouse.co.uk_selenium.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("auctionhouse.co.uk_selenium.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)
        for auction_house_href in self.driver.find_elements(By.XPATH,
                                                            "//div[contains(text(), '*Guide |')]/parent::*/parent::a"):
            auction_house_card = auction_house_href.get_attribute('href')
            auction_house_cards.append(auction_house_card)
            print(auction_house_card)

        for auction_house_card in auction_house_cards:
            self.driver.get(auction_house_card)

            aution_image = self.driver.find_element(By.XPATH, "(//img[@alt='Lot Image'])[1]")
            imagelink = aution_image.get_attribute('src')
            print(imagelink)

            price = self.driver.find_element(By.XPATH, "//b[contains(., '* Guide')] | //li[contains(., '* Guide')] | "
                                                       "//span[contains(., '*Guide')]").text
            price, currency = prepare_price(price)

            description_list = []

            description_lines = self.driver.find_elements(By.XPATH,
                                                          "//div[@class='preline'] | //h4["
                                                          ".='Description']/following-sibling::*[.!='']")
            for element in description_lines:
                description_list.append(element.text)
                description = "".join(description_list)
            print(description)

            tenure = self.driver.find_element(By.XPATH, "(//div[@class='col-md-14 col-sm-13']//b)[6]").text
            print(tenure)

            propertyLink = auction_house_card

            address = self.driver.find_element(By.XPATH, "(//div[@class='container'])[3]//b").text

            postal_code = address.split(',')[-1]

            title = self.driver.find_element(By.XPATH, "(//div[@class='col-sm-24'])[1]").text
            property_type = get_property_type(title)

            number_of_bedrooms = self.driver.find_element(By.XPATH, "//li[contains(., 'Bedroom')]").text

            if property_type == "other":
                property_type = get_property_type(description)

            if number_of_bedrooms is None:
                number_of_bedrooms = get_bedroom(description)

            data_hash = {
                "price": price,
                "currency_type": currency,
                "picture_link": imagelink,
                "property_description": description,
                "property_link": propertyLink,
                "address": address,
                "postal_code": postal_code,
                "auction_venue": "online",
                "source": "auctionhouse.co.uk",
                "property_type": property_type,
                "number_of_bedrooms": number_of_bedrooms,
                "tenure": tenure,
            }

            result_list = list(data_hash.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            jsonString = json.dumps(data_hash)
            json_fh.write(jsonString)
            workbook.save("auctionhouse.co.uk_selenium.xlsx")

        workbook.close()
        csv_fh.close()
        json_fh.close()

    def close(self):
        self.driver.quit()


auction_house = AuctionHouse()
try:
    auction_house.auction_house_scraper()
finally:
    auction_house.close()
