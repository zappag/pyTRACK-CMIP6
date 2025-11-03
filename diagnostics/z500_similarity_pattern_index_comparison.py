import pickle
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # For datetime parsing

def plot_index_pdfs(era5_vals, hist_vals, ssp245_vals, plot_dir, era5_range, hist_range, ssp245_range):
    plt.figure(figsize=(10, 6))

    all_vals = np.concatenate([era5_vals, hist_vals, ssp245_vals])
    bins = np.linspace(all_vals.min(), all_vals.max(), 21)
    bin_width = bins[1] - bins[0]
    bin_centers = bins[:-1] + bin_width / 2

    era5_hist, _ = np.histogram(era5_vals, bins=bins, density=True)
    hist_hist, _ = np.histogram(hist_vals, bins=bins, density=True)
    ssp245_hist, _ = np.histogram(ssp245_vals, bins=bins, density=True)

    bar_width = bin_width / 4
    offsets = [-bar_width, 0, bar_width]

    # Updated labels with year ranges
    label_era5 = f'ERA5 ({era5_range[0]}–{era5_range[1]})'
    label_hist = f'EC-Earth3 Historical ({hist_range[0]}–{hist_range[1]})'
    label_ssp245 = f'EC-Earth3 SSP245 ({ssp245_range[0]}–{ssp245_range[1]})'

    plt.bar(bin_centers + offsets[0], era5_hist, width=bar_width, label=label_era5, color='black', edgecolor='black')
    plt.bar(bin_centers + offsets[1], hist_hist, width=bar_width, label=label_hist, color='darkgreen', edgecolor='black')
    plt.bar(bin_centers + offsets[2], ssp245_hist, width=bar_width, label=label_ssp245, color='darkorange', edgecolor='black')

    plt.xlabel('Similarity Pattern Index')
    plt.ylabel('Probability Density')
    plt.xlim(-1.7, 1.7)
    plt.title('PDF of Z500 Similarity Index\nERA5 vs EC-Earth3 (Historical & SSP245)')
    plt.legend()

    os.makedirs(plot_dir, exist_ok=True)
    output_file = os.path.join(plot_dir, 'comparison_z500_similarity_index_pdf.png')
    plt.savefig(output_file)
    plt.close()

    print(f"Comparison histogram saved to: {output_file}")

def filter_by_year_ERA5(index_dict, start_year, end_year):
    return [
        v for k, v in index_dict.items()
        if start_year <= pd.to_datetime(k).year <= end_year
        and v is not None and not np.isnan(v)
    ]

def filter_by_year(index_dict, start_year, end_year):
    filtered_values = []
    
    for ens_member, time_dict in index_dict.items():
        for timestamp, value in time_dict.items():
            year = pd.to_datetime(timestamp).year
            if start_year <= year <= end_year and value is not None and not np.isnan(value):
                filtered_values.append(value)

    return filtered_values

def flatten_ensemble_values(index_dict):
    flattened = []
    for ens_member, time_dict in index_dict.items():
        if isinstance(time_dict, dict):
            for value in time_dict.values():
                if value is not None and not np.isnan(value):
                    flattened.append(value)
    return flattened



def main():
    # === Predefined year ranges ===
    ERA5_RANGE = (1984, 2014)
    HIST_RANGE = (1984, 2014)
    SSP245_RANGE = (2070, 2100)

    z500_index_pkl = "/home/ghinassi/work/similarity_pattern_index_pkl"
    z500_index_ERA5_pkl_filename = "index_pattern_ERA5.pkl"
    z500_index_CMIP6_hist_pkl_filename = "index_pattern_EC-Earth3_historical_ens_members.pkl"
    z500_index_CMIP6_scen_filename = "index_pattern_EC-Earth3_scenarioMIP_ssp245_ens_members.pkl"
    plot_dir = "/home/ghinassi/work/track_plots/z500_index"

    era5_path = os.path.join(z500_index_pkl, z500_index_ERA5_pkl_filename)
    hist_path = os.path.join(z500_index_pkl, z500_index_CMIP6_hist_pkl_filename)
    ssp245_path = os.path.join(z500_index_pkl, z500_index_CMIP6_scen_filename)

    with open(era5_path, 'rb') as f:
        era5_index = pickle.load(f)
    with open(hist_path, 'rb') as f:
        hist_index = pickle.load(f)
    with open(ssp245_path, 'rb') as f:
        ssp245_index = pickle.load(f)
        

    era5_vals = filter_by_year_ERA5(era5_index, *ERA5_RANGE)
    hist_vals = filter_by_year(hist_index, *HIST_RANGE)
    ssp245_vals = filter_by_year(ssp245_index, *SSP245_RANGE)


    plot_index_pdfs_bool = True  # Set to True to plot the PDFs

    if plot_index_pdfs_bool:
        plot_index_pdfs(era5_vals, hist_vals, ssp245_vals, plot_dir, ERA5_RANGE, HIST_RANGE, SSP245_RANGE)

if __name__ == "__main__":
    main()
