import csv
import json
import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import re
from auction_scraper_base import get_property_type, prepare_price, get_bedroom


class AuctionHouseLondon:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def auction_london_scraper(self):
        auction_divs = []
        for auction_card_href in self.driver.find_elements(By.XPATH, "//a[@class='inline-flex items-center "
                                                                     "postblock__link ml-auto']"):
            auction_property = auction_card_href.get_attribute("href")
            auction_divs.append(auction_property)

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        csv_fh = open('auction_house_london_req.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("auction_house_london_req.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)

        for auction_prop in auction_divs:
            self.driver.get(auction_prop)
            aution_image = self.driver.find_element(By.XPATH, "(//div[@class='absolute inset-0 bg-no-repeat bg-center "
                                                              "bg-contain'])[2]")
            backgroung_image = aution_image.get_attribute('style')
            print(backgroung_image)
            imagelink = re.search(r'url\("?(.+)"?\)', backgroung_image).group(1)
            print(imagelink)

            price = self.driver.find_element(By.XPATH, "(//p[contains(text(),'£')])[1]").text
            price, currency = prepare_price(price)

            description = self.driver.find_element(By.XPATH, "//div[@class='pt-25 max-w-810']").text
            print(description)

            tenure = self.driver.find_element(By.XPATH, "(//div[@class='text-17 xl:text-19 mb-15']/div)[1]").text
            print(tenure)

            propertyLink = auction_prop

            address = self.driver.find_element(By.XPATH, "//div[@class='md:pl-20 py-10 md:py-0']").text

            postal_code = address.split(',')[-1]

            title = self.driver.find_element(By.XPATH,
                                             "//div[@class='flex flex-wrap md:flex-no-wrap items-center text-18']").text

            property_type = get_property_type(title)

            number_of_bedrooms = self.driver.find_element(By.XPATH,
                                                          "(//div[@class='text-17 xl:text-19 mb-15'])[1]").text

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
                "source": "iamsold.co.uk",
                "property_type": property_type,
                "number_of_bedrooms": number_of_bedrooms,
                "tenure": tenure,
            }
            print(data_hash)

            result_list = list(data_hash.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            jsonString = json.dumps(data_hash)
            json_fh.write(jsonString)
            workbook.save("auction_house_london_req.xlsx")

        workbook.close()
        csv_fh.close()
        json_fh.close()

    def run(self):
        self.driver.get("https://auctionhouselondon.co.uk/current-auction/")
        self.auction_london_scraper()

    def close(self):
        self.driver.quit()


aution_card = AuctionHouseLondon()
try:
    aution_card.run()
finally:
    aution_card.close()
