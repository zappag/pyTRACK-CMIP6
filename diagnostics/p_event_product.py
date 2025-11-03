import re
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# === FILE SETUP ===
directory = "/home/ghinassi/work/track_plots/risk_ratio_probabilities/"
index_file = "index_threshold_comparison_output.txt"
precip_file = "precipitation_extreme_probabilities.txt"

# Output directory
plotting_dir = "/home/ghinassi/work/track_plots/precipitation_extremes/"
os.makedirs(plotting_dir, exist_ok=True)


def parse_index_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()
        
    ERA5_match = re.search(r"ERA5: P\(pattern\) = ([\d.]+), P\(storm \| pattern\) = ([\d.]+)", content)
    era5_prob = {"P_pattern": float(ERA5_match.group(1)), "P_storm_given_pattern": float(ERA5_match.group(2))}
    hist_pattern = re.findall(r"HIST\s+(r\d+i1p1f1): P\(pattern\) = ([\d.]+), P\(storm \| pattern\) = ([\d.]+)", content)
    ssp_pattern = re.findall(r"SSP245\s+(r\d+i1p1f1): P\(pattern\) = ([\d.]+), P\(storm \| pattern\) = ([\d.]+)", content)

    hist_data = {m: {"P_pattern": float(p), "P_storm_given_pattern": float(s)} for m, p, s in hist_pattern}
    ssp_data = {m: {"P_pattern": float(p), "P_storm_given_pattern": float(s)} for m, p, s in ssp_pattern}

    # Get ensemble means
    hist_mean_match = re.search(r"Hist ens mean: P\(pattern\) = ([\d.]+), P\(storm \| pattern\) = ([\d.]+)", content)
    ssp_mean_match = re.search(r"SSP245 ens mean: P\(pattern\) = ([\d.]+), P\(storm \| pattern\) = ([\d.]+)", content)

    hist_mean = {"P_pattern": float(hist_mean_match.group(1)), "P_storm_given_pattern": float(hist_mean_match.group(2))}
    ssp_mean = {"P_pattern": float(ssp_mean_match.group(1)), "P_storm_given_pattern": float(ssp_mean_match.group(2))}

    return era5_prob, hist_data, ssp_data, hist_mean, ssp_mean


def parse_precip_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()
        
    ERA5_pattern = re.search(r"ERA5: P\(extreme\) = ([\d.]+), P\(extreme \| storm, large scale\) = ([\d.]+)", content)
    era5_extreme_prob = {"P_extreme": float(ERA5_pattern.group(1)), "P_extreme_given_storm_largescale": float(ERA5_pattern.group(2))}

    hist_pattern = re.findall(r"HIST\s+(r\d+i1p1f1): P\(extreme\) = ([\d.]+), P\(extreme \| storm, large scale\) = ([\d.]+)", content)
    ssp_pattern = re.findall(r"SSP245\s+(r\d+i1p1f1): P\(extreme\) = ([\d.]+), P\(extreme \| storm, large scale\) = ([\d.]+)", content)
    
    hist_data = {m: {"P_extreme": float(p), "P_extreme_given_storm_largescale": float(s)} for m, p, s in hist_pattern}
    ssp_data = {m: {"P_extreme": float(p), "P_extreme_given_storm_largescale": float(s)} for m, p, s in ssp_pattern}

    # Get ensemble means
    hist_mean_match = re.search(r"Hist ens mean: P\(extreme\) = ([\d.]+), P\(extreme \| storm, large scale\) = ([\d.]+)", content)
    ssp_mean_match = re.search(r"SSP245 ens mean: P\(extreme\) = ([\d.]+), P\(extreme \| storm, large scale\) = ([\d.]+)", content)
    
    hist_mean = {"P_extreme": float(hist_mean_match.group(1)), "P_extreme_given_storm_largescale": float(hist_mean_match.group(2))}
    ssp_mean = {"P_extreme": float(ssp_mean_match.group(1)), "P_extreme_given_storm_largescale": float(ssp_mean_match.group(2))}
    
    # Ensure only common members are kept
    common = hist_data.keys() & ssp_data.keys()
    hist_data = {k: hist_data[k] for k in common}
    ssp_data = {k: ssp_data[k] for k in common}
    return era5_extreme_prob, hist_data, ssp_data, hist_mean, ssp_mean


# === COMPUTATION OF P(Event) ===
def compute_event_probs(index_data, precip_data):
    common = set(index_data.keys()) & set(precip_data.keys())
    return {
        m: index_data[m]["P_pattern"]
           * index_data[m]["P_storm_given_pattern"]
           * precip_data[m]
        for m in common
    }


