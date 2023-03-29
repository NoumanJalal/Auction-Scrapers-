import csv
import json
import time

import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from auction_scraper_base import prepare_price, get_property_type, get_bedroom


class AuctionBidx:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def property_scraper(self, property_link):
        self.driver.get(property_link)

        image_link = self.driver.find_element(By.XPATH, "(//img[contains(@class,'d-block w-100')])[2]")

        price = self.driver.find_element(By.XPATH, "//p[contains(text(),'Guide Price')]").text
        price, currency = prepare_price(price)

        description = self.driver.find_element(By.XPATH, "(//div[@class='content container'])[1]").text
        print(description)

        tenure = self.driver.find_element(By.XPATH, "(//div[@class='text-17 xl:text-19 mb-15']/div)[1]").text
        print(tenure)

        address = self.driver.find_element(By.XPATH, "//h2[@class='m-0 order-1 order-lg-0 ']").text

        postal_code = address.split(',')[-1]

        property_type = get_property_type(description)

        number_of_bedrooms = self.driver.find_element(By.XPATH,
                                                      "//div[@id='elevator-pitch']/ul").text

        if property_type == "other":
            property_type = get_property_type(description)

        if number_of_bedrooms is None:
            number_of_bedrooms = get_bedroom(description)

        data_hash = {
            "price": price,
            "currency_type": currency,
            "picture_link": image_link,
            "property_description": description,
            "property_link": property_link,
            "address": address,
            "postal_code": postal_code,
            "auction_venue": "online",
            "source": "iamsold.co.uk",
            "property_type": property_type,
            "number_of_bedrooms": number_of_bedrooms,
            "tenure": tenure,
        }
        print(data_hash)

    def properties_scraper(self):
        auction_divs = []
        for auction_divs_href in self.driver.find_elements(
                By.XPATH, "//a[@class='disable-decoration d-flex flex-column flex-fill']"):
            auction_property = auction_divs_href.get_attribute('href')
            print(auction_property)
            auction_divs.append(auction_property)

        for property_link in auction_divs:
            self.property_scraper(property_link)

    def run(self):
        self.driver.get("https://bidx1.com/en/ireland?division=80&region=1&maxprice=&page=1")
        self.properties_scraper()

    def close(self):
        self.driver.quit()


auction_cards = AuctionBidx()
try:
    auction_cards.run()
finally:
    auction_cards.close()
