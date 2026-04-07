import json, time
import requests
import pandas as pd

KANGAROO_KEY = 12019022
WOMBAT_KEY = 2440301
GBIF_URL = "https://api.gbif.org/v1/occurrence/search"


def main():
    get_gbif_data(WOMBAT_KEY)

    file_name = "vombatus_ursinus_sightings_gbif.json"

    with open(file_name, "r") as file:
        data = json.load(file)

    clean_data(data, file_name)


def get_gbif_data(species_key: int):
    offset = 0
    results = []

    while True:
        # parameters for Macropus giganteus in Australia
        params = {
            "taxonKey": species_key,
            "country": "AU",
            "hasCoordinate": "true",
            "limit": 300,
            "offset": offset,
        }

        print(f"Offset: {offset}")

        # sending the requests
        response = requests.get(GBIF_URL, params=params)

        # checking if the request was successful
        if response.status_code == 200:
            data = response.json()
            results.extend(data["results"])

            # stopping if it's the end of the dataset
            if data["endOfRecords"] or offset > 2500:
                break

            offset += 300
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return 1

        # for avoiding HTTP 429 error
        time.sleep(1)

    file_name = f"{results[0]['species'].lower().replace(' ', '_')}_sightings_gbif.json"

    # exporting the json file
    with open(file_name, "w") as file:
        json.dump(results, file)
    print(f"✅Data exported to {file_name} successfully. ")


def clean_data(data: list, file_name: str):
    # loading the dataframe
    df = pd.DataFrame(data)

    # only keeping rows in Australia
    df = df[df["countryCode"] == "AU"]

    # removing the unnecessary columns
    df = df[["species", "countryCode", "year", "decimalLatitude", "decimalLongitude"]]

    # renmaing the columns
    df = df.rename(
        columns={
            "decimalLatitude": "latitude",
            "decimalLongitude": "longitude",
        }
    )

    # removing rows with missing coordinates
    df = df.dropna(subset=["latitude", "longitude"])

    # removing duplicates
    df = df.drop_duplicates(subset=["latitude", "longitude"])

    print(df.info())

    # exporting the csv file
    df.to_csv(f"{file_name.replace('.json', '.csv')}", index=False)


main()
