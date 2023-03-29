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


def property_scraper(list_url):
    property_link = list_url.attrib["href"]
    response = requests.request("GET", property_link, headers=headers, data=payload, timeout=10)
    detail_page_result = html.fromstring(response.content.decode('utf8'))

    print(property_link)

    image_link = detail_page_result.xpath("(//div[@class='slick-track']//img)[1]")[0].attrib['src']

    guidePrice = detail_page_result.xpath("//h2[contains(@class,'PropertyHeader-price-value')]")[0].text_content()
    price, currency = prepare_price(guidePrice)

    description = detail_page_result.xpath("//div[contains(@class,'Content px-2 px-md-0')]")[0].text_content()

    title = detail_page_result.xpath("//div[contains(@class,'PropertyHeader-description ')]")[0].text_content()

    address = detail_page_result.xpath("//div[contains(@class,'PropertyHeader-description ')]/h1")[0].text_content()
    postal_code = address.split(',')[-1]

    numbers_of_bedrooms = detail_page_result.xpath(
        "(//div[contains(@class,'PropertyHeader-description ')]/p)[2]")[0].text_content()
    number_of_bedrooms = get_bedroom(numbers_of_bedrooms)

    tenure = detail_page_result.xpath("(//div[contains(@class,'my-4')])[4]")[0].text_content()

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


def properties_scraper(url):
    response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
    list_page = html.fromstring(response.content)

    list_page_result = list_page.xpath("//a[@class='PropertyCard']")
    print(list_page_result)

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('bond_wolf_request.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("bond_wolf_request.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    list_dict = []
    for list_url in list_page_result:
        result_dict = property_scraper(list_url)
        result_list = list(result_dict.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        list_dict.append(result_dict)
        workbook.save("bond_wolf_request.xlsx")

    json_result = json.dumps(list_dict)
    json_fh.write(json_result)
    json_fh.close()


def run():
    url = "https://www.bondwolfe.com/auctions/properties/?location=&minprice=&maxprice=&type="
    properties_scraper(url)


if __name__ == "__main__":
    run()
