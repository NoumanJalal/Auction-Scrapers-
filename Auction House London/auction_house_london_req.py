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


def property_scraper(page_list):
    detail_page_attribute = page_list.attrib["href"]
    detail_page_url = f"https://auctionhouselondon.co.uk{detail_page_attribute}"
    response = requests.request("GET", detail_page_url, headers=headers, data=payload, timeout=10)
    detail_page_result = html.fromstring(response.content.decode('utf8'))

    propertyLink = detail_page_url
    print(propertyLink)

    imagelink = \
        detail_page_result.xpath("(//div[@class='absolute inset-0 bg-no-repeat bg-center bg-contain'])[2]")[0].attrib[
            'style']
    my_string = imagelink
    my_string = my_string.replace('background-image:url(', '')
    my_string = my_string.replace(')', '')
    imagelink = my_string.strip()

    print(imagelink)

    guidePrice = detail_page_result.xpath("(//p[contains(text(),'£')])[1]")[0].text_content()
    print(guidePrice)
    price, currency = prepare_price(guidePrice)

    description = detail_page_result.xpath("//div[@class='pt-25 max-w-810']")[0].text_content()

    address = detail_page_result.xpath("//div[@class='md:pl-20 py-10 md:py-0']")[0].text_content()
    postal_code = address.split(',')[-1]

    numbers_of_bedrooms = detail_page_result.xpath("(//div[@class='text-17 xl:text-19 mb-15'])[1]")[0].text_content()
    number_of_bedrooms = get_bedroom(numbers_of_bedrooms)

    if number_of_bedrooms is None:
        number_of_bedrooms = get_bedroom(description)

    property_type = get_property_type(description)
    if property_type == "other" and "land" in address.lower():
        property_type = "land"
    if "land" in address.lower():
        address = re.search(r"(?<= to ).*|(?<= of ).*|(?<= at ).*", address, re.IGNORECASE)
        if address:
            address = address.group().strip()

    tenure = detail_page_result.xpath("(//div[@class='text-17 xl:text-19 mb-15']/div)[1]")[0].text_content()

    if not tenure:
        tenure = get_tenure(description)

    data_hash = {
        "price": price,
        "currency_type": currency,
        "picture_link": imagelink,
        "property_description": description,
        "property_link": propertyLink,
        "address": address,
        "postal_code": postal_code,
        "auction_venue": "online",
        "source": "auctionhouselondon",
        "property_type": property_type,
        "number_of_bedrooms": number_of_bedrooms,
        "tenure": tenure,
    }
    return data_hash


def properties_scraper(url):
    response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
    list_page = html.fromstring(response.content)

    list_page_result = list_page.xpath("//a[@class='inline-flex items-center postblock__link ml-auto']")
    print(list_page_result)

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('auction_house_london_req.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("auction_house_london_req.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    for page_list in list_page_result:
        data = property_scraper(page_list)
        result_list = list(data.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        jsonString = json.dumps(data)
        json_fh.write(jsonString)
        workbook.save("auction_house_london_req.xlsx")

    workbook.close()
    csv_fh.close()
    json_fh.close()


def run():
    url = "https://auctionhouselondon.co.uk/current-auction/"
    properties_scraper(url)


if __name__ == "__main__":
    run()
