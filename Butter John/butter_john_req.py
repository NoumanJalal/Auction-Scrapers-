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
    detail_page_result = html.fromstring(response.content.decode('utf8'))

    print(property_link)

    house_image = detail_page_result.xpath("(//div[contains(@class,'slide__image')])[1]")[0].attrib['style']
    image_link = re.search(r'url\("?(.+)"?\)', house_image).group(1)
    print(image_link)

    guidePrice = detail_page_result.xpath("//span[2]//span[2]")[0].text_content()
    price, currency = prepare_price(guidePrice)

    description = detail_page_result.xpath("//div[contains(@class,'col-md-8')]")[0].text_content()

    partial_description = detail_page_result.xpath("(//div[contains(@class,'col-md-8')]/p)[1]")[0].text_content()
    postal_code = parse_postal_code(partial_description)

    address = detail_page_result.xpath("//h1[contains(@class,'section__title')]")[0].text_content()

    try:
        numbers_of_bedrooms = detail_page_result.xpath(
            "//li[contains(text(),'Bedroom')]")[0].text_content()
        number_of_bedrooms = get_bedroom(numbers_of_bedrooms)
    except:
        print(None)

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
        "source": "buttersjohnbee",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
        "title": title
    }
    return data_hash


def properties_scraper():
    global results
    page = 1
    while page <= 5:
        pageno = ""
        if page > 1:
            pageno = f"/page-{page}"
        url = f"https://www.buttersjohnbee.com/auction-properties/properties-for-sale-in-staffordshire-and-cheshire{pageno}"
        response = requests.request("GET", url, timeout=10)
        results = html.fromstring(response.content)
        page += 1

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('butter_john_req.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("butter_john_req.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    list_dict = []

    for auction in results.xpath("//div[@class='item infinite-item property for-sale-by-auction']//a"):
        property_url = auction.attrib["href"]

        property_link = f"https://www.buttersjohnbee.com{property_url}"
        result_dict = property_scraper(property_link)
        result_list = list(result_dict.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        list_dict.append(result_dict)
        workbook.save("butter_john_req.xlsx")

    json_result = json.dumps(list_dict)
    json_fh.write(json_result)
    json_fh.close()


if __name__ == "__main__":
    properties_scraper()
