import os
import xarray as xr
import geopandas as gpd
import pandas as pd
import numpy as np 
from datetime import datetime
import matplotlib.pyplot as plt


def create_gdf_from_df(df, lat_name, lon_name):
    """
    Converts a DataFrame with latitude and longitude into a GeoDataFrame.

    Parameters:
        df (DataFrame): The input DataFrame containing data with latitude and longitude.
        lat_name (str): The name of the latitude column.
        lon_name (str): The name of the longitude column.

    Returns:
        GeoDataFrame: A GeoDataFrame with a geometry column created from latitude and longitude.
    """
    lats = df.index.get_level_values(lat_name)
    lons = df.index.get_level_values(lon_name)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(lons, lats), crs="EPSG:4326")
    gdf.reset_index(inplace=True)
    return gdf

def process_data4(precip_nc, pr_name, lat_name, lon_name, sy, ly, shape_gdf, saveout=False):
    """
    Processes precipitation data for a specific time range and spatial region.

    Parameters:
        precip_nc (str): Path to the NetCDF file containing precipitation data.
        pr_name (str): Name of the precipitation variable in the dataset.
        lat_name (str): Name of the latitude variable in the dataset.
        lon_name (str): Name of the longitude variable in the dataset.
        sy (str): Start year for the analysis (e.g., '2010-01-01').
        ly (str): End year for the analysis (e.g., '2020-12-31').
        shape_gdf (GeoDataFrame): GeoDataFrame containing the shapefile geometry for spatial filtering.
        saveout (bool): Whether to save intermediate results (default is False).

    Returns:
        DataFrame: A DataFrame with time as rows, geometry as columns, and precipitation values as data.
    """
    # Ensure that shape_gdf has a unique index
    shape_gdf = shape_gdf.reset_index()

    # Open the NetCDF dataset and select the time range
    ds = xr.open_dataset(precip_nc).sel(time=slice(sy, ly))

    # Cut the dataset spatially over Italy
    if ds[lat_name].isel(lat=0) < ds[lat_name].isel(lat=-1):
        ds = ds.sel(lon=slice(6, 19.5)).sel(lat=slice(35, 50))
    else:
        ds = ds.sel(lon=slice(6, 19.5)).sel(lat=slice(50, 35))
  
    # Convert the dataset to a DataFrame
    df = ds[pr_name].to_dataframe()
    gdf = create_gdf_from_df(df, lat_name, lon_name)

    # Perform a spatial join to filter points within the shapefile geometry
    gdf = gpd.sjoin(gdf, shape_gdf, predicate='within')

    # Pivot the data to structure it with time as rows, geometry as columns, and precipitation as values
    results_df = gdf.pivot(index='time', columns='geometry', values=pr_name)

    return results_df

def calculate_grid_area(ds, lat_name='lat', lon_name='lon'):
    """
    Calculates the area (in km²) of each grid cell in a dataset using latitude and longitude.

    Parameters:
        ds (xarray.Dataset): The dataset containing latitude and longitude.
        lat_name (str): Name of the latitude variable.
        lon_name (str): Name of the longitude variable.

    Returns:
        xarray.DataArray: A DataArray with the same shape as the grid, containing the area in km².
    """
    # Earth's radius in kilometers
    R = 6371.0

    # Convert latitude and longitude to radians
    lat = np.deg2rad(ds[lat_name].values)
    lon = np.deg2rad(ds[lon_name].values)

    # Calculate the edges of the latitude and longitude grid
    lat_edges = np.concatenate(([lat[0] - (lat[1] - lat[0]) / 2], 
                                (lat[0:-1] + lat[1:]) / 2, 
                                [lat[-1] + (lat[-1] - lat[-2]) / 2]))
    lon_edges = np.concatenate(([lon[0] - (lon[1] - lon[0]) / 2], 
                                (lon[0:-1] + lon[1:]) / 2, 
                                [lon[-1] + (lon[-1] - lon[-2]) / 2]))

    # Calculate the differences between adjacent edges
    dlat = np.abs(np.diff(lat_edges))
    dlon = np.abs(np.diff(lon_edges))

    # Create 2D grids for dlat and dlon
    dlat_2d, dlon_2d = np.meshgrid(dlat, dlon, indexing="ij")

    # Create a 2D grid for latitude
    lat_2d, _ = np.meshgrid(lat, lon, indexing="ij")

    # Calculate the area of each grid cell
    area = (R**2) * dlat_2d * dlon_2d * np.cos(lat_2d)

    # Return as an xarray.DataArray
    area = xr.DataArray(area, dims=[lat_name, lon_name], coords={lat_name: ds[lat_name], lon_name: ds[lon_name]})

    return area

