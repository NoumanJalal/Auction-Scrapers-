from auction_scraper_base import *
import requests
from lxml import html
import re
import openpyxl
import csv
import json

payload = {}
headers = {
  'authority': 'www.suttonkersh.co.uk',
  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
            'application/signed-exchange;v=b3;q=0.7',
  'accept-language': 'en-GB,en;q=0.9',
  'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"Windows"',
  'sec-fetch-dest': 'document',
  'sec-fetch-mode': 'navigate',
  'sec-fetch-site': 'none',
  'sec-fetch-user': '?1',
  'upgrade-insecure-requests': '1',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 '
                'Safari/537.36',
  'Cookie': 'HttpOnly'
}


def property_scraper(property_url):
    property_link = f"https://www.venmoreauctions.co.uk/{property_url}"
    response = requests.request("GET", property_link, headers=headers, data=payload, timeout=10)
    detail_page_result = html.fromstring(response.content)

    print(property_link)

    image_link = detail_page_result.xpath("(//img[@class='img_resp'])[1]")[0].attrib["src"]
    print(image_link)

    price = detail_page_result.xpath(
        "//h2[contains(text(),'Guide Price ')]")[0].text_content()
    price, currency = prepare_price(price)

    address = detail_page_result.xpath(
        "//span[@class='font-thin f-paragon mini-2']")[0].text_content()
    postal_code = parse_postal_code(address)
    print(address)

    description = detail_page_result.xpath("//div[@class='marbot40']")[0].text_content()

    short_description = detail_page_result.xpath("//div[@class='marbot20']/p")[0].text_content()
    tenure = get_tenure(short_description)
    number_of_bedrooms = get_bedroom(short_description)

    title = detail_page_result.xpath("//span[@class='font-thin f-paragon mini-2']")[0].text_content()

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
        "picture_link": image_link,
        "property_description": description,
        "property_link": property_link,
        "address": address,
        "postal_code": postal_code,
        "auction_venue": "online",
        "source": "venmoreauctions",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure
    }
    return data_hash


def properties_scraper(url):
    response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
    results = html.fromstring(response.content)

    result_page = results.xpath("//span[contains(@class,'posrel')]/a")
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('venmorce_auction_req.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("venmorce_auction_req.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    list_dict = []

    for propertylink in result_page:
        property_url = propertylink.attrib["href"]
        result_dict = property_scraper(property_url)
        result_list = list(result_dict.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        list_dict.append(result_dict)
        workbook.save("venmorce_auction_req.xlsx")

    json_result = json.dumps(list_dict)
    json_fh.write(json_result)
    json_fh.close()
    workbook.close()
    csv_fh.close()


def run():
    url = "https://www.venmoreauctions.co.uk/Property-Search?pageNum=1"
    properties_scraper(url)


if __name__ == "__main__":
    run()
