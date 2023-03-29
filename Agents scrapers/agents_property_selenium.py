from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from auction_scraper_base import get_property_type, prepare_price, get_bedroom


class AgentsProperties:
    driver: webdriver.Chrome

    def __init__(self):
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def auction_estate_scraper(self):
        auction_property_cards = []
        while True:
            for auction_card_href in self.driver.find_elements(By.XPATH, "//a[@class='u-link-cover']"):
                auction_property_card = auction_card_href.get_attribute('href')
                auction_property_cards.append(auction_property_card)

                """

            try:
                next_page_url = self.driver.find_element(By.XPATH,
                                                         "//span[@class='current']"
                                                         "/following-sibling::span").get_attribute("href")
            except:
                next_page_url = None
            """
            for auction_property_card in auction_property_cards:
                self.driver.get(auction_property_card)

                aution_image = self.driver.find_element(By.XPATH, "(//div[@class='gallery-img']//img)[1]")
                imagelink = aution_image.get_attribute('src')
                # print(aution_property_image)

                price = self.driver.find_element(By.XPATH, "//p[@class='single-property-price']").text
                price, currency = prepare_price(price)

                description = self.driver.find_element(By.XPATH, "//div[@class='container container--medium']").text
                print(description)

                tenure = self.driver.find_element(By.XPATH, "//p[contains(.,'Tenure')]").text
                print(tenure)

                propertyLink = auction_property_card

                address = self.driver.find_element \
                    (By.XPATH, "(//div[@class='single-property-intro col--40']//p)[1]").text

                postal_code = address.split(',')[-1]

                title = self.driver.find_element(By.XPATH, "//h1[@class='single-property-title']").text
                property_type = get_property_type(title)

                number_of_bedrooms = self.driver.find_element(By.XPATH, "//h1[@class='single-property-title']").text

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
                """
            if next_page_url is not None:
                self.driver.get(next_page_url)
            else:
                break
                """

    def run(self):
        self.driver.get("https://www.agentspropertyauction.com/next-auction/")

    def close(self):
        self.driver.quit()


aution_card = AgentsProperties()
try:
    aution_card.run()
    aution_card.auction_estate_scraper()
finally:
    aution_card.close()
