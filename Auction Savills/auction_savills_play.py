import csv
import json
import re
import openpyxl
from playwright.sync_api import Page
from auction_scraper_base import browser_context, prepare_price, get_bedroom, get_property_type, get_tenure, \
    parse_postal_code

start_url = "https://auctions.savills.co.uk/"


def property_scraper(detail_url_page, property_link):
    detail_url_page.goto(property_link)

    image_link = detail_url_page.locator(
        "xpath=(//li[contains(@data-slick-index,'')]/img)[1]").get_attribute("src")
    print(image_link)

    guidePrice = detail_url_page.locator("xpath=//span[contains(text(),'£')]").text_content()
    price, currency = prepare_price(guidePrice)

    description = detail_url_page.locator("xpath=//div[@class='description-paragraph']").text_content()
    print(description)
    number_of_bedrooms = get_bedroom(description)

    property_type = get_property_type(description)

    address = detail_url_page.locator(
        "xpath=(//div[@class='sv-property-intro__address-block']/div)[1]").text_content()
    postal_code = parse_postal_code(address)
    title = detail_url_page.locator(
        "xpath=(//div/p)[2]").text_content()

    postal_code = parse_postal_code(address)

    tenure = detail_url_page.locator("xpath=//p[contains(text(),'Fr')]").text_content()

    if not tenure:
        tenure = get_tenure(description)

    if number_of_bedrooms is None:
        number_of_bedrooms = get_bedroom(description)

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
        "source": "pugh-auctions",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
        "title": title
    }
    return data_hash


def properties_scraper(page, browser):
    auction_divs = []
    anchor_locator = page.locator("//a[.='Full details']")

    for i in range(anchor_locator.count()):
        property_href = anchor_locator.nth(i)
        property_card = property_href.get_attribute("href")
        auction_divs.append(property_card)

    detail_url_page: Page = browser.new_page()

    for property_link in auction_divs:
        property_scraper(detail_url_page, property_link)


def run():
    with browser_context(headless=False) as (page, browser):
        page.set_default_navigation_timeout(120000)
        page.goto(start_url)
        properties_scraper(page, browser)


if __name__ == "__main__":
    run()
