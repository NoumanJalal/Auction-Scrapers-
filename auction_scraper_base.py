import contextlib
import inspect
import os
import re
from datetime import datetime
import dateparser
from playwright.sync_api import sync_playwright
from price_parser import Price
import json
from json import JSONDecodeError



def load_json(content):
    try:
        json_data = json.loads(content)
        return json_data
    except JSONDecodeError as ex:
        raise Exception(f"Unable to load JSON with content = {content}, with exception {ex}")


def get_text(nodes, index, xpath):
    try:
        return nodes.xpath(xpath)[index].text_content().strip()
    except Exception as e:
        e.args += (xpath,)
        try:
            filenames = ", ".join({os.path.basename(s.filename) for s in inspect.stack() if r"scrappers" in s.filename})
        except Exception as ex:
            print(f"error while fetching filenames: {ex}")
            filenames = ""
        return None


leashold_re = re.compile(
    r"\b"
    + r"\b|\b".join(
        map(
            lambda v: v.replace(" ", r"[\s -]+"),
            ["currently let", "leasehold", "tenant-in-situ", "tenanted", "tenant", "tenancy"],
        )
    )
    + r"\b",
    flags=re.I,
)

freehold_re = re.compile(
    r"\b"
    + r"\b|\b".join(map(lambda v: v.replace(" ", r"[\s -]+"), ["freehold", "A vacant three bedroom end-terrace"]))
    + r"\b",
    flags=re.I,
)


def get_tenure(tenure_str):
    if tenure_str is None:
        return None
    tenure_str = tenure_str.lower()
    if freehold_re.search(tenure_str):
        return "Freehold"
    elif leashold_re.search(tenure_str):
        return "Leasehold"
    else:
        return None


def get_attrib(node, xpath, index, attribute):
    try:
        return node.xpath(xpath)[index].attrib[attribute]
    except Exception as e:
        print(f"could not find Attribute with Xpath = {xpath}, with exception {e}")
        return ""


def currency_iso_name(currency):
    symbols = {
        "£": "GBP",
        "$": "USD",
    }
    try:
        return symbols[currency]
    except Exception as e:
        e.args += (currency,)
        return None


def prepare_price(price):
    price_obj = Price.fromstring(price)
    price = price_obj.amount_float
    currency = price_obj.currency
    currency = currency_iso_name(currency)
    return price, currency


def parse_auction_date(auction_date_str, **kwargs):
    auction_date = dateparser.parse(auction_date_str, **kwargs)
    if auction_date is not None:
        return auction_date
    raise Exception(f'Unable to parse date from "{auction_date_str}" string')


def parse_uk_date(text):
    match = re.search(r"(\d+)/(\d+)/(\d+)", text)
    if not match:
        raise Exception(f'Unable to parse date from "{text}" string')
    dt = datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)))
    return dt


def parse_postal_code(text):
    try:
        return re.search(r"(\w+\s\w+)\s*$", text).group(1)
    except BaseException as be:
        be.args = be.args + (text)
        return None


property_types_re = re.compile(
    r"|".join(
        map(
            lambda v: v.replace(" ", r"[\s -]+"),
            [
                "commercial",
                "retail",
                "industrial",
                "office",
                "medical",
                "end of terrace house",
                "house end of terrace",
                "end of terrace",
                "end terrace",
                "mid terrace",
                "middle terrace",
                "terraced house",
                r"\bterraced?",
                "land",
                r"\bflat\b",
                "house semi detached",
                "semi detached house",
                "semi detached",
                "detached house",
                "detached bungalow",
                "detached",
                r"\bshop\b",
                "cottage",
                "apartment",
                "bungalow",
                "studio",
                r"\bhouse",
            ],
        )
    ),
    flags=re.I,
)
property_types_map = {
    "house semi detached": "semi detached house",
    "house end of terrace": "end of terrace house",
    "end of terrace": "end of terrace house",
    "middle terrace": "mid terrace",
    "terraced": "terrace",
    "retail": "commercial",
    "industrial": "commercial",
    "office": "commercial",
    "medical": "commercial",
}


def get_property_type(text):
    if match := property_types_re.search(text):
        property_type = match.group().replace("-", " ").lower()
        if property_type in property_types_map:
            property_type = property_types_map[property_type]
        return property_type
    return "other"


def fix_br_tag_issue(doc):
    for br in doc.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"


numbers_words_to_int_map = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "double": 2,
}


def convert_words_to_integer(word):
    try:
        return numbers_words_to_int_map[word.strip().lower()]
    except BaseException as be:
        try:
            return int(word.strip())
        except BaseException as de:
            de.args = de.args + be.args + (word,)
    return None


def get_bedroom(text):
    numRooms = re.search(
        r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|double)\+?\s*(?:double +)?-?bed(?:room)?s?|bed(?:room)?s?:? *(\d+\+?)",
        text,
        re.IGNORECASE,
    )
    if numRooms:
        if numRooms.group(1) is not None:
            return convert_words_to_integer(numRooms.group(1).strip())
        elif numRooms.group(2) is not None:
            return int(numRooms.group(2))
    return None


def get_bathroom(text):
    numRooms = re.search(
        r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|double)\+?\s*(?:double +)?-?bath(?:room)?s?|bath(?:room)?s?:? *(\d+\+?)",
        text,
        re.IGNORECASE,
    )
    if numRooms:
        if numRooms.group(1) is not None:
            return convert_words_to_integer(numRooms.group(1).strip())
        elif numRooms.group(2) is not None:
            return int(numRooms.group(2))
    return None


def get_bedroom_v2(text):
    match = re.search(
        r"(\d+\s?(?:/\s?\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|double)\+?\s*(?:double +)?-?bed(?:room)?s?|bed(?:room)?s?:? *(\d+\+?)",
        text,
        re.IGNORECASE,
    )
    if match:
        if (grp1 := match.group(1)) is not None:
            if "/" in grp1:
                return int(grp1.split("/")[0])
            return convert_words_to_integer(grp1)
        elif match.group(2) is not None:
            return int(match.group(2))
    return None


def get_beds_type_tenure(tenure, property_type, no_of_beds, description):
    if tenure is None:
        tenure = get_tenure(description)
    if property_type:
        property_type_temp = get_property_type(property_type)
        if property_type_temp == "other":
            property_type_temp = get_property_type(description)
        if property_type_temp != "other":
            property_type = property_type_temp
    else:
        property_type_temp = get_property_type(description)
        if property_type_temp != "other":
            property_type = property_type_temp
        if property_type is None:
            property_type = "other"
    if no_of_beds is None:
        no_of_beds = get_bedroom(description)
    return tenure, property_type, no_of_beds


def clean_date_time_txt(auction_date_text):
    for word in re.split(r"\s", auction_date_text):
        if word == "":
            continue
        if not re.search(
                r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:tember)?|"
                r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)|\d+(?:st|nd|rd|th)\b|\d+(?::|\.)\d+\s*(?:am|pm)|\b\d+\b",
                word,
        ):
            auction_date_text = re.sub(rf"\s?\b{word}\b\s?", " ", auction_date_text)
    return auction_date_text


@contextlib.contextmanager
def browser_context(headless=True):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.set_default_timeout(60000)
        try:
            yield page, browser
        finally:
            print(f"Going to close page and browser")
            page.close()
            browser.close()
            print(f"Page and browser closed")
