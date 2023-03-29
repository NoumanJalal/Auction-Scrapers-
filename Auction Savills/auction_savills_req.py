from auction_scraper_base import *
import requests
from lxml import html
import re
import openpyxl
import csv
import json

payload = {}
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,nl;q=0.7',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Cookie': 'PHPSESSID=t25j5e24dbo5ug0vnf2k9k7r41; _ga=GA1.3.1072601377.1677828500; '
              '_gid=GA1.3.2013916700.1677828500; eu-accept-cookies=1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 '
                  'Safari/537.36',
    'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
}


def property_scraper(property_link):
    response = requests.request("GET", property_link, headers=headers, data=payload, timeout=10)
    detail_page_result = html.fromstring(response.content)

    print(property_link)

    # image_link = detail_page_result.xpath("(//li[contains(@data-slick-index,'')]/img)[1]")[0].attrib["src"]

    price = detail_page_result.xpath("//span[contains(text(),'£')]")[0].text_content()
    price, currency = prepare_price(price)

    address = detail_page_result.xpath("(//div[@class='sv-property-intro__address-block']/div)[1]")[0].text_content()
    postal_code = parse_postal_code(address)
    print(address)

    description = detail_page_result.xpath("//div[@class='description-paragraph']")[0].text_content()
    number_of_bedrooms = get_bedroom(description)
    tenure = detail_page_result.xpath("//p[contains(text(),'Fr')]")[0].text_content()

    title = detail_page_result.xpath(
        "(//div/p)[2]")[0].text_content()

    property_type = get_property_type(description)

    if property_type == "other":
        property_type = get_property_type(description)

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
        # "picture_link": image_link,
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


def properties_scraper(url):
    response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
    results = html.fromstring(response.content)

    result_page = results.xpath("//a[.='Full details']")

    for propertyLink in result_page:
        property_link = propertyLink.attrib["href"]
        property_scraper(property_link)


def run():
    url = "https://auctions.savills.co.uk/"
    properties_scraper(url)


if __name__ == "__main__":
    run()
