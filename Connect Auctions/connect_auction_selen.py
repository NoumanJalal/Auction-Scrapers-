import csv
import json
import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from auction_scraper_base import get_property_type, prepare_price, get_bedroom, get_tenure, parse_postal_code


class ConnectAuction:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def property_scraper(self, property_link):
        self.driver.get(property_link)

        image = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "(//img[@class='entered lazyloaded'])[1]")))
        image_link = image.get_attribute("src")
        print(image_link)

        guidePrice = self.driver.find_element(By.XPATH, "//span[contains(@class,'woocommerce-Price-amount')]").text
        price, currency = prepare_price(guidePrice)

        description_list = []

        sibling_description = self.driver.find_elements(By.XPATH, "//div[@id='tab-description']//following-sibling::p")
        for sibling_list in sibling_description:
            description_list.append(sibling_list.text)
            description = "".join(description_list)
            print(description)

        address = self.driver.find_element(By.XPATH, "//div[@class='wprwpg-gmap-content-section']/h2").text

        numbers_of_bedroom = self.driver.find_element(By.XPATH,
                                                      "(//div[@id='tab-description']/p)[2]").text
        number_of_bedrooms = get_bedroom(numbers_of_bedroom)

        title = self.driver.find_element(By.XPATH, "//h1[contains(@class,'product_title')]").text
        property_type = get_property_type(title)
        postal_code = parse_postal_code(title)

        tenure = self.driver.find_element(By.XPATH, "(//div[@id='tab-description']/p)[5]").text

        if not tenure:
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
            "source": "connectukauctions",
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
        csv_fh = open('connect_auction_selen.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("connect_auction_selen.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)

        list_dict = []

        for auction_divs_href in self.driver.find_elements(By.XPATH,
                                                           "//a[@class='ast-loop-product__link']"):
            auction_property = auction_divs_href.get_attribute('href')
            print(auction_property)
            auction_divs.append(auction_property)

        for property_link in auction_divs:
            result_dict = self.property_scraper(property_link)
            result_list = list(result_dict.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            list_dict.append(result_dict)
            workbook.save("connect_auction_selen.xlsx")

        json_result = json.dumps(list_dict)
        json_fh.write(json_result)
        json_fh.close()

    def run(self):
        self.driver.get("https://realtime.connectukauctions.co.uk/")
        self.properties_scraper()


auction = ConnectAuction()
auction.run()