# === bar plot for P(event) computed as product ===
def plot_event_probabilities(era5_prob,hist_p_events, ssp_p_events, output_path, seas="SON"):
    plt.figure(figsize=(10, 6))
    
    # Ensure order of bars is with increasing ens member e.g. r1i1p1f1, r2i1p1f1, ...
    hist_keys = sorted(hist_p_events.keys(), key=lambda x: int(re.search(r"r(\d+)", x).group(1)))
    ssp_keys = sorted(ssp_p_events.keys(), key=lambda x: int(re.search(r"r(\d+)", x).group(1)))

    hist_vals = [hist_p_events[k] for k in hist_keys]
    ssp_vals = [ssp_p_events[k] for k in ssp_keys]

    hist_mean = np.mean(hist_vals)
    ssp_mean = np.mean(ssp_vals)

    x_labels = list(["ERA5"] + hist_keys) + ["Hist ens mean"] + list(ssp_keys) + ["SSP245 ens mean"]
    values = [era5_prob] + hist_vals + [None] + ssp_vals + [None]

    colors = (
        ["black"]
        + ["limegreen"] * len(hist_vals)
        + ["white"]  # placeholder for mean box
        + ["lightsalmon"] * len(ssp_vals)
        + ["white"]
    )

    # Plot individual bars
    for i, (val, color) in enumerate(zip(values, colors)):
        if val is not None:
            plt.bar(i, val, color=color)

    # Add boxplot for ensemble values
    hist_box_idx = len(hist_vals) +1
    ssp_box_idx = len(hist_vals) + 1 + len(ssp_vals) +1
    
    meanprops = dict(color="black", linestyle="-", linewidth=2.5)
    plt.boxplot(
        [hist_vals, ssp_vals],
        positions=[hist_box_idx, ssp_box_idx],
        widths=0.6,
        patch_artist=True,
        boxprops=dict(facecolor="orange", alpha=0.7),
        showfliers=False,
        showmeans=True,
        meanline=True,
        meanprops=meanprops,
        medianprops=dict(color="none"),
    )

    plt.xticks(range(len(x_labels)), x_labels, rotation=45, ha="right")
    plt.ylabel("P(Event)")
    plt.title(f"P(Event) = P(L) × P(S|L) × P(X|S,L) - {seas}")
    plt.grid(True, axis="y", linestyle="--", alpha=0.4)

    legend_elements = [
        mpatches.Patch(facecolor="limegreen", label="Hist members"),
        mpatches.Patch(facecolor="lightsalmon", label="SSP245 members"),
        mpatches.Patch(facecolor="lightgray", label="Ensemble mean (box)"),
    ]
    plt.legend(handles=legend_elements, loc="upper right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Plot saved to {output_path}")


# === MAIN ===
if __name__ == "__main__":
    # Parse input probability files
    era5_prob, precip_hist, precip_ssp, precip_hist_mean, precip_ssp_mean = parse_precip_file(os.path.join(directory, precip_file))
    era5_index_prob, index_hist, index_ssp, index_hist_mean, index_ssp_mean = parse_index_file(os.path.join(directory, index_file))
    
    # print all values for debugging
    print("HIST P(L), P(S|L):")
    for m in index_hist:
        print(f"{m}: P(L)={index_hist[m]['P_pattern']}, P(S|L)={index_hist[m]['P_storm_given_pattern']}")
    print("SSP245 P(L), P(S|L):")
    for m in index_ssp:
        print(f"{m}: P(L)={index_ssp[m]['P_pattern']}, P(S|L)={index_ssp[m]['P_storm_given_pattern']}")
    print("HIST P(X|S,L):")
    for m in precip_hist:
        print(f"{m}: P(X|S,L)={precip_hist[m]['P_extreme_given_storm_largescale']}")
    print("SSP245 P(X|S,L):")
    for m in precip_ssp:
        print(f"{m}: P(X|S,L)={precip_ssp[m]['P_extreme_given_storm_largescale']}")

    # Compute P(event) = P(L) * P(S|L) * P(X|S,L)
    era5_p_event = (
        era5_index_prob["P_pattern"]
        * era5_index_prob["P_storm_given_pattern"]
        * era5_prob["P_extreme_given_storm_largescale"]
    )
    print(f"ERA5 P(Event)={era5_p_event}")  
    hist_p_events = compute_event_probs(index_hist, {m: precip_hist[m]["P_extreme_given_storm_largescale"] for m in precip_hist})
    ssp_p_events = compute_event_probs(index_ssp, {m: precip_ssp[m]["P_extreme_given_storm_largescale"] for m in precip_ssp})   
    print("HIST P(Event):")
    for m in hist_p_events:
        print(f"{m}: P(Event)={hist_p_events[m]}")
    print("SSP245 P(Event):")
    for m in ssp_p_events:
        print(f"{m}: P(Event)={ssp_p_events[m]}")   

    # Plot results
    output_path = os.path.join(plotting_dir, "event_probability_product.png")
    plot_event_probabilities(era5_p_event,hist_p_events, ssp_p_events, output_path, seas="SON")

    save_txt = True
    savetext_dir="/home/ghinassi/work/track_plots/risk_ratio_probabilities/"
    if save_txt:
        save_txt_path = os.path.join(savetext_dir, "event_probability_product.txt")
        
        """
        # now save also the computed probabilities to a text file
        # with the following structure:
        P(event) probabilities (computed multplying the three terms):
        ERA5: P(event) = 0.3636
        Historical:
        HIST r2i1p1f1: P(event) = value
        HIST r7i1p1f1: P(event) = value
        ...
        Hist ens mean: P(event) = value
        SSP245:
        SSP245 r2i1p1f1: P(event) = value
        ....
        SSP245 ens mean: P(event) = value
        """
        with open(save_txt_path, "w") as f:
            f.write("# P(event) probabilities (computed multplying the three terms):\n")
            f.write(f"ERA5: P(event) = {era5_p_event:.4f}\n")
            f.write("Historical:\n")
            for m in sorted(hist_p_events.keys(), key=lambda x: int(re.search(r"r(\d+)", x).group(1))):
                f.write(f"HIST {m}: P(event) = {hist_p_events[m]:.4f}\n")
            hist_ens_mean = np.mean(list(hist_p_events.values()))
            f.write(f"Hist ens mean: P(event) = {hist_ens_mean:.4f}\n")
            f.write("SSP245:\n")
            for m in sorted(ssp_p_events.keys(), key=lambda x: int(re.search(r"r(\d+)", x).group(1))):
                f.write(f"SSP245 {m}: P(event) = {ssp_p_events[m]:.4f}\n")
            ssp_ens_mean = np.mean(list(ssp_p_events.values()))
            f.write(f"SSP245 ens mean: P(event) = {ssp_ens_mean:.4f}\n")
        print(f"Computed probabilities saved to {save_txt_path}")


