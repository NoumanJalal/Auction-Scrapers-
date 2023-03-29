import csv
import json

import openpyxl
from playwright.sync_api import Page
from auction_scraper_base import browser_context
from auction_scraper_base import get_property_type, prepare_price, get_bedroom
import re

start_url = "https://auctionhouselondon.co.uk/current-auction/"


def property_scraper(detail_url_page, auction_house):
    propertyLink = f"https://auctionhouselondon.co.uk{auction_house}"
    detail_url_page.goto(propertyLink)
    print(propertyLink)

    house_image = detail_url_page.locator(
        "xpath=(//div[@class='absolute inset-0 bg-no-repeat bg-center bg-contain'])[2]").get_attribute('style')
    imagelink = re.search(r'url\("?(.+)"?\)', house_image).group(1)
    print(imagelink)

    number_of_bedrooms = detail_url_page.locator(
        "xpath=(//div[@class='text-17 xl:text-19 mb-15'])[1]").text_content()
    number_of_bedrooms = get_bedroom(number_of_bedrooms)
    print(number_of_bedrooms)

    price = detail_url_page.locator("(//p[contains(text(),'£')])[1]").text_content()
    price, currency = prepare_price(price)

    # print(price)

    address = detail_url_page.locator(
        "xpath=//div[@class='md:pl-20 py-10 md:py-0']").text_content()
    # print(address)

    postal_code = address.split(',')[-1]

    tenure = detail_url_page.locator("xpath=(//div[@class='text-17 xl:text-19 mb-15']/div)[1]").text_content()

    description = detail_url_page.locator(
        "xpath=//div[@class='pt-25 max-w-810']").text_content()

    title = detail_url_page.locator(
        "xpath=//div[@class='flex flex-wrap md:flex-no-wrap items-center text-18']").text_content()
    property_type = get_property_type(title)

    property_type = get_property_type(title)

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
        "source": "auctionhouselondon",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
    }
    print(data_hash)
    return data_hash


def properties_scraper(page, browser):
    auction_divs = []
    anchor_locator = page.locator("//a[@class='inline-flex items-center postblock__link ml-auto']")

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('auction_house_london_play.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("auction_house_london_play.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    for i in range(anchor_locator.count()):
        property_href = anchor_locator.nth(i)
        property_card = property_href.get_attribute("href")
        auction_divs.append(property_card)

    detail_url_page: Page = browser.new_page()
    list_dict = []

    for auction_house in auction_divs:
        result_dict = property_scraper(detail_url_page, auction_house)
        result_list = list(result_dict.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        list_dict.append(result_dict)
        workbook.save("auction_house_london_play.xlsx")

    json_result = json.dumps(list_dict)
    json_fh.write(json_result)
    json_fh.close()


def run():
    with browser_context(headless=False) as (page, browser):
        page.set_default_navigation_timeout(120000)
        page.goto(start_url)
        properties_scraper(page, browser)


if __name__ == "__main__":
    run()
