import csv
import json
import tempfile

import geojson
import requests

from stock_data.company import Company
from stock_data.google_maps_api import get_coordinates


def get_sp500(csvurl, print_output=True):
    r = requests.get(csvurl)
    f = tempfile.NamedTemporaryFile('wb')
    f.write(r.content)

    with open(f.name, 'rt', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        tickers = []
        for row in csvreader:
            if print_output:
                print(', '.join(row))
            if row[0] != 'Symbol':
                tickers.append(row[0])
    f.close()
    return tickers

def get_price_data(ticker):
    url = "https://api.iextrading.com/1.0/stock/" + ticker + "/quote"
    response = requests.get(url=url)
    responseString = response.content.decode('utf-8')
    try:
        responseObject = json.loads(responseString)
    except:
        return None
    return Company(marketCap=responseObject["marketCap"], symbol=responseObject["symbol"], companyName=responseObject["companyName"])

def get_feature(company):
    company_location = get_coordinates(company.companyName + " Headquarters")
    try:
        my_point = geojson.Point((company_location.location["lat"], company_location.location["lng"]))
        my_feature = geojson.Feature(geometry=my_point, properties={"mag": company.marketCap, "companyName": company.companyName})
        return my_feature
    except:
        return None

def get_feature_collection(companies):
    features = []
    for company in companies:
        features.append(get_feature(company))
    return geojson.FeatureCollection(features)

tickers = get_sp500("https://datahub.io/core/s-and-p-500-companies/r/constituents.csv")

features = []
# try to display location for first 10 of 500 companies
for ticker in tickers[:10]:
    company = get_price_data(ticker)
    if company == None:
        continue
    feature = get_feature(company)
    if feature == None:
        continue
    features.append(feature)
    print(geojson.dumps(feature))
    company_location = get_coordinates(company.companyName + " Headquarters")
    if company_location != None:
        print(company.companyName + " is located in " + company_location.formatted_address)
    else:
        print("Unable to get location for: " + company.companyName)
    feature_collection = geojson.FeatureCollection(features)