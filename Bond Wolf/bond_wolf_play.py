import csv
import json
import re
import time

import openpyxl
from playwright.sync_api import Page
from selenium.webdriver.support.wait import WebDriverWait

from auction_scraper_base import browser_context, prepare_price, get_bedroom, get_property_type, get_tenure

start_url = "https://www.bondwolfe.com/auctions/properties/?location=&minprice=&maxprice=&type="


def property_scraper(detail_url_page, property_link):
    detail_url_page.goto(property_link)

    image_link = detail_url_page.locator("(//div[@class='slick-track']//img)[1]").get_attribute('src')

    guidePrice = detail_url_page.locator("//h2[contains(@class,'PropertyHeader-price-value')]").text_content()
    price, currency = prepare_price(guidePrice)

    description = detail_url_page.locator("//div[contains(@class,'Content px-2 px-md-0')]").text_content()

    title = detail_url_page.locator("//div[contains(@class,'PropertyHeader-description ')]").text_content()

    address = detail_url_page.locator("//div[contains(@class,'PropertyHeader-description ')]/h1").text_content()
    postal_code = address.split(',')[-1]

    numbers_of_bedrooms = detail_url_page.locator(
        "(//div[contains(@class,'PropertyHeader-description ')]/p)[2]").text_content()
    number_of_bedrooms = get_bedroom(numbers_of_bedrooms)

    tenure = detail_url_page.locator("(//div[contains(@class,'my-4')])[4]").text_content()

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
    return data_hash


def properties_scraper(page, browser):
    auction_divs = []
    max_retries = 50
    button_clicking = 0
    while button_clicking < max_retries:
        try:
            load_more_button = page.wait_for_selector("xpath=//button[contains(text(), 'Load more')]", timeout=10000)
            page.execute_script("""
                                                arguments[0].scrollIntoView({
                                                    behavior: 'auto',
                                                    block: 'center',
                                                    inline: 'center'
                                                });
                                                """, load_more_button)
            time.sleep(1)
            if load_more_button.is_displayed():
                load_more_button.click()
                time.sleep(1)
                button_clicking += 1
            else:
                break
        except:
            break

    anchor_locator = page.locator("//p[.='Guide price']//parent::*//parent::*//parent::*//parent::a")

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('bond_wolf_play.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("bond_wolf_play.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    for i in range(anchor_locator.count()):
        property_href = anchor_locator.nth(i)
        property_card = property_href.get_attribute("href")
        auction_divs.append(property_card)

    detail_url_page: Page = browser.new_page()
    list_dict = []

    for property_link in auction_divs:
        result_dict = property_scraper(detail_url_page, property_link)
        result_list = list(result_dict.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        list_dict.append(result_dict)
        workbook.save("bond_wolf_play.xlsx")

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
