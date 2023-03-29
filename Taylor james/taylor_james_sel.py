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

        image = self.driver.find_element(By.XPATH, "(//div[@class='slide-content'])[1]").get_attribute("style")
        image_link = re.search(r'url\("?(.+)"?\)', image).group(1)
        print(image_link)

        guidePrice = self.driver.find_element(
            By.XPATH, "(//div[@class='col col-xs-12 col-sm-12 col-md-12 col-lg-12 col-xl-12']/p)[3]").text
        price, currency = prepare_price(guidePrice)

        description = self.driver.find_element(By.XPATH, "//div[@data-tab-content='tab_key_features']").text
        number_of_bedrooms = get_bedroom(description)

        address = self.driver.find_element(
            By.XPATH, "//div[@class='col col-xs-12 col-sm-12 col-md-7 col-lg-7 col-xl-7']//h1").text
        postal_code = parse_postal_code(address)

        tenure = self.driver.find_element(By.XPATH, "//p[substring-after(text(),'Fre')]").text

        title = self.driver.find_element(
            By.XPATH, "(//div[@class='col col-xs-12 col-sm-12 col-md-7 col-lg-7 col-xl-7'])[2]").text

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
            "source": "suttonkersh",
            "property_type": property_type,
            "number_of_bedrooms": number_of_bedrooms,
            "tenure": tenure,
        }
        return data_hash

    def properties_scraper(self):
        auction_divs = []
        for auction_divs_href in self.driver.find_elements(
                By.XPATH, "//a[contains(@class,'property-link')]"):
            auction_property = auction_divs_href.get_attribute('href')
            print(auction_property)
            auction_divs.append(auction_property)

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        csv_fh = open('taylorjamesauctions_sel.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("taylorjamesauctions_sel.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)

        list_dict = []

        for property_link in auction_divs:
            result_dict = self.property_scraper(property_link)
            result_list = list(result_dict.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            list_dict.append(result_dict)
            workbook.save("taylorjamesauctions_sel.xlsx")

        json_result = json.dumps(list_dict)
        json_fh.write(json_result)
        json_fh.close()
        workbook.close()
        csv_fh.close()

    def run(self):
        self.driver.get(
            "https://www.taylorjamesauctions.co.uk/auction/online-property-auction-22-03-2023-0800/")
        self.properties_scraper()


auction = TaylorJames()
auction.run()
