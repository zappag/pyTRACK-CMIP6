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

tracks_for_weights = "/home/ghinassi/work/track_plots/risk_ratio_probabilities/track_counts_summary.txt"

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

def bootstrap_mean_std(values_hist, values_ssp, weights_hist=None, weights_ssp=None, n_bootstrap=1000):
    """
    Return bootstrap mean, std, and percentile CI (2.5–97.5%) of the ratio (ssp_mean / hist_mean).
    If weights_hist / weights_ssp are provided, they must be numeric arrays (per-member counts).
    Bootstrap is performed at the track level using multinomial resampling so that members with
    more tracks contribute proportionally more to the bootstrap sample.
    """
    values_hist = np.array(values_hist, dtype=float)
    values_ssp = np.array(values_ssp, dtype=float)
    n_hist_members = len(values_hist)
    n_ssp_members = len(values_ssp)

    # Validate shapes if weights are provided
    if weights_hist is not None:
        weights_hist = np.array(weights_hist, dtype=int)
        if len(weights_hist) != n_hist_members:
            raise ValueError("weights_hist length must equal number of historical members in values_hist")
        total_hist_tracks = weights_hist.sum()
        if total_hist_tracks <= 0:
            raise ValueError("Sum of historical weights must be > 0")
    else:
        total_hist_tracks = None

    if weights_ssp is not None:
        weights_ssp = np.array(weights_ssp, dtype=int)
        if len(weights_ssp) != n_ssp_members:
            raise ValueError("weights_ssp length must equal number of SSP members in values_ssp")
        total_ssp_tracks = weights_ssp.sum()
        if total_ssp_tracks <= 0:
            raise ValueError("Sum of SSP weights must be > 0")
    else:
        total_ssp_tracks = None

    ratios = []
    for _ in range(n_bootstrap):
        # Historical mean
        if weights_hist is None:
            # member-level bootstrap (old behavior)
            sample_hist_idx = np.random.choice(n_hist_members, n_hist_members, replace=True)
            mean_hist = np.mean(values_hist[sample_hist_idx])
        else:
            sample_hist_idx = np.random.choice(n_hist_members, n_hist_members, replace=True)
            mean_hist = np.average(values_hist[sample_hist_idx],
            weights=weights_hist[sample_hist_idx])

        # SSP mean
        if weights_ssp is None:
            sample_ssp_idx = np.random.choice(n_ssp_members, n_ssp_members, replace=True)
            mean_ssp = np.mean(values_ssp[sample_ssp_idx])
        else:
            #print("Bootstrapping SSP with weights:", weights_ssp)
            sample_ssp_idx = np.random.choice(n_ssp_members, n_ssp_members, replace=True)
            mean_ssp = np.average(values_ssp[sample_ssp_idx],
            weights=weights_ssp[sample_ssp_idx])


        if mean_hist != 0:
            ratios.append(mean_ssp / mean_hist)
        else:
            # avoid division by zero; append np.nan and filter later
            ratios.append(np.nan)

    ratios = np.array(ratios)

    ratio_mean = np.mean(ratios)
    ratio_std = np.std(ratios, ddof=1)
    ci_lower = np.percentile(ratios, 2.5)
    ci_upper = np.percentile(ratios, 97.5)
    iqr_lower = np.percentile(ratios, 25)
    iqr_upper = np.percentile(ratios, 75)
    return ratio_mean, ratio_std, (ci_lower, ci_upper), (iqr_lower, iqr_upper)

