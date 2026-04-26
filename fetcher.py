import json, os, time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# getting the variables from the .env file
KANGAROO_KEY = int(os.getenv("KANGAROO_KEY"))
WOMBAT_KEY = int(os.getenv("WOMBAT_KEY"))
KOALA_KEY = int(os.getenv("KOALA_KEY"))
KANGAROO_SCIENTIFIC_NAME = os.getenv("KANGAROO_SCIENTIFIC_NAME")
WOMBAT_SCIENTIFIC_NAME = os.getenv("WOMBAT_SCIENTIFIC_NAME")
KOALA_SCIENTIFIC_NAME = os.getenv("KOALA_SCIENTIFIC_NAME")
GBIF_URL = os.getenv("GBIF_URL")
ALA_URL = os.getenv("ALA_URL")


def main():
    f = get_ala_data(KANGAROO_SCIENTIFIC_NAME)
    clean_data(f)


def get_gbif_data(species_key: int) -> str:
    offset = 0
    results = []

    while True:
        params = {
            "taxonKey": species_key,
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
            results.extend(data["results"])

            # stopping if it's the end of the dataset
            if data["endOfRecords"] or offset > 10000:
                break
            offset += 300
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return 1

        print(f"Data Pulled: {offset}")
        # for avoiding HTTP 429 error
        time.sleep(1)
    if results:
        file_name = (
            f"{results[0]['species'].lower().replace(' ', '_')}_sightings_gbif.json"
        )

        # exporting the json file
        with open(file_name, "w") as file:
            json.dump(results, file)
        print(f"✅Data exported to {file_name} successfully. ")

        return file_name
    else:
        print("No results found.")
        return None


def get_ala_data(species_scientific_name: str) -> str:
    offset = 0
    results = []

    while True:
        params = {
            "q": species_scientific_name,
            "fq": ["country:Australia"],
            "pageSize": 500,  # records per page (max 1000)
            "startIndex": offset,  # for pagination
            "fl": "scientificName,month,year,stateProvince,raw_countryCode,decimalLatitude,decimalLongitude",  # fields to return
        }
        headers = {"Accept": "application/json"}

        # sending the requests
        response = requests.get(ALA_URL, params=params, headers=headers)

        # checking if the request was successful
        if response.status_code == 200:
            data = response.json()
            results.extend(data["occurrences"])

            # stopping if it's the end of the dataset
            if data["totalRecords"] < (offset + 500) or offset > 10:
                break
            offset += 500
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return 1

        print(f"Data Pulled: {offset}")
        # for avoiding HTTP 429 error
        time.sleep(1)

    if results:
        file_name = f"{results[0]['scientificName'].lower().replace(' ', '_')}_sightings_ala.json"

        # exporting the json file
        with open(file_name, "w") as file:
            json.dump(results, file)
        print(f"✅Data exported to {file_name} successfully. ")

        return file_name
    else:
        print("No results found.")
        return None


def clean_data(file_name: str):
    column_schema = [
        "species",
        "month",
        "year",
        "stateProvince",
        "countryCode",
        "decimalLatitude",
        "decimalLongitude",
    ]

    # loading the file
    with open(file_name, "r") as file:
        data: dict = json.load(file)

    # loading the dataframe
    df = pd.DataFrame(data)

    # for GBIF data
    try:
        # only keeping rows in Australia
        df = df[df["countryCode"] == "AU"]
        # removing the unnecessary columns
        df = df[column_schema]
    # for ALA data
    except KeyError:
        # only keeping rows in Australia
        df = df[df["raw_countryCode"] == "AU"]

        # renmaing the ala specific columns
        df = df.rename(
            columns={
                "scientificName": "species",
                "raw_countryCode": "countryCode",
            }
        )

        # ordering the column in correct schema
        df = df[column_schema]

    # renmaing the other columns
    df = df.rename(
        columns={
            "stateProvince": "state",
            "decimalLatitude": "latitude",
            "decimalLongitude": "longitude",
        }
    )

    # removing the countryCode column
    df = df.drop(columns=["countryCode"])

    # removing rows with missing values
    df = df.dropna(subset=["latitude", "longitude", "year", "month", "state"])

    # removing rows with older sighting data
    df = df.drop(df[df["year"] < 2020].index)

    # removing duplicates
    df = df.drop_duplicates(subset=["latitude", "longitude", "year", "month"])

    # removing the json file as it's pretty much useless
    os.remove(file_name)
    print(f"✅{file_name} removed successfully. ")

    file_name = file_name.replace(".json", ".csv")
    # exporting the csv file
    df.to_csv(f"{file_name}", index=False)
    print(f"✅Data exported to {file_name} successfully. ")


def merge_csv(new_file_name: str, file_names: list):
    df_list = []

    # loading all DataFrames in a single list
    for file_name in file_names:
        df_list.append(pd.read_csv(file_name))

    # merging the dfs all together
    merged_df = pd.concat(df_list, ignore_index=True)

    # removing duplicates
    merged_df = merged_df.drop_duplicates(
        subset=["species", "month", "year", "latitude", "longitude"]
    )

    # removing the old csv files
    for file_name in file_names:
        os.remove(file_name)

    # exporting the csv file
    merged_df.to_csv(new_file_name, index=False)

    print(f"✅{file_names} merged into {new_file_name} successfully. ")


if __name__ == "__main__":
    main()
