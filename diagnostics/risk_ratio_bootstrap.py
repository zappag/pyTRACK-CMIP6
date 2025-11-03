import re
import matplotlib.pyplot as plt
import numpy as np
import os

# === FILE SETUP ===
directory = "/home/ghinassi/work/track_plots/risk_ratio_probabilities/"
index_file = "index_threshold_comparison_output.txt"
precip_file = "precipitation_extreme_probabilities_only_stormgivenlargescale.txt"

index_file_flattend = "/home/ghinassi/work/track_plots/summary_index_probability/index_threshold_comparison_output_flattened_ens.txt"
precip_file_flattened = "/home/ghinassi/work/track_plots/precipitation_extremes_flattened/precipitation_extreme_probabilities_flattened.txt"

# plotting dir
plotting_dir = "/home/ghinassi/work/track_plots/risk_ratio_probabilities/"
if not os.path.exists(plotting_dir):
    os.makedirs(plotting_dir, exist_ok=True)


# === PARSING FUNCTIONS ===

def parse_index_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    hist_pattern = re.findall(r"HIST\s+(r\d+i1p1f1): P\(pattern\) = ([\d.]+), P\(storm \| pattern\) = ([\d.]+)", content)
    ssp_pattern = re.findall(r"SSP245\s+(r\d+i1p1f1): P\(pattern\) = ([\d.]+), P\(storm \| pattern\) = ([\d.]+)", content)

    hist_data = {m: {"P_pattern": float(p), "P_storm_given_pattern": float(s)} for m, p, s in hist_pattern}
    ssp_data = {m: {"P_pattern": float(p), "P_storm_given_pattern": float(s)} for m, p, s in ssp_pattern}

    # Get ensemble means
    hist_mean_match = re.search(r"Hist ens mean: P\(pattern\) = ([\d.]+), P\(storm \| pattern\) = ([\d.]+)", content)
    ssp_mean_match = re.search(r"SSP245 ens mean: P\(pattern\) = ([\d.]+), P\(storm \| pattern\) = ([\d.]+)", content)

    hist_mean = {"P_pattern": float(hist_mean_match.group(1)), "P_storm_given_pattern": float(hist_mean_match.group(2))}
    ssp_mean = {"P_pattern": float(ssp_mean_match.group(1)), "P_storm_given_pattern": float(ssp_mean_match.group(2))}

    return hist_data, ssp_data, hist_mean, ssp_mean

def parse_precip_file_event(filepath):
    
    with open(filepath, "r") as f:
        content = f.read()
    # Extract P(extreme | storm, large scale) probabilities
    hist_pattern = re.findall(r"HIST\s+(r\d+i1p1f1): P\(extreme \| storm, large scale\) = ([\d.]+)", content)
    ssp_pattern = re.findall(r"SSP245\s+(r\d+i1p1f1): P\(extreme \| storm, large scale\) = ([\d.]+)", content)
    
    hist_data = {m: {"P_extreme_given_storm_largescale": float(s)} for m, s in hist_pattern}
    ssp_data = {m: {"P_extreme_given_storm_largescale": float(s)} for m, s in ssp_pattern}

    # Get ensemble means
    hist_mean_match = re.search(r"Hist ens mean: P\(extreme \| storm, large scale\) = ([\d.]+)", content)
    ssp_mean_match = re.search(r"SSP245 ens mean: P\(extreme \| storm, large scale\) = ([\d.]+)", content)
    
    hist_mean = {"P_extreme_given_storm_largescale": float(hist_mean_match.group(1))}
    ssp_mean = {"P_extreme_given_storm_largescale": float(ssp_mean_match.group(1))}
    
    # Ensure only common members are kept
    common = hist_data.keys() & ssp_data.keys()
    hist_data = {k: hist_data[k] for k in common}
    ssp_data = {k: ssp_data[k] for k in common}
    
    return hist_data, ssp_data, hist_mean, ssp_mean

def parse_p_event(filepath):
    with open(filepath, "r") as f:
        content = f.read()
    # Extract P(event) probabilities
    hist_pattern = re.findall(r"HIST\s+(r\d+i1p1f1): P\(event\) = ([\d.]+)", content)
    ssp_pattern = re.findall(r"SSP245\s+(r\d+i1p1f1): P\(event\) = ([\d.]+)", content)
    hist_data = {m: {"P_event": float(p)} for m, p in hist_pattern}
    ssp_data = {m: {"P_event": float(p)} for m, p in ssp_pattern}
    # Get ensemble means
    hist_mean_match = re.search(r"Hist ens mean: P\(event\) = ([\d.]+)", content)
    ssp_mean_match = re.search(r"SSP245 ens mean: P\(event\) = ([\d.]+)", content)
    hist_mean = {"P_event": float(hist_mean_match.group(1))}
    ssp_mean = {"P_event": float(ssp_mean_match.group(1))}
    # Ensure only common members are kept
    common = hist_data.keys() & ssp_data.keys()
    hist_data = {k: hist_data[k] for k in common}
    ssp_data = {k: ssp_data[k] for k in common}
    return hist_data, ssp_data, hist_mean, ssp_mean

