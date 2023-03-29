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


def property_scraper(result):
    auction_url = result.xpath("//a[@class='u-link-cover']")[0].attrib["href"]
    response = requests.request("GET", auction_url, headers=headers, data=payload, timeout=10)
    result = html.fromstring(response.content.decode('utf8'))

    _url = auction_url
    print(_url)

    auction_image = result.xpath("(//div[@class='gallery-img']//img)[1]")[0].attrib['src'].strip()
    guidePrice = result.xpath("//p[@class='single-property-price']")[0].text_content().strip()
    guidePrice, currency = prepare_price(guidePrice)

    description = result.xpath("//div[@class='container container--medium']")[0].text_content().strip()

    beds_div = result.xpath("//h1[@class='single-property-title']")[0].text_content()
    no_of_beds = get_bedroom(beds_div)

    if no_of_beds is None:
        no_of_beds = get_bedroom(description)

    property_type = get_property_type(description)
    address = result.xpath("(//div[@class='single-property-intro col--40']//p)[1]")[0].text_content().strip()
    address = " ".join(address.split())
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
        "price": guidePrice,
        "currency_type": currency,
        "picture_link": auction_image,
        "property_description": description,
        "property_link": _url,
        "property_type": property_type,
        "tenure": tenure,
        "address": address,
        "no_of_beds": no_of_beds,
        "source": "https://www.agentspropertyauction.com/next-auction/",
    }

    return data_hash


def properties_scraper(url):
    response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
    results = html.fromstring(response.content)

    results_cards = results.xpath("//a[@class='u-link-cover']")
    print(results_cards)

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    csv_fh = open('agents_property_request.csv', mode='w', newline='', encoding='utf8')
    json_fh = open("agents_property_request.json", "w", encoding='utf8')
    csv_writer = csv.writer(csv_fh)

    for result in results_cards:
        data = property_scraper(result)
        result_list = list(data.values())
        worksheet.append(result_list)
        csv_writer.writerow(result_list)
        jsonString = json.dumps(data)
        json_fh.write(jsonString)
        workbook.save("agents_property_request.xlsx")

    workbook.close()
    csv_fh.close()
    json_fh.close()


def run():
    url = "https://www.agentspropertyauction.com/next-auction/"
    properties_scraper(url)


if __name__ == "__main__":
    run()