def read_tracks_for_weights(filepath):
    """
    Read track counts from a summary file to compute weights for flattened ensemble means.
    Expected lines:
    ERA5 (1984-2014): total_ts=2821, largescale_timesteps=100, total_tracks=36, large_scale=11, large+precip=3
    Historical r2i1p1f1: total_ts=2821, largescale_timesteps=135, total_tracks=49, large_scale=14, large+precip=3
    ...
    ssp245 r25i1p1f1: total_ts=2821, largescale_timesteps=12, total_tracks=41, large_scale=5, large+precip=3
    ...
    """
    hist_counts = {}
    ssp_counts = {}
    with open(filepath, "r") as f:
        for line in f:
            hist_match = re.match(r"Historical\s+(r\d+i1p1f1):\s*total_ts=(\d+),\s*largescale_timesteps=(\d+),\s*total_tracks=(\d+),\s*large_scale=(\d+),\s*large\+precip=(\d+)", line)
            ssp_match = re.match(r"ssp245\s+(r\d+i1p1f1):\s*total_ts=(\d+),\s*largescale_timesteps=(\d+),\s*total_tracks=(\d+),\s*large_scale=(\d+),\s*large\+precip=(\d+)", line)
            if hist_match:
                member = hist_match.group(1)
                total_ts = int(hist_match.group(2))
                large_scale_ts = int(hist_match.group(3))
                total_tracks = int(hist_match.group(4))
                large_scale = int(hist_match.group(5))
                large_precip = int(hist_match.group(6))
                hist_counts[member] = {
                    "total_ts": total_ts,
                    "largescale_timesteps": large_scale_ts,
                    "total_tracks": total_tracks,
                    "large_scale": large_scale,
                    "large_precip": large_precip
                }
            elif ssp_match:
                member = ssp_match.group(1)
                total_ts = int(ssp_match.group(2))
                large_scale_ts = int(ssp_match.group(3))
                total_tracks = int(ssp_match.group(4))
                large_scale = int(ssp_match.group(5))
                large_precip = int(ssp_match.group(6))
                ssp_counts[member] = {
                    "total_ts": total_ts,
                    "largescale_timesteps": large_scale_ts,
                    "total_tracks": total_tracks,
                    "large_scale": large_scale,
                    "large_precip": large_precip
                }
    return hist_counts, ssp_counts


# === PLOTTING FUNCTION ===

