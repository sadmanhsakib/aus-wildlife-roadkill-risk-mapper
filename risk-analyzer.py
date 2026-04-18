from re import S
import time
import osmnx as ox
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd


LATITUDE_COLUMN = "latitude"
LONGITUDE_COLUMN = "longitude"

sightings_df = pd.read_csv("sightings/sightings.csv")

MAIN_STATES = ("New South Wales", "Victoria", "Queensland", 
               "Western Australia", "South Australia", "Tasmania",
               "Australian Capital Territory", "Northern Territory")


def main():
    high_risk, low_risk, states_projected, edges_projected, road_buffer_gdf = prepare_spatial_data(
        sightings_df
    )
    
    visualize_data(high_risk, low_risk, states_projected, edges_projected, road_buffer_gdf)


def prepare_spatial_data(df: pd.DataFrame) -> tuple[gpd.GeoDataFrame]:
    # converting pandas DataFrame to GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,
        # creating the geometry column
        geometry=gpd.points_from_xy(df[LONGITUDE_COLUMN], df[LATITUDE_COLUMN]),
        crs="EPSG:4326",
    )

    # converting to projected CRS
    gdf_projected = gdf.to_crs("EPSG:32754")

    states = gpd.read_file("roads/SA1_2021_AUST_GDA2020.shp")

    # Filter to just the main states
    states = states[states["STE_NAME21"].isin(MAIN_STATES)]
                    
    columns = [
        "SA1_CODE21",
        "CHG_FLAG21",
        "CHG_LBL21",
        "SA2_CODE21",
        "SA2_NAME21",
        "SA3_CODE21",
        "SA3_NAME21",
        "SA4_CODE21",
        "SA4_NAME21",
        "GCC_CODE21",
        "GCC_NAME21",
        "AUS_CODE21",
        "AUS_NAME21",
        "AREASQKM21",
        "LOCI_URI21",
        "STE_CODE21",
    ]
    # removing unnecessary columns
    states = states.drop(columns=columns)
    states_projected = states.to_crs(gdf_projected.crs)
    
    # finding sightings within states
    sightings = gpd.sjoin(
        gdf_projected, states_projected, how="inner", predicate="within"
    )
    
    # dropping unnecessary columns
    sightings = sightings.drop(columns=["index_right", "countryCode"])
    sightings = sightings.rename(columns={"STE_NAME21": "state"})

    high_risk_parts = []
    edges_projected_parts = []
    road_buffer_gdf_parts = []

    # looping through each state for better data handling
    for STATE in MAIN_STATES:
        # isolating the sightings
        state_sightings = sightings[sightings["state"] == STATE]
        state_sightings_projected = state_sightings.to_crs("EPSG:32754")
        
        # pulling driveable roads for the current state
        G = ox.graph_from_place(
            f"{STATE}, Australia", network_type="drive"
        )

        # converting graph to node and edge GeoDataFrames
        # nodes are intersections or endpoints
        # edges are the roads connecting nodes
        state_nodes, state_edges = ox.graph_to_gdfs(G)

        # converting to projected CRS
        state_edges_projected = state_edges.to_crs("EPSG:32754")
        # creating a buffer of 500m around the roads
        state_road_buffer = state_edges_projected.buffer(500).union_all()
        state_road_buffer_gdf = gpd.GeoDataFrame(geometry=[state_road_buffer], crs="EPSG:32754")

        # finding sightings within 500m of a road
        high_risk_state = gpd.sjoin(
            state_sightings_projected,
            state_road_buffer_gdf,
            how="inner",
            predicate="within",
        )
        # storing the data for combining
        high_risk_parts.append(high_risk_state)
        edges_projected_parts.append(state_edges_projected)
        road_buffer_gdf_parts.append(state_road_buffer_gdf)        
        
    # merging the parts for full gdf
    high_risk = pd.concat(high_risk_parts, ignore_index=True)
    edges_projected = pd.concat(edges_projected_parts, ignore_index=True)
    road_buffer_gdf = pd.concat(road_buffer_gdf_parts, ignore_index=True)

    # finding sightings not within 500m of a road
    low_risk = sightings[~sightings.index.isin(high_risk.index)]
    
    return high_risk, low_risk, states_projected, edges_projected, road_buffer_gdf


def visualize_data(high_risk, low_risk, states_projected, edges_projected, road_buffer_gdf):
    fig, ax = plt.subplots(figsize=(12, 10))

    # plotting the whole country
    states_projected.plot(ax=ax, color="green", alpha=0.2)
    
    # plotting the edges and roads
    edges_projected.plot(ax=ax, color="black", linewidth=0.5, alpha=0.5)
    road_buffer_gdf.plot(ax=ax, color="grey", alpha=0.2)

    # plotting the sightings
    high_risk.plot(ax=ax, color="red", markersize=8, alpha=0.9, label="High risk")
    low_risk.plot(ax=ax, color="blue", markersize=6, alpha=0.9, label="Low risk")

    # labeling the map
    ax.set_title("Sightings across Australia", fontsize=14)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
