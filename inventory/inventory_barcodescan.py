'''
This script will create a new inventory.csv file in the Downloads folder and a logging file to keep track of scans.
It then prompts the user for input for the Asset Tag, Serial Number, MAC Address, and User.
This is meant to be used with a barcode scanner with the input ending in a newline.
'''


# "https://develop.snipeitapp.com/api/v1/hardware/1234/checkin"

import requests
import os
import csv
import time
import logging
from dotenv import load_dotenv

load_dotenv()

outputfolder = os.getenv("DOWNLOADS_FOLDER")
csvfilename = "inventory.csv"

logging.basicConfig(filename='barcode_scan.log',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d, %(levelname)s, %(module)s, %(funcName)s, %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    )

def csvcreator(csvfilename, headers):
    csvfile = os.path.join(os.path.sep, outputfolder, csvfilename)
    with open(csvfile, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        logging.info('Wrote headers ' + str(headers))
        f.close()

def csvwriter(csvfilename, row):
    csvfile = os.path.join(os.path.sep, outputfolder, csvfilename)

    with open(csvfile, 'a', newline='') as f:  # Changed 'w' to 'a', otherwise was overwriting everything
        writer = csv.writer(f)
        writer.writerow(row)
        logging.info('Wrote row: ' + str(row))
        f.close()

def scanbarcode():
    assetTag = ''
    serialNumber = ''
    user = ''

    if os.path.exists(os.path.join(os.path.sep, outputfolder, csvfilename)):
        return
    else:
        headers = ["AssetTag", "SerialNumber", "MAC", "User"]
        csvcreator(csvfilename, headers)

    while assetTag != 'exit':
        print('')
        print('==========================')
        user = input("User: ")
        if user == 'exit':
            break
        assetTag = input("Asset Tag: ")
        if assetTag == 'exit':
            break
        serialNumber = input("Serial Number: ")
        if serialNumber == 'exit':
            break
        macAddress = input("MAC Address: ")
        if macAddress == 'exit':
            break
        
        row = [assetTag, serialNumber, macAddress, user]

        csvwriter(csvfilename, row)
        print("Added asset " + assetTag)

    else:
        print('Exiting...')

def main():
    scanbarcode()

if __name__ == '__main__':
    main()