def process_precip(precip_nc_files, pr_name, lat_name, lon_name, shapefile, qthreshold, sy, ly, sy_clim, ly_clim, scalef, save_mean=False):
    """
    Processes precipitation data for multiple NetCDF files and computes statistics for warning regions.

    Parameters:
        precip_nc_files (list): List of paths to NetCDF files containing precipitation data.
        pr_name (str): Name of the precipitation variable in the dataset.
        lat_name (str): Name of the latitude variable in the dataset.
        lon_name (str): Name of the longitude variable in the dataset.
        shapefile (str): Path to the shapefile for spatial filtering.
        qthreshold (float): Quantile threshold for identifying intense precipitation events.
        sy (str): Start year for the analysis (e.g., '2010-01-01').
        ly (str): End year for the analysis (e.g., '2020-12-31').
        sy_clim (datetime): Start date for the climatological reference period.
        ly_clim (datetime): End date for the climatological reference period.
        scalef (float): Scaling factor for precipitation values (e.g., to convert units).
        save_mean (bool): Whether to save intermediate results (default is False).

    Returns:
        DataFrame: A DataFrame containing precipitation statistics for the warning regions.
    """
    # Read the shapefile and dissolve to keep only the external border
    shape_gdf = gpd.read_file(shapefile)
    shape_gdf = shape_gdf.dissolve()
    shape_gdf = shape_gdf[['geometry']]

    # Create a DataFrame to store results
    precip_wr = pd.DataFrame()

    # Loop over all NetCDF files and extract precipitation within the shapefile
    for pr_file_path in precip_nc_files:
        print(f"Processing {pr_file_path}")
        tmp = process_data4(pr_file_path, pr_name, lat_name, lon_name, sy, ly, shape_gdf, save_mean)    
        precip_wr = pd.concat([precip_wr, tmp], ignore_index=False)

    # Compute the area of each grid point in the original dataset
    ds = xr.open_dataset(pr_file_path)
    area = calculate_grid_area(ds, lat_name, lon_name)

    # Extract points of dataset within the shapefile
    points = precip_wr.columns

    # Initialize an empty DataFrame to store the area values
    area_df = pd.DataFrame(columns=['area'])

    # Loop through the points within the shapefile and create a DataFrame with the area values
    for point in points:
        lon = point.x
        lat = point.y
        areapoint = area.sel(lon=lon, lat=lat, method='nearest')
        temp_df = pd.DataFrame({'area': [areapoint.values]}, index=[point])
        area_df = pd.concat([area_df, temp_df])

    # Scale and round precipitation values
    precip_wr = precip_wr * scalef
    precip_wr = precip_wr.round(3)

    # Select time period to compute climatological statistics
    precip_wr_c = precip_wr[(precip_wr.index >= sy_clim) & (precip_wr.index <= ly_clim)]

    # Exclude drizzle/no rain days (1mm/day threshold)
    precip_wr_cr = precip_wr_c[precip_wr_c > 1]

    # Compute threshold for intense events and index with information
    precip_threshold_row = pd.DataFrame(precip_wr_cr.quantile(qthreshold)).T
    precip_threshold_row.index = [f'99p rainy days;{sy_clim.year}-{ly_clim.year}']
    precip_wrt = pd.concat([precip_wr, precip_threshold_row], ignore_index=False)

    # Identify intense rainfall days
    a = precip_wrt.values > precip_threshold_row.values
    a2 = np.any(a, axis=1)  # At least one region/grid point
    a3 = np.sum(a, axis=1)  # Number of regions/grid points
    precip_wrt['intense rain day'] = a2
    precip_wrt['#regions'] = a3

    # Initialize a new column to store the sum of 'area_kmq' for each row where 'a' is true
    precip_wrt['sum_area_kmq'] = 0.0
    sum_area_kmq_idx = precip_wrt.columns.get_loc('sum_area_kmq')

    # Loop over the rows of 'a' and sum 'area_kmq' for each row where 'a' is true
    for i in range(a.shape[0]):
        sum_area = area_df.iloc[a[i, :]]['area'].values.sum()
        precip_wrt.iloc[i, sum_area_kmq_idx] = sum_area

    # Identify intense rainfall days with specific area thresholds
    precip_wrt['area 5000km2'] = precip_wrt['sum_area_kmq'] > 5000.0
    precip_wrt['area 10000km2'] = precip_wrt['sum_area_kmq'] > 10000.0
    precip_wrt['area 25000km2'] = precip_wrt['sum_area_kmq'] > 25000.0
    precip_wrt['area 50000km2'] = precip_wrt['sum_area_kmq'] > 50000.0

    return precip_wrt