def parse_precip_file_only_precipitation(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    hist_pattern = re.findall(r"HIST\s+(r\d+i1p1f1): P\(extreme\) = ([\d.]+)", content)
    ssp_pattern = re.findall(r"SSP245\s+(r\d+i1p1f1): P\(extreme\) = ([\d.]+)", content)

    hist_data = {m: {"P_extreme": float(p)} for m, p in hist_pattern}
    ssp_data = {m: {"P_extreme": float(p)} for m, p in ssp_pattern} 
    # Get ensemble means
    hist_mean_match = re.search(r"Hist ens mean: P\(extreme\) = ([\d.]+)", content)
    ssp_mean_match = re.search(r"SSP245 ens mean: P\(extreme\) = ([\d.]+)", content)
    hist_mean = {"P_extreme": float(hist_mean_match.group(1))}
    ssp_mean = {"P_extreme": float(ssp_mean_match.group(1))}
    # Ensure only common members are kept
    common = hist_data.keys() & ssp_data.keys()
    hist_data = {k: hist_data[k] for k in common}
    ssp_data = {k: ssp_data[k] for k in common}
    return hist_data, ssp_data, hist_mean, ssp_mean

def read_index_file_flattened(filepath):
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

def read_precip_file_flattened(filepath):
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

def bootstrap_mean_std(values_hist, values_ssp, n_bootstrap=100):
    """Return bootstrap mean, std, and percentile CI (2.5–97.5%) of the ratio (ssp_mean / hist_mean)."""
    values_hist = np.array(values_hist)
    values_ssp = np.array(values_ssp)
    n_hist = len(values_hist)
    n_ssp = len(values_ssp)
    ratios = []
    
    for _ in range(n_bootstrap):
        sample_hist = np.random.choice(values_hist, n_hist, replace=True)
        sample_ssp = np.random.choice(values_ssp, n_ssp, replace=True)
        mean_hist = np.mean(sample_hist)
        mean_ssp = np.mean(sample_ssp)
        if mean_hist != 0:
            ratios.append(mean_ssp / mean_hist)
        elif mean_hist == 0:
            raise ValueError("Mean of historical values is zero, cannot compute ratio.")

    ratios = np.array(ratios)
    ratio_mean = np.mean(ratios)
    ratio_std = np.std(ratios)
    ci_lower = np.percentile(ratios, 2.5)
    ci_upper = np.percentile(ratios, 97.5)
    return ratio_mean, ratio_std, (ci_lower, ci_upper)


# === PLOTTING FUNCTION ===

def plot_ratios(index_hist, index_ssp, keys_index, keys_precip, keys_p_event, plotting_dir,
                flattened_index_data=None, flattened_precip_data=None):
    index_means, index_stds, index_means_bootstrap, index_cis = [], [], [], []
    
    for k in keys_index:
        hist_mean = index_hist_mean[k]
        ssp_mean = index_ssp_mean[k]
        index_means.append(ssp_mean / hist_mean)
        hist_values = [v[k] for v in index_hist.values() if k in v]
        ssp_values = [v[k] for v in index_ssp.values() if k in v]
        mean_bootstrap, std, ci = bootstrap_mean_std(hist_values, ssp_values)
        index_means_bootstrap.append(mean_bootstrap)
        index_stds.append(std)
        index_cis.append(ci)
        
    precip_means, precip_stds, precip_means_bootstrap, precip_cis = [], [], [], []
    
    for k in keys_precip:
        hist_mean = precip_hist_mean[k]
        ssp_mean = precip_ssp_mean[k]
        precip_means.append(ssp_mean / hist_mean)
        hist_values = [v[k] for v in precip_hist.values() if k in v]
        ssp_values = [v[k] for v in precip_ssp.values() if k in v]
        mean_bootstrap, std, ci = bootstrap_mean_std(hist_values, ssp_values)
        precip_means_bootstrap.append(mean_bootstrap)
        precip_stds.append(std)
        precip_cis.append(ci)
        
    # now extract p_event
    p_event_means, p_event_stds, p_event_means_bootstrap, p_event_cis = [], [], [], []
    for k in keys_p_event:
        hist_mean = hist_p_event_mean[k]
        ssp_mean = ssp_p_event_mean[k]
        p_event_means.append(ssp_mean / hist_mean)
        hist_values = [v[k] for v in hist_p_events.values() if k in v]
        ssp_values = [v[k] for v in ssp_p_events.values() if k in v]
        mean_bootstrap, std, ci = bootstrap_mean_std(hist_values, ssp_values)
        p_event_means_bootstrap.append(mean_bootstrap)
        p_event_stds.append(std)
        p_event_cis.append(ci)
        
    # Combine all data
    means = index_means + precip_means + p_event_means
    stds = index_stds + precip_stds + p_event_stds
    means_bootstrap = index_means_bootstrap + precip_means_bootstrap + p_event_means_bootstrap
    cis = index_cis + precip_cis + p_event_cis

    labels = [
        "P(large scale)",
        "P(storm | large scale)",
        "P(precipitation | storm, large scale)",
        "P(event) = P(L)*P(S|L)*P(X|S,L)"
    ]

    # compute P(event) from product
    p_precip_event_mean = np.prod(means[:-1])
    relative_vars = [(std / mean) ** 2 for mean, std in zip(means[:-1], stds[:-1])]
    p_precip_event_std = p_precip_event_mean * np.sqrt(np.sum(relative_vars))
    p_precip_event_mean_bootstrap = np.prod(means_bootstrap[:-1])

    means.append(p_precip_event_mean)
    stds.append(p_precip_event_std)
    means_bootstrap.append(p_precip_event_mean_bootstrap)
    labels.append("P(event) from product of RR terms")

    x = np.arange(len(means))
    fig, ax = plt.subplots(figsize=(10, 6))

    # --- Regular ensemble mean + CI
    for i in range(len(means) - 1):
        ax.errorbar(
            x[i], means[i], yerr=[[means[i] - cis[i][0]], [cis[i][1] - means[i]]],
            fmt='s', color='red', ecolor='black', capsize=5, label='Ens Mean' if i == 0 else ""
        )
    ax.errorbar(
        x[-1], means[-1], yerr=stds[-1],
        fmt='s', color='blue', ecolor='black', capsize=5, label='P(event) Ens Mean (±1 std)'
    )

    # --- Bootstrap means
    ax.scatter(x, means_bootstrap, color='green', marker='x', s=80, label='Bootstrap Mean')

    # --- Flattened ensemble mean (NEW)
    #if flattened_index_data and flattened_precip_data:
    
    if flattened_index_data is not None and flattened_precip_data is not None:
        print("Adding flattened ensemble mean points to the plot.")
        flat_ratios = []
        flat_ratios.append(flattened_index_data["SSP245"]["P_pattern"] /
                            flattened_index_data["Historical"]["P_pattern"])
        flat_ratios.append(flattened_index_data["SSP245"]["P_storm_given_pattern"] /
                            flattened_index_data["Historical"]["P_storm_given_pattern"])
        flat_ratios.append(flattened_precip_data["SSP245"]["P_extreme_given_storm_largescale"] /
                            flattened_precip_data["Historical"]["P_extreme_given_storm_largescale"])
        flat_ratios.append(flat_ratios[0] * flat_ratios[1] * flat_ratios[2])
        ax.scatter(x[:len(flat_ratios)], flat_ratios, color='purple', marker='o', s=90, label='Flattened ens mean')
        
        # add also value of RR from the product of flattened means
        p_precip_event_flat = flat_ratios[0] * flat_ratios[1] * flat_ratios[2]
        ax.scatter(len(flat_ratios), p_precip_event_flat, color='purple', marker='o', s=90)

    # --- Style
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=6)
    ax.grid(axis='y', linestyle=':', linewidth=0.8) 
    ax.legend(fontsize=9)
    ax.set_ylabel('Risk Ratio (SSP245 / Historical)')
    ax.set_title('Risk Ratios with 95% CI, Bootstrap, and Flattened Means')
    ax.axhline(1, color='gray', linestyle='--')
    plt.tight_layout()
    plt.savefig(os.path.join(plotting_dir, "risk_ratios_bootstrap.png"))
    plt.close()
    print(f"✅ Risk ratio plot saved to {os.path.join(plotting_dir, 'risk_ratios_bootstrap.png')}")


# === MAIN ===

if __name__ == "__main__":
    # Parse regular ensemble results
    index_hist, index_ssp, index_hist_mean, index_ssp_mean = parse_index_file(os.path.join(directory, index_file))
    precip_hist, precip_ssp, precip_hist_mean, precip_ssp_mean = parse_precip_file_event(os.path.join(directory, precip_file))
    hist_p_events, ssp_p_events, hist_p_event_mean, ssp_p_event_mean = parse_p_event(os.path.join(directory, "p_event_product_output.txt"))

    # Parse flattened ensemble means
    flattened_index_data = read_index_file_flattened(index_file_flattend)
    flattened_precip_data = read_precip_file_flattened(precip_file_flattened)
    
    print("Flattened index data:", flattened_index_data)
    print("Flattened precip data:", flattened_precip_data)


    # Keys
    index_keys = ["P_pattern", "P_storm_given_pattern"]
    precip_keys = ["P_extreme_given_storm_largescale"]
    p_event_keys = ["P_event"]

    # Plot including flattened points
    plot_ratios(index_hist, index_ssp, index_keys, precip_keys, p_event_keys,
                plotting_dir, flattened_index_data, flattened_precip_data)

