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


def properties_scraper(url):
    response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
    list_page_result = html.fromstring(response.content)
    result_divs = list_page_result.xpath("//a[contains(.,'plus fees')]")

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('auctionhouse.co.uk_selenium.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("auctionhouse.co.uk_selenium.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    for result in result_divs:
        detail_page_url = result.attrib["href"]
        response = requests.request("GET", detail_page_url, headers=headers, data=payload, timeout=10)
        result = html.fromstring(response.content.decode('utf8'))

        propertyLink = detail_page_url
        print(propertyLink)

        imagelink = result.xpath("(//img[@alt='Lot Image'])[1]")[0].attrib['src'].strip()
        guidePrice = result.xpath("//b[contains(., '* Guide')] | //li[contains(., '* Guide')] | //span[contains(., "
                                  "'*Guide')]")[0].text_content().strip()
        price, currency = prepare_price(guidePrice)

        description_list = []

        desc_elements = result.xpath("//div[@class='preline'] | //h4["
                                     ".='Description']/following-sibling::*[.!='']")
        description = ""
        for desc_element in desc_elements:
            description_list.append(desc_element.text_content())
            description = "".join(description_list)
        try:
            bedrooms = result.xpath("//li[contains(., 'Bedroom')]")[0].text_content().strip()
            number_of_bedrooms = get_bedroom(bedrooms)

        except:
            bedrooms = None
            number_of_bedrooms = None

        if bedrooms is None:
            number_of_bedrooms = get_bedroom(description)

        property_type = get_property_type(description)
        address = result.xpath("(//div[@class='container'])[3]//b")[0].text_content().strip()
        postal_code = address.split(',')[-1]
        print(address)
        if property_type == "other" and "land" in address.lower():
            property_type = "land"
        if "land" in address.lower():
            address = re.search(r"(?<= to ).*|(?<= of ).*|(?<= at ).*", address, re.IGNORECASE)
            if address:
                address = address.group().strip()
        tenure = result.xpath("//p[contains(.,'Tenure')]")[0].text_content().split()[-1]
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
            "source": "auctionhouse.co.uk",
            "property_type": property_type,
            "number_of_bedrooms": number_of_bedrooms,
            "tenure": tenure,
        }
        print(data_hash)

        result_list = list(data_hash.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        jsonString = json.dumps(data_hash)
        json_fh.write(jsonString)
        workbook.save("auctionhouse.co.uk_request.xlsx")

    workbook.close()
    csv_fh.close()
    json_fh.close()


def run():
    url = "https://www.auctionhouse.co.uk/auction/search-results?searchType=0"
    properties_scraper(url)


if __name__ == "__main__":
    run()
