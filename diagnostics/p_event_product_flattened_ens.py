import re
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# === FILE SETUP ===
directory_index = "/home/ghinassi/work/track_plots/summary_index_probability/"
directory_precip = "/home/ghinassi/work/track_plots/precipitation_extremes_flattened/"
index_file = "index_threshold_comparison_output_flattened_ens.txt"
precip_file = "precipitation_extreme_probabilities_flattened.txt"

# Output directory
plotting_dir = "/home/ghinassi/work/track_plots/precipitation_extremes_flattened/"
os.makedirs(plotting_dir, exist_ok=True)


def read_index_file(filepath):
    """
    Parse index_threshold_comparison_output_flattened_ens.txt

    Expected block:
    === Large-scale Pattern and Storm Probabilities ===
    ERA5: P(pattern) = 0.0354, P(storm | pattern) = 0.1100
    Historical (flattened): P(pattern) = 0.0184, P(storm | pattern) = 0.1458
    SSP245 (flattened): P(pattern) = 0.0126, P(storm | pattern) = 0.1544
    """
    with open(filepath, "r") as f:
        content = f.read()

    pattern = re.compile(
        r"(\bERA5\b|Historical.*?|SSP245.*?)\s*:\s*P\(pattern\)\s*=\s*([\d.]+),\s*P\(storm\s*\|\s*pattern\)\s*=\s*([\d.]+)"
    )

    data = {}
    for match in pattern.finditer(content):
        label = match.group(1)
        p_pattern = float(match.group(2))
        p_storm_given_pattern = float(match.group(3))

        if label.startswith("ERA5"):
            data["ERA5"] = {"P_pattern": p_pattern, "P_storm_given_pattern": p_storm_given_pattern}
        elif label.startswith("Historical"):
            data["Historical"] = {"P_pattern": p_pattern, "P_storm_given_pattern": p_storm_given_pattern}
        elif label.startswith("SSP245"):
            data["SSP245"] = {"P_pattern": p_pattern, "P_storm_given_pattern": p_storm_given_pattern}

    return data

def read_precip_file(filepath):
    """
    Parse precipitation_extreme_probabilities_flattened_ens.txt

    Expected block:
    Flattened Precipitation Probabilities:
    ERA5: P(extreme) = 0.0085, P(extreme | storm, large scale) = 0.3636, P(event) = 0.0014
    Historical (flattened): P(extreme) = 0.0092, P(extreme | storm, large scale) = 0.1707, P(event) = 0.0025
    SSP245 (flattened): P(extreme) = 0.0143, P(extreme | storm, large scale) = 0.5455, P(event) = 0.0043
    """
    with open(filepath, "r") as f:
        content = f.read()

    pattern = re.compile(
        r"(\bERA5\b|Historical.*?|SSP245.*?)\s*:\s*P\(extreme\)\s*=\s*([\d.]+),\s*P\(extreme\s*\|\s*storm, large scale\)\s*=\s*([\d.]+)"
    )

    data = {}
    for match in pattern.finditer(content):
        label = match.group(1)
        p_extreme = float(match.group(2))
        p_extreme_given = float(match.group(3))

        if label.startswith("ERA5"):
            data["ERA5"] = {"P_extreme": p_extreme, "P_extreme_given_storm_largescale": p_extreme_given}
        elif label.startswith("Historical"):
            data["Historical"] = {"P_extreme": p_extreme, "P_extreme_given_storm_largescale": p_extreme_given}
        elif label.startswith("SSP245"):
            data["SSP245"] = {"P_extreme": p_extreme, "P_extreme_given_storm_largescale": p_extreme_given}

    return data

# === COMPUTATION OF P(Event) ===
def compute_event_probs(index_data, precip_data):
    common = set(index_data.keys()) & set(precip_data.keys())
    return {
        m: index_data[m]["P_pattern"]
           * index_data[m]["P_storm_given_pattern"]
           * precip_data[m]
        for m in common
    }


# === bar plot for P(event) computed as product (ensemble means only) ===
def plot_event_probabilities(era5_p_event, hist_mean, ssp_mean, output_path, seas="SON"):
    """
    Plot only three bars: ERA5, Historical ensemble mean, SSP245 ensemble mean.
    """
    plt.figure(figsize=(7, 5))
    labels = ["ERA5", "Historical (mean)", "SSP245 (mean)"]
    values = [era5_p_event, hist_mean, ssp_mean]
    colors = ["black", "green", "orange"]

    plt.bar(labels, values, color=colors, alpha=0.8)
    plt.ylabel("P(Event)")
    plt.title(f"P(Event) = P(L) × P(S|L) × P(X|S,L) - {seas}")
    plt.grid(True, axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Plot saved to {output_path}")


# === MAIN ===
if __name__ == "__main__":
    # Parse input probability files
    precip_data = read_precip_file(os.path.join(directory_precip, precip_file))
    index_data = read_index_file(os.path.join(directory_index, index_file))

    # Extract datasets
    era5_prob = precip_data["ERA5"]
    era5_index_prob = index_data["ERA5"]
    hist_prob = precip_data["Historical"]
    ssp_prob = precip_data["SSP245"]
    hist_index = index_data["Historical"]
    ssp_index = index_data["SSP245"]

    # Compute P(event) = P(L) × P(S|L) × P(X|S,L)
    era5_p_event = (
        era5_index_prob["P_pattern"]
        * era5_index_prob["P_storm_given_pattern"]
        * era5_prob["P_extreme_given_storm_largescale"]
    )
    hist_p_event = (
        hist_index["P_pattern"]
        * hist_index["P_storm_given_pattern"]
        * hist_prob["P_extreme_given_storm_largescale"]
    )
    ssp_p_event = (
        ssp_index["P_pattern"]
        * ssp_index["P_storm_given_pattern"]
        * ssp_prob["P_extreme_given_storm_largescale"]
    )

    print("\n=== Flattened Ensemble P(Event) Computation ===")
    print(f"ERA5: P(event) = {era5_p_event:.4f}")
    print(f"Historical (ens mean): P(event) = {hist_p_event:.4f}")
    print(f"SSP245 (ens mean): P(event) = {ssp_p_event:.4f}")

    # Plot histogram
    output_path = os.path.join(plotting_dir, "p_event_product_flattened_ens.png")
    plot_event_probabilities(era5_p_event, hist_p_event, ssp_p_event, output_path, seas="SON")

    # Save results to text file
    savetext_dir = "/home/ghinassi/work/track_plots/risk_ratio_probabilities/"
    os.makedirs(savetext_dir, exist_ok=True)
    save_txt_path = os.path.join(savetext_dir, "event_probability_threebars.txt")

    with open(save_txt_path, "w") as f:
        f.write("# P(event) probabilities (computed multiplying the three ensemble-mean terms)\n")
        f.write(f"ERA5: P(event) = {era5_p_event:.4f}\n")
        f.write(f"Historical (mean): P(event) = {hist_p_event:.4f}\n")
        f.write(f"SSP245 (mean): P(event) = {ssp_p_event:.4f}\n")

    print(f"Computed probabilities saved to {save_txt_path}")

