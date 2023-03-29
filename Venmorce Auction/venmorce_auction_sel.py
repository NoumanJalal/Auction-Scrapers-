import csv
import json
import re
import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from auction_scraper_base import get_property_type, prepare_price, get_bedroom, get_tenure, parse_postal_code


class TaylorJames:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def property_scraper(self, property_link):
        self.driver.get(property_link)
        print(property_link)

        image_link = self.driver.find_element(By.XPATH, "(//img[@class='img_resp'])[1]").get_attribute("src")
        print(image_link)

        guidePrice = self.driver.find_element(
            By.XPATH, "//h2[contains(text(),'Guide Price ')]").text
        price, currency = prepare_price(guidePrice)

        description = self.driver.find_element(By.XPATH, "//div[@class='marbot40']").text

        short_description = self.driver.find_element(By.XPATH, "//div[@class='marbot20']/p").text
        number_of_bedrooms = get_bedroom(short_description)
        tenure = get_tenure(short_description)

        address = self.driver.find_element(
            By.XPATH, "//span[@class='font-thin f-paragon mini-2']").text
        postal_code = parse_postal_code(address)

        title = self.driver.find_element(
            By.XPATH, "//span[@class='font-thin f-paragon mini-2']").text

        property_type = get_property_type(description)

        if property_type == "other":
            property_type = get_property_type(description)
        if not tenure:
            tenure = get_tenure(description)

        data_hash = {
            "price": price,
            "currency_type": currency,
            "picture_link": image_link,
            "property_description": description,
            "property_link": property_link,
            "address": address,
            "postal_code": postal_code,
            "auction_venue": "online",
            "source": "venmoreauctions",
            "property_type": property_type,
            "number_of_bedrooms": number_of_bedrooms,
            "tenure": tenure,
        }
        return data_hash

    def properties_scraper(self):
        auction_divs = []
        for auction_divs_href in self.driver.find_elements(
                By.XPATH, "//span[contains(@class,'posrel')]/a"):
            auction_property = auction_divs_href.get_attribute('href')
            print(auction_property)
            auction_divs.append(auction_property)

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        csv_fh = open('venmorce_auction_sel.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("venmorce_auction_sel.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)

        list_dict = []

        for property_link in auction_divs:
            result_dict = self.property_scraper(property_link)
            result_list = list(result_dict.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            list_dict.append(result_dict)
            workbook.save("venmorce_auction_sel.xlsx")

        json_result = json.dumps(list_dict)
        json_fh.write(json_result)
        json_fh.close()
        workbook.close()
        csv_fh.close()

    def run(self):
        self.driver.get(
            "https://www.venmoreauctions.co.uk/Property-Search?pageNum=1")
        self.properties_scraper()


auction = TaylorJames()
auction.run()