def plot_ratios(index_hist, index_ssp, keys_index, keys_precip, keys_p_event, plotting_dir,
                flattened_index_data=None, flattened_precip_data=None,
                hist_track_counts=None, ssp_track_counts=None,
                n_bootstrap=1000):

    def weighted_mean(values, weights):
        values, weights = np.array(values), np.array(weights)
        if np.sum(weights) == 0:
            return np.mean(values)
        return np.sum(values * weights) / np.sum(weights)

    index_means, index_stds, index_means_bootstrap, index_cis, index_iqrs = [], [], [], [], []
    
    # --- INDEX KEYS (P_pattern and P_storm_given_pattern, weighting with timesteps above large scale applied only to P_storm_given_pattern )
    for k in keys_index:
        members = index_hist.keys()
        hist_values, ssp_values = [], []
        hist_weights, ssp_weights = [], []

        for m in members:
            if k in index_hist[m] and k in index_ssp[m]:
                hist_values.append(index_hist[m][k])
                ssp_values.append(index_ssp[m][k])
                # Apply weights only to P(storm | large scale)
                if k == "P_storm_given_pattern":
                    print(f"Applying weights for member {m} and key {k}")
                    hist_weights.append(hist_track_counts.get(m, {}).get("largescale_timesteps", 1) if hist_track_counts else 1)
                    ssp_weights.append(ssp_track_counts.get(m, {}).get("largescale_timesteps", 1) if ssp_track_counts else 1)
                elif k == "P_pattern":
                    hist_weights.append(1)
                    ssp_weights.append(1)

        # --- Weighted ensemble means (NEW)
        weighted_hist_mean = weighted_mean(hist_values, hist_weights)
        weighted_ssp_mean = weighted_mean(ssp_values, ssp_weights)
        ratio_weighted = weighted_ssp_mean / weighted_hist_mean if weighted_hist_mean != 0 else np.nan
        index_means.append(ratio_weighted)

        # --- Weighted bootstrap
        mean_bootstrap, std, ci, iqr = bootstrap_mean_std(
            hist_values, ssp_values,
            weights_hist=hist_weights, weights_ssp=ssp_weights,
            n_bootstrap=n_bootstrap
        )
        index_means_bootstrap.append(mean_bootstrap)
        index_stds.append(std)
        index_cis.append(ci)
        index_iqrs.append(iqr)

    # --- PRECIP KEYS (P_extreme_given_storm_largescale)
    precip_means, precip_stds, precip_means_bootstrap, precip_cis, precip_iqrs = [], [], [], [], []
    for k in keys_precip:
        members = precip_hist.keys()
        hist_values, ssp_values = [], []
        hist_weights, ssp_weights = [], []
        for m in members:
            if k in precip_hist[m] and k in precip_ssp[m]:
                hist_values.append(precip_hist[m][k])
                ssp_values.append(precip_ssp[m][k])
                # Weighted by large-scale tracks
                hist_weights.append(hist_track_counts.get(m, {}).get("large_scale", 1) if hist_track_counts else 1)
                ssp_weights.append(ssp_track_counts.get(m, {}).get("large_scale", 1) if ssp_track_counts else 1)

        # --- Weighted ensemble mean (NEW)
        weighted_hist_mean = weighted_mean(hist_values, hist_weights)
        weighted_ssp_mean = weighted_mean(ssp_values, ssp_weights)
        ratio_weighted = weighted_ssp_mean / weighted_hist_mean if weighted_hist_mean != 0 else np.nan
        precip_means.append(ratio_weighted)

        mean_bootstrap, std, ci, iqr = bootstrap_mean_std(hist_values, ssp_values,
                                                     weights_hist=hist_weights, weights_ssp=ssp_weights,
                                                     n_bootstrap=n_bootstrap)
        precip_means_bootstrap.append(mean_bootstrap)
        precip_stds.append(std)
        precip_cis.append(ci)
        precip_iqrs.append(iqr)

    # --- P(event)
    p_event_means, p_event_stds, p_event_means_bootstrap, p_event_cis, p_event_iqrs = [], [], [], [], []
    for k in keys_p_event:
        members = index_hist.keys()
        hist_values, ssp_values = [], []
        hist_weights, ssp_weights = [], []
        for m in members:
            if k in hist_p_events[m] and k in ssp_p_events[m]:
                hist_values.append(hist_p_events[m][k])
                ssp_values.append(ssp_p_events[m][k])
                hist_weights.append(1)
                ssp_weights.append(1)

        # --- Weighted ensemble mean (NEW)
        weighted_hist_mean = weighted_mean(hist_values, hist_weights)
        weighted_ssp_mean = weighted_mean(ssp_values, ssp_weights)
        ratio_weighted = weighted_ssp_mean / weighted_hist_mean if weighted_hist_mean != 0 else np.nan
        p_event_means.append(ratio_weighted)

        mean_bootstrap, std, ci, iqr = bootstrap_mean_std(hist_values, ssp_values,
                                                     weights_hist=hist_weights, weights_ssp=ssp_weights,
                                                     n_bootstrap=n_bootstrap)
        p_event_means_bootstrap.append(mean_bootstrap)
        p_event_stds.append(std)
        p_event_cis.append(ci)
        p_event_iqrs.append(iqr)

    # Combine all data
    means = index_means + precip_means + p_event_means
    stds = index_stds + precip_stds + p_event_stds
    means_bootstrap = index_means_bootstrap + precip_means_bootstrap + p_event_means_bootstrap
    cis = index_cis + precip_cis + p_event_cis
    iqrs = index_iqrs + precip_iqrs + p_event_iqrs

    labels = [
        "P(large scale)",
        "P(storm | large scale)",
        "P(precipitation | storm, large scale)",
        "P(event) = P(L)*P(S|L)*P(X|S,L)"
    ]

    
    # compute P(event) from product
    #p_precip_event_mean = np.prod(means[:-1])
    #relative_vars = [(std / mean) ** 2 for mean, std in zip(means[:-1], stds[:-1])]
    #p_precip_event_std = p_precip_event_mean * np.sqrt(np.sum(relative_vars))
    #p_precip_event_mean_bootstrap = np.prod(means_bootstrap[:-1])
    
    #means.append(p_precip_event_mean)
    #stds.append(p_precip_event_std)
    #means_bootstrap.append(p_precip_event_mean_bootstrap)
    #labels.append("P(event) from product of RR terms")
    
        # ------------------------------------------------------------
    # --- BUILD BOXPLOT/WHISKER DATA FROM BOOTSTRAP DISTRIBUTION
    # ------------------------------------------------------------
    x = np.arange(len(means))
    fig, ax = plt.subplots(figsize=(10, 12))

    # Extract 2.5/97.5% CI for whiskers and 25/75% for box
    whisker_low  = [ci[0] for ci in cis]
    whisker_high = [ci[1] for ci in cis]
    iqr_low      = [iqr[0] for iqr in iqrs]
    iqr_high     = [iqr[1] for iqr in iqrs]
    # Height of each box
    box_heights = [iqr_high[i] - iqr_low[i] for i in range(len(means))]

    # ------------------------------------------------------------
    # --- DRAW WHISKERS (95% CI)
    # ------------------------------------------------------------
    for i in range(len(means)):
        ax.plot([x[i], x[i]], [whisker_low[i], whisker_high[i]],
                color="black", linewidth=2.5)

        # whisker caps
        ax.plot([x[i] - 0.15, x[i] + 0.15],
                [whisker_low[i], whisker_low[i]], color="black", linewidth=2.5)
        ax.plot([x[i] - 0.15, x[i] + 0.15],
                [whisker_high[i], whisker_high[i]], color="black", linewidth=2.5)

    # ------------------------------------------------------------
    # --- DRAW Interquartile Range BOXES
    # ------------------------------------------------------------
    for i in range(len(means)):
        box = plt.Rectangle(
            (x[i] - 0.2, iqr_low[i]),
            0.4,
            box_heights[i],
            facecolor="lightblue",
            edgecolor="black",
            linewidth=2.0,
            alpha=0.7
        )
        ax.add_patch(box)

    # ------------------------------------------------------------
    # --- PLOT WEIGHTED ENSEMBLE MEAN (dot)
    # ------------------------------------------------------------
    ax.scatter(
        x, means,
        color="blue",
        s=90,
        zorder=10,
        label="Ens Mean"
    )


    # ------------------------------------------------------------
    # --- OPTIONAL: FLATTENED MEAN OVERLAY
    # ------------------------------------------------------------
    if flattened_index_data is not None and flattened_precip_data is not None:
        print("Adding flattened ensemble mean points to the plot.")
        flat_ratios = []
        flat_ratios.append(flattened_index_data["SSP245"]["P_pattern"]
                            / flattened_index_data["Historical"]["P_pattern"])
        flat_ratios.append(flattened_index_data["SSP245"]["P_storm_given_pattern"]
                            / flattened_index_data["Historical"]["P_storm_given_pattern"])
        flat_ratios.append(flattened_precip_data["SSP245"]["P_extreme_given_storm_largescale"]
                            / flattened_precip_data["Historical"]["P_extreme_given_storm_largescale"])
        flat_ratios.append(flat_ratios[0] * flat_ratios[1] * flat_ratios[2])

        ax.scatter(
            x, flat_ratios,
            color="purple",
            marker="o",
            s=120,
            zorder=12,
            label="Flattened Ens Mean",
            alpha=0.8
        )

    # ------------------------------------------------------------
    # --- AXES / TITLE STYLING
    # ------------------------------------------------------------
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=16, rotation=45, ha='right')
    ax.set_yticks( np.arange(0, max(whisker_high)+0.5, 0.5) )
    ax.set_yticklabels( [f"{tick:.1f}" for tick in np.arange(0, max(whisker_high)+0.5, 0.5)], fontsize=16 )
    ax.set_title(
        "Risk Ratio (SSP245 / Historical)",
        fontsize=20,
        pad=15
    )

    ax.axhline(1, color='gray', linestyle='--', linewidth=1.5)
    ax.grid(axis='y', linestyle=':', linewidth=1.2)

    plt.tight_layout()
    plt.savefig(os.path.join(plotting_dir, "risk_ratios_whisker_box_mean.png"), dpi=300)
    plt.close()

    print(f"Risk ratio plot saved to: {os.path.join(plotting_dir, 'risk_ratios_whisker_box_mean.png')}")




