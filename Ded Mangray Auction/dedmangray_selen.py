import csv
import json
import re
import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from auction_scraper_base import get_property_type, prepare_price, get_bedroom, get_tenure, parse_postal_code, \
    get_bathroom


class DedMangrayAuction:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def property_scraper(self, property_link):
        self.driver.get(property_link)
        image = self.driver.find_element(By.XPATH, "//img[@class='main-photo']")
        image_link = image.get_attribute("src")

        guidePrice = self.driver.find_element(By.XPATH, "(//div[contains(@class,'twelve fluid')]//p)[8]").text
        price, currency = prepare_price(guidePrice)

        description_list = []
        description_loc = self.driver.find_element(By.XPATH, "//div[contains(@class,'twelve fluid columns')]/p").text
        for sibling_list in description_loc:
            description_list.append(sibling_list)
            description = "".join(description_list)
            print(description)

        property_type = get_property_type(description)
        number_of_bedrooms = get_bedroom(description)

        address = self.driver.find_element(By.XPATH, "(//tr[contains(@class,'lotrow')]/td)[2]").text
        postal_code = address.split(',')[-1]

        tenure = self.driver.find_element(By.XPATH, "//p[contains(text(),'Freehold')]").text

        title = self.driver.find_element(By.XPATH, "(//tr[contains(@class,'lotrow')]/td)[2]").text

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

        if property_type == "other":
            get_property_type(description)

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
        return data_hash

    def properties_scraper(self):
        auction_divs = []
        for auction_divs_href in self.driver.find_elements(
                By.XPATH, "//a[contains(@target,'lotdetails')]"):
            auction_property = auction_divs_href.get_attribute('href')
            print(auction_property)
            auction_divs.append(auction_property)

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        csv_fh = open('dedmangray_selen.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("dedmangray_selen.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)

        list_dict = []

        for property_link in auction_divs:
            result_dict = self.property_scraper(property_link)
            result_list = list(result_dict.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            list_dict.append(result_dict)
            workbook.save("dedmangray_selen.xlsx")

        json_result = json.dumps(list_dict)
        json_fh.write(json_result)
        json_fh.close()
        workbook.close()
        csv_fh.close()

    def run(self):
        self.driver.get(
            "https://www.iamsold.co.uk/properties/all/aberdeenshire/?search_id=bdd20b95a679410294dbac10f300505a")
        self.properties_scraper()


auction = DedMangrayAuction()
auction.run()
