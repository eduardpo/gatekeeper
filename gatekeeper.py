"""
This script provides driver for Gatekeeper api,
It accepts one optional parameter --m (multiple)
Free OCR API can be used only 10 number of times within 600 seconds
By crossing this limitation you will receive an error:
OCR API Error: You may only perform this action upto maximum 10 number of times within 600 seconds

Usage:

python gatekeeper.py --m    # for multiple gates, process all cars simultaneously

python gatekeeper.py        # single gate, car by car

"""

import os
import asyncio
import argparse
from gatekeeper_api import LicensePlate
from database import DB

INCOMING_CARS = 'incoming_cars'


async def process_car(f_name):
    car = LicensePlate()
    await car.read_number(f_name)
    car.set_fuel()
    car.verify_permission()
    print("car: {}, fuel_type: {}, permission: {}".format(car.number, car.fuel, car.permission))
    return car.permission


async def multiple_gates(plates):
    result = await asyncio.gather(*[process_car(
        os.path.join(INCOMING_CARS, plate)) for plate in plates])
    return result


# multiple gates, process all cars simultaneously
def multi_gate_op(plates):
    return asyncio.run(multiple_gates(plates))


# single gate, car by car
def single_gate_op(plates):
    result = []
    for plate in plates:
        result.append(asyncio.run(process_car(os.path.join(INCOMING_CARS, plate))))
    return result


if __name__ == '__main__':
    # parse arguments, with default as a single gate
    parser = argparse.ArgumentParser(description='Automatic parking lot gates controller program.')
    parser.add_argument('--m', help='multiple gates.', action='store_true')
    args = vars(parser.parse_args())
    # delete database
    DB(connect=True, database='gatekeeper_api', user='root', password='123123', host='localhost').drop()
    # get and store all cars' plates
    l_plates = [files for subdir, dirs, files in os.walk(INCOMING_CARS)][0]
    # run multiple or single gate operation
    if args['m']:
        multi_gate_op(l_plates)
    else:
        single_gate_op(l_plates)
