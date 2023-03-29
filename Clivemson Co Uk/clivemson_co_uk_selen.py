import csv
import json
import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import re
from auction_scraper_base import get_property_type, prepare_price, get_bedroom, get_tenure, parse_postal_code


class CliveAuction:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def property_scraper(self, property_link):
        self.driver.get(property_link)

        house_image = self.driver.find_element(By.XPATH,
                                               "(//span[contains(@class,'image-placeholder')])[2]").get_attribute(
            "style")
        image_link = re.search(r'url\("?(.+)"?\)', house_image).group(1)
        print(image_link)

        guidePrice = self.driver.find_element(By.XPATH, "//strong[@class='lot-price']").text
        price, currency = prepare_price(guidePrice)

        description = self.driver.find_element(By.XPATH, "//section[contains(@class,'single-content')]").text

        address = self.driver.find_element(By.XPATH, "(//address[@class='lot-address'])[1]").text
        postal_code = parse_postal_code(address)

        numbers_of_bedroom = self.driver.find_element(By.XPATH,
                                                      "(//section[contains(@class,'single-content')]/p)[1]").text
        number_of_bedrooms = get_bedroom(numbers_of_bedroom)

        title = self.driver.find_element(By.XPATH, "//div[@class='section__meta']").text
        property_type = get_property_type(title)

        tenure = get_tenure(description)

        if number_of_bedrooms is None:
            number_of_bedrooms = get_bedroom(title)

        if property_type == "other" and "land" in address.lower():
            property_type = "land"
        if "land" in address.lower():
            address = re.search(r"(?<= to ).*|(?<= of ).*|(?<= at ).*", address, re.IGNORECASE)
            if address:
                address = address.group().strip()

        data_hash = {
            "price": price,
            "currency_type": currency,
            "picture_link": image_link,
            "property_description": description,
            "property_link": property_link,
            "address": address,
            "postal_code": postal_code,
            "auction_venue": "online",
            "source": "cliveemson",
            "property_type": property_type,
            "number_of_bedrooms": number_of_bedrooms,
            "tenure": tenure,
            "title": title
        }

        return data_hash

    def properties_scraper(self):
        auction_divs = []

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        csv_fh = open('butter_john_play.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("butter_john_play.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)

        list_dict = []

        for auction_divs_href in self.driver.find_elements(By.XPATH,
                                                           "//a[@class='tile-block-link']"):
            auction_property = auction_divs_href.get_attribute('href')
            print(auction_property)
            auction_divs.append(auction_property)

        for property_link in auction_divs:
            result_dict = self.property_scraper(property_link)
            result_list = list(result_dict.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            list_dict.append(result_dict)
            workbook.save("butter_john_play.xlsx")

        json_result = json.dumps(list_dict)
        json_fh.write(json_result)
        json_fh.close()

    def run(self):
        self.driver.get(
            "https://www.cliveemson.co.uk/properties/")
        self.properties_scraper()


auction = CliveAuction()
auction.run()
