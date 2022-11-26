"""
This class provides brief usage example of Free OCR API,
By providing interface to imaginary Automatic parking lot gates controller - gatekeeper.py.
It's writing to database and espousing three methods:

* async def read_number(self, f_name, **kwargs)
    Asynchronously post images depicting cars license plate
    to Free OCR API server and returns their numbers.

* def set_fuel(self)
    Randomly set fuel type from: 'gas', 'diesel' or 'benzine'

* verify_permission(self)
    The rules are:
    Public transportation vehicles may enter the parking lot (their license plates always end
    with 25 or 26).
    Digit numbers whose two last digits are 85/86/87/88/89/00, should not enter.
    If the license plate number consists of 7 digits, and ends with 0 or 5, he cannot enter.
"""

import requests
import json
import random
import aiohttp
import logging
from database import DB
from datetime import datetime

# create and configure logger
logging.basicConfig(filename="gatekeeper_api.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')

# creating logging object
logger = logging.getLogger()

# setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)

OCR_FREE_API = 'https://api.ocr.space/parse/image'


class LicensePlate:
    # two last digits access rules:
    allowed = (25, 26)
    not_allowed = (85, 86, 87, 88, 89, 00)

    def __init__(self):
        self.number = None
        self.permission = None
        self.fuel = None
        # create or use existing db
        self.db = DB(connect=True, drop=True, database='gatekeeper_api', user='root', password='123123', host='localhost')

    async def read_number(self, f_name, overlay='False', api_key='helloworld', language='eng'):
        logger.info("posting image file {} to: {}".format(f_name, OCR_FREE_API))
        try:
            with open(f_name, 'rb') as f:
                async with aiohttp.ClientSession() as session:
                    async with session.post(OCR_FREE_API,
                                             data={'file': f, 'isOverlayRequired': overlay,
                                                   'apikey': api_key,
                                                   'language': language,
                                                   }) as response:
                        data = await response.text()
        except FileNotFoundError or requests.exceptions.RequestException as e:
            logger.error(e)
            raise SystemExit(e)
        j_data = json.loads(data)
        if isinstance(j_data, dict) and len(j_data["ParsedResults"]) == 0 and \
                j_data["IsErroredOnProcessing"]:
            error = "OCR API Error: {}, OCRExitCode: {}".format(
                j_data["ErrorMessage"], j_data["OCRExitCode"])
            logger.error(error)
            raise SystemExit(error)
        elif isinstance(j_data, str):
            error = "OCR API Error: {}".format(j_data)
            logger.error(error)
            raise SystemExit(error)

        # get text from json
        text = j_data["ParsedResults"][0]["ParsedText"]
        logger.info("the text read from image is: {}".format(text))
        # convert to number
        self.number = ''.join(
            i for i in text.split('\r\n')[0] if i.isdigit())

    def set_fuel(self):
        fuel_type = ('gas', 'diesel', 'benzine')
        self.fuel = fuel_type[random.randint(0, len(fuel_type) - 1)]
        logger.info("the random fuel was set to: {}".format(self.fuel))

    def verify_permission(self):
        if len(self.number) == 7 and self.number[-1] in (0, 5) or \
                self.number[-2:] not in self.allowed \
                or self.number[-2:] in self.not_allowed:
            self.permission = 'no'
        else:
            self.permission = 'yes'
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        # insert to db
        self.db.insert("gatekeeper_api",
                       {'plate_no': int(self.number), 'fuel_type': self.fuel,
                        'permission': self.permission, 'dt': formatted_date},
                       debug=False)
        logger.info("writing to database, permission: {}".format(self.permission))
