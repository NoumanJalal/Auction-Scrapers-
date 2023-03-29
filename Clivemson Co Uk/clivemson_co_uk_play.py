import csv
import json
import re
import time
import openpyxl
from playwright.sync_api import Page
from auction_scraper_base import browser_context, prepare_price, get_bedroom, get_property_type, get_tenure, parse_postal_code

start_url = "https://www.cliveemson.co.uk/properties/"


def property_scraper(detail_url_page, property_link):
    detail_url_page.goto(property_link)

    house_image = detail_url_page.locator("(//span[contains(@class,'image-placeholder')])[2]").get_attribute("style")
    image_link = re.search(r'url\("?(.+)"?\)', house_image).group(1)
    print(image_link)

    guidePrice = detail_url_page.locator("//strong[@class='lot-price']").text_content()
    price, currency = prepare_price(guidePrice)

    description = detail_url_page.locator("//section[contains(@class,'single-content')]").text_content()

    address = detail_url_page.locator("(//address[@class='lot-address'])[1]").text_content()
    postal_code = parse_postal_code(address)

    numbers_of_bedroom = detail_url_page.locator("(//section[contains(@class,'single-content')]/p)[1]").text_content()
    number_of_bedrooms = get_bedroom(numbers_of_bedroom)

    title = detail_url_page.locator("//div[@class='section__meta']").text_content()
    property_type = get_property_type(title)

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
        "source": "cliveemson",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
        "title": title
    }

    return data_hash


def properties_scraper(page, browser):
    auction_divs = []
    anchor_locator = page.locator("//a[@class='tile-block-link']")

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('butter_john_play.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("butter_john_play.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    list_dict = []

    for i in range(anchor_locator.count()):
        property_href = anchor_locator.nth(i)
        property_card = property_href.get_attribute("href")
        auction_divs.append(property_card)

    detail_url_page: Page = browser.new_page()

    for property_link in auction_divs:
        result_dict = property_scraper(detail_url_page, property_link)
        result_list = list(result_dict.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        list_dict.append(result_dict)
        workbook.save("butter_john_play.xlsx")

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
