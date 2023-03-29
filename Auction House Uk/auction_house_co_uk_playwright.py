import csv
import json
import openpyxl
from playwright.sync_api import Page
from auction_scraper_base import browser_context, get_tenure
from auction_scraper_base import get_property_type, prepare_price, get_bedroom

start_url = "https://www.auctionhouse.co.uk/auction/search-results?searchType=0"


def property_scraper(detail_url_page, i, auction_house_card):
    detail_url_page.set_default_navigation_timeout(120000)
    propertyLink = auction_house_card
    detail_url_page.goto(propertyLink)
    print(propertyLink)

    print(f"Iteration {i + 1}: {propertyLink}")

    house_image = detail_url_page.locator(
        "xpath=(//img[@alt='Lot Image'])[1]")

    imagelink = house_image.get_attribute("src")
    # print(imagelink)

    number_of_bedrooms = detail_url_page.locator(
        "xpath=(//div[@class='col-md-14 col-sm-13']//p)[3]").text_content()
    number_of_bedrooms = get_bedroom(number_of_bedrooms)
    print(number_of_bedrooms)

    price = detail_url_page.locator("//b[contains(., '* Guide')] | //li[contains(., '* Guide')] | "
                                    "//span[contains(., '*Guide')]").text_content()
    price, currency = prepare_price(price)

    # print(price)

    address = detail_url_page.locator(
        "xpath=(//div[@class='container'])[3]//b").text_content()
    print(address)

    postal_code = address.split(',')[-1]

    tenure = detail_url_page.locator("xpath=(//p[contains(.,'Tenure:')])[2]").text_content().split()[-1]
    print(tenure)

    description_list = []

    description_loc = detail_url_page.locator(
        "xpath=//div[@class='preline'] | //h4[.='Description']/following-sibling::*[.!='']")

    for i in range(description_loc.count()):
        sibling_list = description_loc.nth(i)
        description_list.append(sibling_list.text_content())
        description = "".join(description_list)
    print(description)

    if not tenure:
        tenure = get_tenure(description)

    title = detail_url_page.locator("xpath=(//div[@class='col-sm-24'])[1]").text_content()

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
        "source": "auctionhouse.co.uk",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
    }

    return data_hash


def properties_scraper(page: Page, browser):
    auction_house_cards = []
    prop_xpath = "xpath=//div[contains(text(), '*Guide |')]/parent::*/parent::a"

    anchor_locator = page.locator(prop_xpath)
    print(anchor_locator)
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('auction_house_co_uk_playwright.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("agents_property_request.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)
    for i in range(anchor_locator.count()):
        auction_house_href = anchor_locator.nth(i)
        auction_house_card = auction_house_href.get_attribute('href')
        auction_house_cards.append(auction_house_card)

    detail_url_page: Page = browser.new_page()
    detail_url_page.wait_for_load_state()
    list_dict = []

    for i, auction_house_card in enumerate(auction_house_cards):
        result_dict = property_scraper(detail_url_page, i, auction_house_card)
        print(auction_house_card)

        result_list = list(result_dict.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        list_dict.append(result_dict)
        workbook.save("auction_house_co_uk_playwright.xlsx")

    json_result = json.dumps(list_dict)
    json_fh.write(json_result)
    json_fh.close()
    workbook.close()
    csv_fh.close()
    detail_url_page.close()


def run():
    with browser_context(headless=False) as (page, browser):
        page.set_default_navigation_timeout(180000)
        page.route("**/*", lambda route: route.abort() if route.request.resource_type == "image" else route.continue_())
        page.goto(start_url)
        properties_scraper(page, browser)


if __name__ == "__main__":
    run()
