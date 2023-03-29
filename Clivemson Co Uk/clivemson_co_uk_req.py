from auction_scraper_base import *
import requests
from lxml import html
import re
import openpyxl
import csv

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
    detail_page_result = html.fromstring(response.content.decode("utf8"))
    print(detail_page_result)

    print(property_link)
    house_image = detail_page_result.xpath("(//span[contains(@class,'image-placeholder')])[2]")[0].attrib['style']
    image_link = re.search(r'url\("?(.+)"?\)', house_image).group(1)
    print(image_link)

    guidePrice = detail_page_result.xpath("//strong[@class='lot-price']")[0].text_content()
    price, currency = prepare_price(guidePrice)

    description = detail_page_result.xpath("//section[contains(@class,'single-content')]")[0].text_content()

    address = detail_page_result.xpath("(//address[@class='lot-address'])[1]")[0].text_content()
    postal_code = parse_postal_code(address)

    numbers_of_bedroom = detail_page_result.xpath(
        "(//section[contains(@class,'single-content')]/p)[1]")[0].text_content()
    number_of_bedrooms = get_bedroom(numbers_of_bedroom)

    title = detail_page_result.xpath("//div[@class='section__meta']")[0].text_content()
    property_type = get_property_type(title)

    if number_of_bedrooms is None:
        number_of_bedrooms = get_bedroom(title)

    if property_type == "other" and "land" in address.lower():
        property_type = "land"
    if "land" in address.lower():
        address = re.search(r"(?<= to ).*|(?<= of ).*|(?<= at ).*", address, re.IGNORECASE)
        if address:
            address = address.group().strip()
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
        "source": "cliveemson",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
        "title": title
    }


def properties_scraper(results):
    for auction in results.xpath("//a[@class='tile-block-link']"):
        property_link = auction.attrib["href"]
        print(property_link)
        property_scraper(property_link)


def run():
    url = "https://www.cliveemson.co.uk/properties/"
    response = requests.request("GET", url, timeout=10)
    results = html.fromstring(response.content)
    properties_scraper(results)


if __name__ == "__main__":
    run()