# === MAIN ===

if __name__ == "__main__":
    # Parse regular ensemble results
    index_hist, index_ssp, index_hist_mean, index_ssp_mean = parse_index_file(os.path.join(directory, index_file))
    precip_hist, precip_ssp, precip_hist_mean, precip_ssp_mean = parse_precip_file_event(os.path.join(directory, precip_file))
    hist_p_events, ssp_p_events, hist_p_event_mean, ssp_p_event_mean = parse_p_event(os.path.join(directory, "p_event_product_output.txt"))

    # Parse flattened ensemble means
    #flattened_index_data = read_index_file_flattened(index_file_flattend)
    #flattened_precip_data = read_precip_file_flattened(precip_file_flattened)
    
    #print("Flattened index data:", flattened_index_data)
    #print("Flattened precip data:", flattened_precip_data)

    # Read track counts (weights)
    hist_track_counts, ssp_track_counts = read_tracks_for_weights(tracks_for_weights)
    print("Historical track counts loaded:", len(hist_track_counts), "members")
    print("SSP track counts loaded:", len(ssp_track_counts), "members")

    # Keys
    index_keys = ["P_pattern", "P_storm_given_pattern"]
    precip_keys = ["P_extreme_given_storm_largescale"]
    p_event_keys = ["P_event"]

    # Make globals for means so plot function can read them (keeping original structure)
    index_hist_mean = index_hist_mean
    index_ssp_mean = index_ssp_mean
    precip_hist_mean = precip_hist_mean
    precip_ssp_mean = precip_ssp_mean
    hist_p_event_mean = hist_p_event_mean
    ssp_p_event_mean = ssp_p_event_mean

    flattened_index_data, flattened_precip_data = None, None
    # Plot including flattened points and pass track counts so bootstrap uses them
    plot_ratios(index_hist, index_ssp, index_keys, precip_keys, p_event_keys,
                plotting_dir, flattened_index_data, flattened_precip_data,
                hist_track_counts, ssp_track_counts, n_bootstrap=100)
