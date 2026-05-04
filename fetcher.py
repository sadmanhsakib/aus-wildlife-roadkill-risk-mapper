import os, time
import requests
import pandas as pd

# GBIF KEYS
KANGAROO_RED_KEY = 12019022
KANGAROO_GREY_KEY = 5219981
WALLABY_SWAMP_KEY = 2440149
WALLABY_RED_NECKED_KEY = 9589697
WOMBAT_KEY = 2440301
KOALA_KEY = 2440012
POSSUM_BRUSHTAIL_KEY = 2440254
POSSUM_RINGTAIL_KEY = 2440062
BANDICOOT_BROWN_KEY = 2435311
ECHIDNA_KEY = 2433378
PLATYPUS_KEY = 2433376
# Scientific Names for ALA
KANGAROO_RED_SCIENTIFIC_NAME = "Osphranter rufus"
KANGAROO_GREY_SCIENTIFIC_NAME = "Macropus giganteus"
WALLABY_SWAMP_SCIENTIFIC_NAME = "Wallabia bicolor"
WALLABY_RED_NECKED_SCIENTIFIC_NAME = "Notamacropus rufogriseus"
WOMBAT_SCIENTIFIC_NAME = "Vombatus ursinus"
KOALA_SCIENTIFIC_NAME = "Phascolarctos cinereus"
POSSUM_BRUSHTAIL_SCIENTIFIC_NAME = "Trichosurus vulpecula"
POSSUM_RINGTAIL_SCIENTIFIC_NAME = "Pseudocheirus peregrinus"
BANDICOOT_BROWN_SCIENTIFIC_NAME = "Isoodon obesulus"
ECHIDNA_SCIENTIFIC_NAME = "Tachyglossus aculeatus"
PLATYPUS_SCIENTIFIC_NAME = "Ornithorhynchus anatinus"
# Base URLs
GBIF_URL = "https://api.gbif.org/v1/occurrence/search"
ALA_URL = "https://biocache-ws.ala.org.au/ws/occurrences/search"

STATE_CODES = {
    "New South Wales": "NSW",
    "Queensland": "QLD",
    "Victoria": "VIC",
    "Tasmania": "TAS",
    "Australian Capital Territory": "ACT",
    "Nortern Territory": "NT",
    "South Australia": "SA",
    "Western Australia": "WA",
}


def main():
    to_parquet("sightings/")


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
            if data["endOfRecords"] or offset > 100:
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
            f"{results[0]['species'].lower().replace(' ', '_')}_sightings_gbif.csv"
        )
        # exporting the collected data to a csv file
        df = pd.DataFrame(results)
        df.to_csv(file_name, index=False)
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
            "fl": "scientificName,month,year,stateProvince,country,decimalLatitude,decimalLongitude",  # fields to return
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
        file_name = f"{results[0]['scientificName'].lower().replace(' ', '_')}_sightings_ala.csv"

        # exporting the collected data to a csv file
        df = pd.DataFrame(results)
        df.to_csv(file_name, index=False)
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
        "decimalLatitude",
        "decimalLongitude",
    ]

    # reading the csv file
    df = pd.read_csv(file_name)

    # for ALA data
    try:
        # renmaing the ala specific column
        df = df.rename(
            columns={
                "scientificName": "species",
            }
        )
    # for GBIF data
    except KeyError:
        pass

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

    # adding the state codes
    df["state"] = df["state"].map(STATE_CODES)

    # removing rows with missing values
    df = df.dropna(subset=["latitude", "longitude", "year", "month", "state"])

    # removing rows with older sighting data
    df = df.drop(df[df["year"] < 2020].index)

    # removing duplicates
    df = df.drop_duplicates(subset=["latitude", "longitude", "year", "month"])

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


def to_parquet(path: str):
    for file_name in os.listdir(path):
        if not file_name.endswith(".csv"):
            continue

        file_name = os.path.join(path, file_name)
        new_file_name = file_name.replace(".csv", ".parquet")

        df = pd.read_csv(file_name)
        df.to_parquet(new_file_name, index=False)

        os.remove(file_name)
        print(f"✅Data exported to {new_file_name} successfully. ")


if __name__ == "__main__":
    main()
