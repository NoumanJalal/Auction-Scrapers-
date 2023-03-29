import csv
import json
import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from auction_scraper_base import get_property_type, prepare_price, get_bedroom, get_tenure, parse_postal_code, \
    get_bathroom


class IAmSoldAuction:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def property_scraper(self, property_link):
        self.driver.get(property_link)
        print(property_link)

        image = self.driver.find_element(By.XPATH, "(//div[@data-bkimage])[last()]")
        image_link = image.get_attribute("data-bkimage")

        guidePrice = self.driver.find_element(By.XPATH, "(//span[@class='current_price'])[1]").text
        price, currency = prepare_price(guidePrice)

        partial_description = self.driver.find_element(By.XPATH, "(//div[@class='p__readmore__wrap']/p)[1]").text

        address = self.driver.find_element(By.XPATH, "//div[@class='c__property__address p__property__address']/p").text
        postal_code = address.split(',')[-1]

        number_of_bedroom = self.driver.find_element(
            By.XPATH, "//ul[@class='nolist p__rooms']/li[contains(.,' bedroom')]").text
        number_of_bedrooms = get_bedroom(number_of_bedroom)

        number_of_bathroom = self.driver.find_element(
            By.XPATH, "//ul[@class='nolist p__rooms']/li[contains(.,' bathroom')]").text
        number_of_bathrooms = get_bathroom(number_of_bathroom)

        tenure = self.driver.find_element(By.XPATH, "(//table[@class='p__table']//td)[4]").text

        title = self.driver.find_element(By.XPATH, "//h1[@class='p__property__title']").text

        property_type = get_property_type(title)

        if property_type == "other":
            property_type = get_property_type(partial_description)

        data_hash = {
            "price": price,
            "currency_type": currency,
            "picture_link": image_link,
            "property_description": partial_description,
            "property_link": property_link,
            "address": address,
            "postal_code": postal_code,
            "auction_venue": "online",
            "source": "iamsold.co.uk",
            "property_type": property_type,
            "number_of_bedrooms": number_of_bedrooms,
            "tenure": tenure,
            "number_of_bathrooms": number_of_bathrooms
        }
        return data_hash

    def properties_scraper(self):
        while True:
            auction_divs = []

            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            csv_fh = open('iamsold_selen.csv', mode='w', newline='', encoding='utf8')
            json_fh = open("iamsold_selen.json", "w", encoding='utf8')
            csv_writer = csv.writer(csv_fh)

            list_dict = []

            for auction_divs_href in self.driver.find_elements(
                    By.XPATH, "//div[contains(@id, 'property') and .//li[@class='auctionTime']]"
                              "//a[@class='c__property__imgLink']"):
                auction_property = auction_divs_href.get_attribute('href')
                print(auction_property)
                auction_divs.append(auction_property)

            try:
                next_link = self.driver.find_element(By.XPATH, "(//ul[@class='nolist']//a)[10]").get_attribute("href")
            except:
                next_link = None

            for property_link in auction_divs:
                result_dict = self.property_scraper(property_link)
                result_list = list(result_dict.values())
                worksheet.append(result_list)
                csv_writer.writerow(result_list)
                list_dict.append(result_dict)
                workbook.save("iamsold_selen.xlsx")
            if next_link is not None:
                self.driver.get(next_link)
            else:
                break

        json_result = json.dumps(list_dict)
        json_fh.write(json_result)
        json_fh.close()
        workbook.close()
        csv_fh.close()

    def run(self):
        self.driver.get(
            "https://www.iamsold.co.uk/properties/all/aberdeenshire/?search_id=bdd20b95a679410294dbac10f300505a")
        self.properties_scraper()


auction = IAmSoldAuction()
auction.run()
