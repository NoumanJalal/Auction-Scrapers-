from playwright.sync_api import Page
from auction_scraper_base import browser_context, get_tenure
from auction_scraper_base import get_property_type, prepare_price, get_bedroom

start_url = "https://www.agentspropertyauction.com/next-auction/"


def property_scraper(detail_url_page, i, auction_house_card):

    detail_url_page.set_default_navigation_timeout(120000)
    propertyLink = auction_house_card
    detail_url_page.goto(propertyLink)
    print(propertyLink)

    print(f"Iteration {i + 1}: {propertyLink}")

    house_image = detail_url_page.locator(
        "xpath=(//div[@class='gallery-img']//img)[1]")

    imagelink = house_image.get_attribute("src")
    # print(imagelink)

    number_of_bedrooms = detail_url_page.locator(
        "xpath=//h1[@class='single-property-title']").text_content()
    number_of_bedrooms = get_bedroom(number_of_bedrooms)
    print(number_of_bedrooms)

    price = detail_url_page.locator("//p[@class='single-property-price']").text_content()
    price, currency = prepare_price(price)

    # print(price)

    address = detail_url_page.locator(
        "xpath=(//div[@class='single-property-intro col--40']//p)[1]").text_content()
    # print(address)

    postal_code = address.split(',')[-1]

    tenure = detail_url_page.locator("xpath=//p[contains(.,'Tenure')]").text_content().split()[-1]
    print(tenure)

    description = detail_url_page.locator(
        "xpath=//div[@class='container container--medium']").text_content()
    if not tenure:
        tenure = get_tenure(description)

    title = detail_url_page.locator("xpath=//h1[@class='single-property-title']").text_content()

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
        "source": "iamsold.co.uk",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
    }
    print(data_hash)


def properties_scraper(page: Page, browser):
    while True:
        auction_house_cards = []
        prop_xpath = "xpath=//a[@class='u-link-cover']"

        anchor_locator = page.locator(prop_xpath)
        print(anchor_locator)
        for i in range(anchor_locator.count()):
            auction_house_href = anchor_locator.nth(i)
            auction_house_card = auction_house_href.get_attribute('href')
            auction_house_cards.append(auction_house_card)

        detail_url_page: Page = browser.new_page()
        detail_url_page.wait_for_load_state()
        for i, auction_house_card in enumerate(auction_house_cards):
            try_count = 0
            while True:
                try_count += 1
                property_scraper(detail_url_page, i, auction_house_card)
                print(auction_house_card)

        detail_url_page.close()


def run():
    with browser_context(headless=False) as (page, browser):
        page.set_default_navigation_timeout(120000)
        page.goto(start_url)
        properties_scraper(page, browser)


if __name__ == "__main__":
    run()
