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
from auction_scraper_base import get_property_type, prepare_price, get_bedroom, get_tenure


class BondWolfAuction:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def property_scraper(self, property_link):
        self.driver.get(property_link)

        image_link = self.driver.find_element(By.XPATH, "(//div[@class='slick-track']//img)[1]").get_attribute('src')

        guidePrice = self.driver.find_element(By.XPATH, "//h2[contains(@class,'PropertyHeader-price-value')]").text
        price, currency = prepare_price(guidePrice)

        description = self.driver.find_element(By.XPATH, "//div[contains(@class,'Content px-2 px-md-0')]").text

        title = self.driver.find_element(By.XPATH, "//div[contains(@class,'PropertyHeader-description ')]").text

        address = self.driver.find_element(By.XPATH, "//div[contains(@class,'PropertyHeader-description ')]/h1").text
        postal_code = address.split(',')[-1]

        tenure = self.driver.find_element(By.XPATH, "(//div[contains(@class,'my-4')])[4]").text

        numbers_of_bedrooms = self.driver.find_element(By.XPATH,
                                                       "(//div[contains(@class,'PropertyHeader-description ')]/p)[2]").text
        number_of_bedrooms = get_bedroom(numbers_of_bedrooms)

        if number_of_bedrooms is None:
            number_of_bedrooms = get_bedroom(title)

        property_type = get_property_type(description)

        if property_type == "other" and "land" in address.lower():
            property_type = "land"
        if "land" in address.lower():
            address = re.search(r"(?<= to ).*|(?<= of ).*|(?<= at ).*", address, re.IGNORECASE)
            if address:
                address = address.group().strip()

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
            "source": "auctionhouselondon",
            "property_type": property_type,
            "number_of_bedrooms": number_of_bedrooms,
            "tenure": tenure,
            "title": title
        }
        print(data_hash)
        return data_hash

    def properties_scraper(self):
        auction_divs = []
        max_retries = 50
        button_clicking = 0
        while button_clicking < max_retries:
            try:
                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Load more')]")))
                self.driver.execute_script("""
                                            arguments[0].scrollIntoView({
                                                behavior: 'auto',
                                                block: 'center',
                                                inline: 'center'
                                            });
                                            """, load_more_button)
                time.sleep(3)
                if load_more_button.is_displayed():
                    load_more_button.click()
                    time.sleep(1)
                    button_clicking += 1
                else:
                    break
            except:
                break

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        csv_fh = open('bond_wolf_selenium.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("bond_wolf_selenium.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)

        for auction_divs_href in self.driver.find_elements(By.XPATH,
                                                           "//p[.='Guide price']//parent::*//parent::*//parent::*"
                                                           "//parent::a"):
            auction_property = auction_divs_href.get_attribute('href')
            print(auction_property)
            auction_divs.append(auction_property)
        list_dict = []

        for property_link in auction_divs:
            result_dict = self.property_scraper(property_link)

            result_list = list(result_dict.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            list_dict.append(result_dict)
            workbook.save("bond_wolf_selenium.xlsx")

        json_result = json.dumps(list_dict)
        json_fh.write(json_result)
        json_fh.close()

    def run(self):
        self.driver.get("https://www.bondwolfe.com/auctions/properties/?location=&minprice=&maxprice=&type=")
        self.properties_scraper()


auction = BondWolfAuction()
auction.run()

