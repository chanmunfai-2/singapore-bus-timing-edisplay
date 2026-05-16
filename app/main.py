import os
import sys

from dotenv import load_dotenv

# Load environment variabless
load_dotenv()

# Setting up directories
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
import time
import holidays 
from datetime import datetime
from retrieve_telegram_message import check_telegram

import requests
from PIL import Image, ImageDraw, ImageFont

DEFAULT_MESSAGE = "Nothing is possible"
IGNORE_BUS_TIMING = False # Global state variable; to be controlled by Tele bot 
FRAME_X_OFFSET = 45 # offset from x-axis due to Ikea frame 

EPD_AVAILABLE = False 
try: # only for Linux devices like raspberry pi 
    from waveshare_epd import epd7in5_V2
    EPD_AVAILABLE = True  

except Exception as e: 
    print("Not running on Linux. Skipping EPD import")

logging.basicConfig(level=logging.DEBUG)

def get_bus_arrival(api_key, bus_stop_code):
    url = "https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival?BusStopCode=" + bus_stop_code
    headers = {
        'AccountKey': api_key,
        'accept': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        services = data.get("Services", [])
        bus_info = []
        
        for service in services:
            service_no = service["ServiceNo"]
            arrival_times = []
            for bus in ["NextBus", "NextBus2", "NextBus3"]:
                if service.get(bus):
                    eta = service[bus]["EstimatedArrival"]
                    if eta:
                        eta_time = datetime.strptime(eta, "%Y-%m-%dT%H:%M:%S%z")
                        time_diff = (eta_time - datetime.now(eta_time.tzinfo)).total_seconds() / 60
                        arrival_times.append(round(time_diff))
            if arrival_times:
                bus_info.append((service_no, arrival_times))
        return bus_info
    else:
        logging.error("Error: Unable to fetch data. Status code: " + str(response.status_code))
        return []

def display_bus_arrivals(epd, draw, font, bus_info_A, bus_info_B):
    draw.rectangle((0, 0, epd.width, epd.height), fill=255)  # Clear the display
    y = 20  # Initial Y position for text
    column_offset = epd.width // 2  # Divide the screen into two columns
    
    draw.text((120, y),"Downstairs", font=font, fill=0)

    # Display for Bus Stop A (left column)
    for service_no, arrival_times in bus_info_A:
        draw.rectangle((20 + FRAME_X_OFFSET, y+50, 180 + FRAME_X_OFFSET, y + 110), fill=0)
        draw.text((50 + FRAME_X_OFFSET, y + 58), service_no, font=font, fill=255)
        times_text = " | ".join(map(str, arrival_times))
        draw.text((220, y + 55), times_text, font=font, fill=0)
        y += 70
    
    y = 20  # Reset Y position for the right column

    draw.text((120+column_offset, y),"Opposite", font=font, fill=0)

    # Display for Bus Stop B (right column)
    for service_no, arrival_times in bus_info_B:
        draw.rectangle((20 + column_offset, y+50, 180 + column_offset, y + 110), fill=0)
        draw.text((50 + column_offset, y + 58), service_no, font=font, fill=255)
        times_text = " | ".join(map(str, arrival_times))
        draw.text((220 + column_offset, y + 55), times_text, font=font, fill=0)
        y += 70

    # Display time last updated
    now = datetime.now()
    formatted_time = now.strftime("%-I:%M %p, %d %b")
    time_text = "Last Updated: " + formatted_time
    draw.text((50 + FRAME_X_OFFSET, y), time_text, font=font, fill = 0)    
    
    epd.display(epd.getbuffer(Himage))

def display_center_message(epd, draw, font, message): 
    # Works for single line so far
    draw.rectangle((0, 0, epd.width, epd.height), fill=255)  # Clear the display

    # Get text size
    bbox = draw.textbbox((0,0), message, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (epd.width - text_width) // 2
    y = (epd.height - text_height) // 2

    draw.text((x,y), message, font=font, fill = 0)

    epd.display(epd.getbuffer(Himage))

def should_display_bus_timing(): 
    now = datetime.now()
    day_of_week = now.weekday() # 0 for Monday, ... 6 for Sunday

    current_hour = now.hour
    current_minute = now.minute
    current_time_in_minutes = current_hour * 60 + current_minute
    is_waking_hours = (7 <= current_hour <= 23) # 7:00 am to 11:59pm 

    sg_holidays = holidays.Singapore()
    is_public_holiday = now.date() in sg_holidays
    is_public_holiday_and_waking_hours = is_public_holiday and is_waking_hours

    is_weekend_and_waking_hours = day_of_week >=5 and is_waking_hours

    # Weekday Morning - 7:15am to 9:45am 
    morning_start = 7 * 60 + 15 # 715am 
    morning_end = 9 * 60 + 45 # 945am 
    is_weekday_morning = day_of_week <5 and (morning_start <= current_time_in_minutes <=morning_end)

    # Weekday Evening - 530pm to 715pm 
    evening_start = 17 * 60 + 30 # 530pm 
    evening_end = 19 * 60 + 30 # 715pm 
    is_weekday_evening = day_of_week <5 and (evening_start <= current_time_in_minutes <= evening_end)
    
    return is_weekend_and_waking_hours or is_public_holiday_and_waking_hours or is_weekday_evening or is_weekday_morning

if __name__ == "__main__": 

    api_key = os.getenv('API_KEY')
    bus_stop_code_A = os.getenv('BUS_STOP_CODE_A')
    bus_stop_code_B = os.getenv('BUS_STOP_CODE_B')

    if EPD_AVAILABLE is True:
        try: # EPD display is connected
            logging.info("Bus Arrival Display on E-Ink")
            epd = epd7in5_V2.EPD()
            
            logging.info("Init and Clear")
            epd.init()
            epd.Clear()

        # Using a larger and bold font
            font48 = ImageFont.truetype(os.path.join(picdir, 'OpenSans-Bold.ttf'), 0)
            Himage = Image.new('1', (epd.width, epd.height), 255)
            draw = ImageDraw.Draw(Himage)
            
            api_key = os.getenv('API_KEY')
            bus_stop_code_A = os.getenv('BUS_STOP_CODE_A')
            bus_stop_code_B = os.getenv('BUS_STOP_CODE_B')

            while True:
                msg = check_telegram() # can always check Telegram 
                if msg == "/ignore_bus": 
                    IGNORE_BUS_TIMING = True
                    print("Telegram Instruction: Ignore Bus Timing")
                elif msg == "/resume_bus": 
                    IGNORE_BUS_TIMING = False
                    print("Telegram Instruction: Resume Bus Timing")       

                #Display Bus Arrival
                if should_display_bus_timing() and not IGNORE_BUS_TIMING: 
                    bus_info_A = get_bus_arrival(api_key, bus_stop_code_A)
                    bus_info_B = get_bus_arrival(api_key, bus_stop_code_B)
                    display_bus_arrivals(epd, draw, font48, bus_info_A, bus_info_B)
                    time.sleep(60)  # Refresh every minute

                # Display Telegram Message 
                else: # outside of bus display timings
                    msg = check_telegram
                    if msg is None or msg == "/ignore_bus": 
                        msg = DEFAULT_MESSAGE
                    display_center_message(epd, draw, font48, msg)
                    time.sleep(60)

        except IOError as e:
            logging.error(e)
            
        except KeyboardInterrupt:
            logging.info("Exiting...")
            epd.Clear()
            epd7in5_V2.epdconfig.module_exit(cleanup=True)
            exit()

    else: # EPD_available is false 
        # Test Telegram and Bus Arrivals separately
        while True: 
            # Check for Telegram commands to ignore bus timings 
            msg = check_telegram() # can always check Telegram 
            if msg == "/ignore_bus": 
                IGNORE_BUS_TIMING = True
                print("Telegram Instruction: Ignore Bus Timing")
            elif msg == "/resume_bus": 
                IGNORE_BUS_TIMING = False
                print("Telegram Instruction: Resume Bus Timing")         

            # Display Bus Timings 
            if  should_display_bus_timing() and not IGNORE_BUS_TIMING: 
                bus_info_A = get_bus_arrival(api_key, bus_stop_code_A)
                bus_info_B = get_bus_arrival(api_key, bus_stop_code_B)
                print(bus_info_A, bus_info_B)

                time.sleep(10)  
            
            # Display Telegram Messages 
            else: 
                if msg and msg != "/ignore_bus":
                    print("Telegram message:", msg)
                else: print("Default Telegram message:", DEFAULT_MESSAGE)

                time.sleep(10)
                
        ### Test Telegram and Bus Arrivals together 
        # while True:
        #     msg = check_telegram()
        #     if msg:
        #         print("Telegram message:", msg)
        #     else: print("Default Telegram message:", DEFAULT_MESSAGE)

        #     bus_info_A = get_bus_arrival(api_key, bus_stop_code_A)
        #     bus_info_B = get_bus_arrival(api_key, bus_stop_code_B)
        #     print(bus_info_A, bus_info_B)
            
        #     time.sleep(10)  
                

        