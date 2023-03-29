import csv
import json
import re
import time
import openpyxl
from playwright.sync_api import Page
from auction_scraper_base import browser_context, prepare_price, get_bedroom, get_property_type, get_tenure

start_url = "https://www.buttersjohnbee.com/auction-properties/properties-for-sale-in-staffordshire-and-cheshire"


def property_scraper(detail_url_page, property_url):
    property_link = detail_url_page.goto(f"https://www.buttersjohnbee.com{property_url}")
    print(property_link)

    image = detail_url_page.locator("(//div[contains(@class,'slide__image')])[1]").get_attribute(
        'style')
    image_link = re.search(r'url\("?(.+)"?\)', image).group(1)
    print(image_link)

    guidePrice = detail_url_page.locator("//span[2]//span[2]").text_content()
    price, currency = prepare_price(guidePrice)

    description = detail_url_page.locator("//div[contains(@class,'col-md-8')]").text_content()

    partial_description = detail_url_page.locator("(//div[contains(@class,'col-md-8')]/p)[1]").text_content()

    title = detail_url_page.locator("//div[@class='section__meta']").text_content()
    property_type = get_property_type(title)

    address = detail_url_page.locator("//h1[contains(@class,'section__title')]").text_content()

    number_of_bedrooms = ""
    try:
        number_of_bedrooms = detail_url_page.locator("//li[contains(text(),'Bedroom')] | "
                                                     "//li[contains(text(),'BEDROOM')]")
    except:
        if number_of_bedrooms is None:
            number_of_bedrooms = get_bedroom(title)
        print(f"no of bedrooms is {number_of_bedrooms}")

    tenure = get_tenure(description)

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
        # "postal_code": postal_code,
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
            page.evaluate('''() => {
              window.scrollTo(0, document.body.scrollHeight);
            }''')
            time.sleep(1)
            show_more_button = page.wait_for_selector("xpath=//a[contains(text(),'Show More')]", timeout=10000)
            page.evaluate('''(show_more_button) => {
                      show_more_button.scrollIntoView({
                        behavior: 'auto',
                        block: 'center',
                        inline: 'center'
                      });
                    }''', show_more_button)
            time.sleep(1)
            if show_more_button.is_visible():
                show_more_button.click()
                time.sleep(1)
                button_clicking += 1
            else:
                break
        except:
            break

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('butter_john_play.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("butter_john_play.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    list_dict = []

    anchor_locator = page.locator("//div[contains(@class,'item infinite')]//a")

    for i in range(anchor_locator.count()):
        property_href = anchor_locator.nth(i)
        property_card = property_href.get_attribute("href")
        auction_divs.append(property_card)

    detail_url_page: Page = browser.new_page()

    for property_url in auction_divs:
        result_dict = property_scraper(detail_url_page, property_url)
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
