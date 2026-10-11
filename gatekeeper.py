import os
import asyncio
import argparse
from gatekeeper_api import LicensePlate
from database import DB

INCOMING_CARS = 'incoming_cars'


async def process_car(f_name):
    car = LicensePlate()
    await car.read_number(f_name)   # Asynchronous, needs await for remote OCR API call
    car.set_fuel()                  # Synchronous, no await
    await car.verify_permission()   # Asynchronous, needs await for database verification
    # Optional: Add a small delay if you want to avoid tripping strict firewalls
    await asyncio.sleep(1) 
    print("car: {}, fuel_type: {}, permission: {}".format(car.number, car.fuel, car.permission))
    return car.permission


# --- MULTIPLE GATES (CONCURRENT) ---
async def multiple_gates(plates):
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for plate in plates:
            path = os.path.join(INCOMING_CARS, plate)
            task = tg.create_task(process_car(path))
            tasks.append(task)
    return [task.result() for task in tasks]

def multi_gate_op(plates):
    return asyncio.run(multiple_gates(plates))


# --- SINGLE GATE (SEQUENTIAL) ---
async def sequential_gates(plates):
    result = []
    for plate in plates:
        # Standard 'await' inside a loop ensures they run one strictly after the other
        res = await process_car(os.path.join(INCOMING_CARS, plate))
        result.append(res)
    return result

def single_gate_op(plates):
    # Only call asyncio.run ONCE to spin up the loop for the entire sequence
    return asyncio.run(sequential_gates(plates))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Automatic parking lot gates controller program.')
    parser.add_argument('--m', help='multiple gates.', action='store_true')
    args = vars(parser.parse_args())
    
    # DB cleanup
    DB(connect=True, database='gatekeeper_api', user='root', password='123123', host='localhost').drop()
    
    # Get all cars' plates safely
    l_plates = [files for subdir, dirs, files in os.walk(INCOMING_CARS)][0]
    
    if args['m']:
        print(f"Starting concurrent processing for {len(l_plates)} cars...")
        multi_gate_op(l_plates)
    else:
        print(f"Starting sequential processing for {len(l_plates)} cars...")
        single_gate_op(l_plates)
