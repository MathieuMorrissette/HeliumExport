import requests 
import json
import csv
import io
from datetime import datetime

address = ""

def getAddressActivity(address):
    done = False
    cursor = None

    data = []

    while(not done):
        if cursor != None:
            datareq = json.loads(requests.get("https://api.helium.io/v1/accounts/" + address + "/activity?cursor=" + cursor + "&?min_time=2021-01-01T00:00:00Z&max_time=2021-12-31T00:00:00Z").text)
        else:
            datareq = json.loads(requests.get("https://api.helium.io/v1/accounts/" + address + "/activity?min_time=2021-01-01T00:00:00Z&max_time=2021-12-31T23:59:99Z").text)

        data = data + datareq["data"]

        if("cursor" in datareq):
            cursor = datareq["cursor"]
        else:
            done = True

    return data

# format in CryptoTaxCalculator
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
                total = reward["amount"]/100000000

        if(entry["type"] == "payment_v2"):
            template["Type"] = "transfer-out"

            for payment in entry["payments"]:
                total = payment["amount"]/100000000

        if(entry["type"] == "assert_location_v2"):
            template["Type"] = "transfer-out" # asserting location only cost a fee
            
        template["Base Amount"] = "{:.8f}".format(total) # remove scientific notation

        print(template["Base Amount"])
        if "fee" in entry:
            fee = entry["fee"]/100000000
            template["Fee Amount (Optional)"] = "{:.8f}".format(fee) # remove scientific notation

        #template["ID (Optional)"] = entry["hash"]

        formatted.append(template)

    return formatted


dataactivity = getAddressActivity(address)

f = open("helium.json", "w") # raw data
f.write(json.dumps(dataactivity))
f.close()

formatted = formatActivity(dataactivity)

fcsv = open("helium.csv", "w") # formatted data
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