import json, time
import requests


GBIF_URL = "https://api.gbif.org/v1/occurrence/search"


def main():
    get_gbif_data()


def get_gbif_data():
    offset = 0
    results = ""

    while True:
        # for avoiding HTTP 429 error
        time.sleep(1)

        # parameters for Macropus giganteus in Australia
        params = {
            "taxonKey": 2436775,
            "country": "AU",
            "hasCoordinate": "true",
            "limit": 300,
            "offset": offset,
        }

        # sending the requests
        response = requests.get(GBIF_URL, params=params)

        # checking if the request was successful
        if response.status_code == 200:
            data = response.json()
            results += str(data["results"])

            # stopping if it's the end of the dataset
            if data["endOfRecords"]:
                break
            offset += 300
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    # exporting the json file
    with open("wombat.json", "w") as file:
        json.dump(data, file)
    print("✅Data saved to data.json")


main()
