import csv
import json
import re
import openpyxl
from playwright.sync_api import Page
from auction_scraper_base import browser_context, prepare_price, get_bedroom, get_property_type, get_tenure, \
    parse_postal_code, get_bathroom

start_url = "https://www.iamsold.co.uk/properties/all/aberdeenshire/?search_id=bdd20b95a679410294dbac10f300505a"


def property_scraper(detail_url_page, property_link):
    detail_url_page.goto(property_link)

    image_link = detail_url_page.locator("xpath=(//div[@data-bkimage])[last()]").get_attribute("data-bkimage")
    print(image_link)

    guidePrice = detail_url_page.locator("xpath=(//span[@class='current_price'])[1]").text_content()
    price, currency = prepare_price(guidePrice)

    description = detail_url_page.locator("xpath=(//div[@class='p__readmore__wrap']/p)[1]")
    print(description)

    property_type = get_property_type(description)

    address = detail_url_page.locator("xpath=//div[@class='c__property__address p__property__address']/p").text_content()

    number_of_bedroom = detail_url_page.locator(
        "xpath=//ul[@class='nolist p__rooms']/li[contains(.,' bedroom')]").text_content()
    number_of_bedrooms = get_bedroom(number_of_bedroom)

    number_of_bathroom = detail_url_page.locator(
        "xpath=//ul[@class='nolist p__rooms']/li[contains(.,' bathroom')]").text_content()
    number_of_bathrooms = get_bathroom(number_of_bathroom)

    title = detail_url_page.locator("xpath=//h1[@class='p__property__title']").text_content()

    postal_code = parse_postal_code(title)

    tenure = detail_url_page.locator("xpath=(//table[@class='p__table']//td)[4]").text_content()

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
        "title": title
    }
    return data_hash


def properties_scraper(page, browser):
    while True:
        auction_divs = []

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        csv_fh = open('iamsold_play.csv', mode='w', newline='', encoding='utf8')
        json_fh = open("iamsold_play.json", "w", encoding='utf8')
        csv_writer = csv.writer(csv_fh)

        list_dict = []

        anchor_locator = page.locator("//div[contains(@id, 'property') and .//li[@class='auctionTime']]"
                                      "//a[@class='c__property__imgLink']")

        for i in range(anchor_locator.count()):
            property_href = anchor_locator.nth(i)
            property_card = property_href.get_attribute("href")
            auction_divs.append(property_card)

        detail_url_page: Page = browser.new_page()

        try:
            next_link = page.locator("xpath=(//ul[@class='nolist']//a)[10]").get_attribute("href")
        except:
            next_link = None

        for property_link in auction_divs:
            result_dict = property_scraper(detail_url_page, property_link)
            result_list = list(result_dict.values())
            worksheet.append(result_list)
            csv_writer.writerow(result_list)
            list_dict.append(result_dict)
            workbook.save("iamsold_play.xlsx")

        if next_link is not None:
            page.goto(next_link)
        else:
            break

    json_result = json.dumps(list_dict)
    json_fh.write(json_result)
    json_fh.close()
    workbook.close()
    csv_fh.close()


def run():
    with browser_context(headless=False) as (page, browser):
        page.set_default_navigation_timeout(120000)
        page.goto(start_url)
        properties_scraper(page, browser)


if __name__ == "__main__":
    run()
