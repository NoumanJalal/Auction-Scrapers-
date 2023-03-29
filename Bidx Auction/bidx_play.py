import re

import openpyxl
from playwright.sync_api import Page
from auction_scraper_base import browser_context, get_tenure
from auction_scraper_base import get_property_type, prepare_price, get_bedroom

start_url = "https://bidx1.com/en/ireland?division=80&region=1&maxprice=&page=1"


def property_scraper(detail_url_page, auction_house):
    propertyLink = f'https://bidx1.com{auction_house}'
    detail_url_page.goto(propertyLink)
    print(propertyLink)

    image_link = detail_url_page.locator("(//img[contains(@class,'d-block w-100')])[2]")
    print(image_link)

    guidePrice = detail_url_page.locator("xpath=//p[contains(text(),'Guide Price')]").text_content()
    price, currency = prepare_price(guidePrice)

    description = detail_url_page.locator("xpath=(//div[@class='content container'])[1]").text_content()
    print(description)

    address = detail_url_page.locator("xpath=//h2[@class='m-0 order-1 order-lg-0 ']").text_content()
    postal_code = address.split(',')[-1]

    numbers_of_bedrooms = detail_url_page.locator("xpath=//div[@id='elevator-pitch']/ul").text_content()
    number_of_bedrooms = get_bedroom(numbers_of_bedrooms)
    print(number_of_bedrooms)

    tenure = detail_url_page.locator("xpath=(//div[@id='elevator-pitch']//strong)[1]").text_content()

    if number_of_bedrooms is None:
        number_of_bedrooms = get_bedroom(description)

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
        "property_link": propertyLink,
        "address": address,
        "postal_code": postal_code,
        "auction_venue": "online",
        "source": "auctionhouselondon",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
    }


def properties_scraper(page, browser):
    auction_divs = []
    anchor_locator = page.locator("//a[@class='disable-decoration d-flex flex-column flex-fill']")

    for i in range(anchor_locator.count()):
        property_href = anchor_locator.nth(i)
        property_card = property_href.get_attribute("href")
        auction_divs.append(property_card)

    detail_url_page: Page = browser.new_page()

    for auction_house in auction_divs:
        property_scraper(detail_url_page, auction_house)


def run():
    with browser_context(headless=False) as (page, browser):
        page.set_default_navigation_timeout(120000)
        page.goto(start_url)
        properties_scraper(page, browser)


if __name__ == "__main__":
    run()
