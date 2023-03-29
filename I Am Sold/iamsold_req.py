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


def property_scraper(property_url):
    property_link = f"https://www.iamsold.co.uk{property_url}"
    response = requests.request("GET", property_link, headers=headers, data=payload, timeout=10)
    detail_page_result = html.fromstring(response.content)

    print(f"Property Link = {property_link}")

    imagelink = detail_page_result.xpath(
        "(//div[@data-bkimage])[last()]")[0].attrib["data-bkimage"]

    number_of_bedroom = detail_page_result.xpath(
        "//ul[@class='nolist p__rooms']/li[contains(.,' bedroom')]")[0].text_content()
    number_of_bedrooms = get_bedroom(number_of_bedroom)

    number_of_bathroom = detail_page_result.xpath(
        "//ul[@class='nolist p__rooms']/li[contains(.,' bathroom')]")[0].text_content()
    number_of_bathrooms = get_bathroom(number_of_bathroom)

    price = detail_page_result.xpath("(//span[@class='current_price'])[1]")[0].text_content()
    price, currency = prepare_price(price)

    address = detail_page_result.xpath("//div[@class='c__property__address p__property__address']/p")[0].text_content()
    postal_code = address.split(',')[-1]

    tenure = detail_page_result.xpath("(//table[@class='p__table']//td)[4]")[0].text_content()

    partial_description = detail_page_result.xpath("(//div[@class='p__readmore__wrap']/p)[1]")[0].text_content()

    title = detail_page_result.xpath("//h1[@class='p__property__title']")[0].text_content()

    property_type = get_property_type(title)

    if property_type == "other":
        property_type = get_property_type(partial_description)

    data_hash = {
        "price": price,
        "currency_type": currency,
        "picture_link": imagelink,
        "property_description": partial_description,
        "property_link": property_link,
        "address": address,
        "postal_code": postal_code,
        "auction_venue": "online",
        "source": "iamsold.co.uk",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
        "number_of_bathrooms": number_of_bathrooms
    }
    print(data_hash)

    return data_hash


def properties_scraper(url):
    response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
    results = html.fromstring(response.content)
    result_auctions = results.xpath("//div[contains(@id, 'property') and .//li[@class='auctionTime']]"
                                    "//a[@class='c__property__imgLink']")

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('iamsold_req.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("iamsold_req.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    list_dict = []

    for auction in result_auctions:
        property_url = auction.attrib["href"]
        result_dict = property_scraper(property_url)
        result_list = list(result_dict.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        list_dict.append(result_dict)
        workbook.save("iamsold_req.xlsx")

    json_result = json.dumps(list_dict)
    json_fh.write(json_result)
    json_fh.close()
    workbook.close()
    csv_fh.close()


def run():
    url = "https://www.iamsold.co.uk/properties/all/aberdeenshire/?search_id=bdd20b95a679410294dbac10f300505a"
    properties_scraper(url)


if __name__ == "__main__":
    run()
