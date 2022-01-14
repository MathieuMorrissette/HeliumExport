# Written by Mathieu Morrissette

import requests 
import json
import csv
import io
from datetime import datetime

print("Helium wallet activity exporter.")
address = input("Enter your Helium wallet address:")
print("Time must be in ISO 8601 format ex: 2021-12-31T23:59:99Z.\r\nKeep it empty to retrieve all activity.")
min_time = input("Min time (optional): ")
max_time = input("Max time (optional): ")

if address == "":
    print("Please provide an address!")
    exit(1)


def convertDCToHNT(dc):
    res = dc/100000000
    return "{:.8f}".format(res) # convert to string and remove scientific notation.

def getAddressActivity(address, min_time, max_time):
    done = False
    cursor = None

    # Todo add some throttling to prevent hammering the Helium api. (ex 1 req per sec)
    data = []

    params = {}
    req = "https://api.helium.io/v1/accounts/" + address + "/activity"

    while(not done):

        if min_time != "":
            params["min_time"] = min_time
        if max_time != "":
            params["max_time"] = max_time
       
        datareq = json.loads(requests.get(req, params=params).text)

        data = data + datareq["data"]

        if("cursor" in datareq):
           params["cursor"] = datareq["cursor"]
        else:
            # no cursor means no remaining data
            done = True

    return data

# Format in CryptoTaxCalculator
def formatActivity(dataparam):

    formatted = []

    for entry in dataparam:
        template = {
            "Timestamp (UTC)" : "",
            "Type" : "",
            "Base Currency" : "HNT",
            "Base Amount" : "",
            "Quote Currency (Optional)" : "",
            "Quote Amount (Optional)" : "",
            "Fee Currency (Optional)" : "HNT",
            "Fee Amount (Optional)" : "",
            "From (Optional)" : "",
            "To (Optional)" : "",
            "ID (Optional)" : "",
            "Description (Optional)" : ""
        }

        template["Timestamp (UTC)"] = datetime.fromtimestamp(entry["time"]).strftime("%d/%m/%Y %H:%M:%S")
        
        total = 0

        if(entry["type"] == "rewards_v2"):
            template["Type"] = "mining"

            for reward in entry["rewards"]:
                total += reward["amount"]

        if(entry["type"] == "payment_v2"):
            template["Type"] = "transfer-out"

            for payment in entry["payments"]:
                total += payment["amount"]

        if(entry["type"] == "assert_location_v2"):
            template["Type"] = "transfer-out" # Asserting location only cost a fee.
            
        template["Base Amount"] = convertDCToHNT(total)

        if "fee" in entry:
            template["Fee Amount (Optional)"] = convertDCToHNT(entry["fee"])

        formatted.append(template)

    return formatted


dataactivity = getAddressActivity(address, min_time, max_time)

f = open("helium.json", "w") # write raw data to helium.json
f.write(json.dumps(dataactivity))
f.close()

formatted = formatActivity(dataactivity)

fcsv = open("helium.csv", "w") # write formatted data to helium.csv
csv_writer = csv.writer(fcsv)
count = 0

for data in formatted:
    if count == 0:
        header = data.keys()
        csv_writer.writerow(header)
        count += 1

    csv_writer.writerow(data.values())

fcsv.close()

print(formatted)