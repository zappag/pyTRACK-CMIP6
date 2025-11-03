import re
import matplotlib.pyplot as plt
import numpy as np
import os

# === FILE SETUP ===
directory = "/home/ghinassi/work/track_plots/risk_ratio_probabilities/"
index_file = "index_threshold_comparison_output.txt"
precip_file = "precipitation_extreme_probabilities.txt"

#plotting dir
plotting_dir = "/home/ghinassi/work/track_plots/risk_ratio_probabilities/"
if not os.path.exists(plotting_dir):
    os.makedirs(plotting_dir, exist_ok=True)
    
"""
Large-scale Pattern and Storm Probabilities (file "index_threshold_comparison_output.txt")

Large-scale Pattern and Storm Probabilities
ERA5: P(pattern) = 0.0354, P(storm | pattern) = 0.1100
Historical:
HIST r2i1p1f1: P(pattern) = 0.0227, P(storm | pattern) = 0.2188
HIST r7i1p1f1: P(pattern) = 0.0216, P(storm | pattern) = 0.1639
HIST r10i1p1f1: P(pattern) = 0.0191, P(storm | pattern) = 0.1667
HIST r12i1p1f1: P(pattern) = 0.0142, P(storm | pattern) = 0.0750
HIST r14i1p1f1: P(pattern) = 0.0121, P(storm | pattern) = 0.2353
HIST r16i1p1f1: P(pattern) = 0.0099, P(storm | pattern) = 0.1429
HIST r17i1p1f1: P(pattern) = 0.0238, P(storm | pattern) = 0.0896
HIST r18i1p1f1: P(pattern) = 0.0135, P(storm | pattern) = 0.1842
HIST r19i1p1f1: P(pattern) = 0.0269, P(storm | pattern) = 0.1579
HIST r20i1p1f1: P(pattern) = 0.0195, P(storm | pattern) = 0.1091
HIST r21i1p1f1: P(pattern) = 0.0163, P(storm | pattern) = 0.0217
HIST r22i1p1f1: P(pattern) = 0.0198, P(storm | pattern) = 0.0926
HIST r23i1p1f1: P(pattern) = 0.0202, P(storm | pattern) = 0.1579
HIST r24i1p1f1: P(pattern) = 0.0167, P(storm | pattern) = 0.2340
HIST r25i1p1f1: P(pattern) = 0.0191, P(storm | pattern) = 0.1481
Hist ens mean: P(pattern) = 0.0184, P(storm | pattern) = 0.1465
ScenarioMIP SSP245:
SSP245 r2i1p1f1: P(pattern) = 0.0163, P(storm | pattern) = 0.1087
SSP245 r7i1p1f1: P(pattern) = 0.0149, P(storm | pattern) = 0.1190
SSP245 r10i1p1f1: P(pattern) = 0.0131, P(storm | pattern) = 0.2973
SSP245 r12i1p1f1: P(pattern) = 0.0170, P(storm | pattern) = 0.0833
SSP245 r14i1p1f1: P(pattern) = 0.0131, P(storm | pattern) = 0.1622
SSP245 r16i1p1f1: P(pattern) = 0.0106, P(storm | pattern) = 0.1000
SSP245 r17i1p1f1: P(pattern) = 0.0096, P(storm | pattern) = 0.1111
SSP245 r18i1p1f1: P(pattern) = 0.0124, P(storm | pattern) = 0.1429
SSP245 r19i1p1f1: P(pattern) = 0.0106, P(storm | pattern) = 0.1667
SSP245 r20i1p1f1: P(pattern) = 0.0150, P(storm | pattern) = 0.0976
SSP245 r21i1p1f1: P(pattern) = 0.0135, P(storm | pattern) = 0.1053
SSP245 r22i1p1f1: P(pattern) = 0.0124, P(storm | pattern) = 0.2857
SSP245 r23i1p1f1: P(pattern) = 0.0117, P(storm | pattern) = 0.2121
SSP245 r24i1p1f1: P(pattern) = 0.0142, P(storm | pattern) = 0.1250
SSP245 r25i1p1f1: P(pattern) = 0.0043, P(storm | pattern) = 0.4167
SSP245 ens mean: P(pattern) = 0.0126, P(storm | pattern) = 0.1689

"""
"""
Precipitation probabilities (file "precipitation_extreme_probabilities.txt")

Precipitation probabilities:
ERA5: P(extreme) = 0.0085, P(extreme | storm | large scale) = 0.3636
Historical:
HIST r2i1p1f1: P(extreme) = 0.0089, P(extreme | storm | large scale) = 0.2143
HIST r7i1p1f1: P(extreme) = 0.0092, P(extreme | storm | large scale) = 0.4000
HIST r10i1p1f1: P(extreme) = 0.0067, P(extreme | storm | large scale) = 0.1111
HIST r12i1p1f1: P(extreme) = 0.0057, P(extreme | storm | large scale) = 0.0000
HIST r14i1p1f1: P(extreme) = 0.0085, P(extreme | storm | large scale) = 0.1250
HIST r16i1p1f1: P(extreme) = 0.0067, P(extreme | storm | large scale) = 0.0000
HIST r17i1p1f1: P(extreme) = 0.0071, P(extreme | storm | large scale) = 0.1667
HIST r18i1p1f1: P(extreme) = 0.0060, P(extreme | storm | large scale) = 0.4286
HIST r19i1p1f1: P(extreme) = 0.0103, P(extreme | storm | large scale) = 0.5000
HIST r20i1p1f1: P(extreme) = 0.0082, P(extreme | storm | large scale) = 0.0000
HIST r21i1p1f1: P(extreme) = 0.0060, P(extreme | storm | large scale) = 0.0000
HIST r22i1p1f1: P(extreme) = 0.0085, P(extreme | storm | large scale) = 0.0000
HIST r23i1p1f1: P(extreme) = 0.0078, P(extreme | storm | large scale) = 0.3333
HIST r24i1p1f1: P(extreme) = 0.0085, P(extreme | storm | large scale) = 0.1818
HIST r25i1p1f1: P(extreme) = 0.0092, P(extreme | storm | large scale) = 0.1250
Hist ens mean: P(extreme) = 0.0078, P(extreme | storm | large scale) = 0.1724
ScenarioMIP SSP245:
SSP245 r2i1p1f1: P(extreme) = 0.0088, P(extreme | storm | large scale) = 0.0000
SSP245 r7i1p1f1: P(extreme) = 0.0117, P(extreme | storm | large scale) = 0.2000
SSP245 r10i1p1f1: P(extreme) = 0.0183, P(extreme | storm | large scale) = 0.3636
SSP245 r12i1p1f1: P(extreme) = 0.0179, P(extreme | storm | large scale) = 0.5000
SSP245 r14i1p1f1: P(extreme) = 0.0161, P(extreme | storm | large scale) = 0.6667
SSP245 r16i1p1f1: P(extreme) = 0.0081, P(extreme | storm | large scale) = 0.3333
SSP245 r17i1p1f1: P(extreme) = 0.0187, P(extreme | storm | large scale) = 0.3333
SSP245 r18i1p1f1: P(extreme) = 0.0183, P(extreme | storm | large scale) = 0.4000
SSP245 r19i1p1f1: P(extreme) = 0.0103, P(extreme | storm | large scale) = 0.8000
SSP245 r20i1p1f1: P(extreme) = 0.0117, P(extreme | storm | large scale) = 0.5000
SSP245 r21i1p1f1: P(extreme) = 0.0179, P(extreme | storm | large scale) = 0.2500
SSP245 r22i1p1f1: P(extreme) = 0.0139, P(extreme | storm | large scale) = 0.4000
SSP245 r23i1p1f1: P(extreme) = 0.0139, P(extreme | storm | large scale) = 0.1429
SSP245 r24i1p1f1: P(extreme) = 0.0147, P(extreme | storm | large scale) = 0.4000
SSP245 r25i1p1f1: P(extreme) = 0.0143, P(extreme | storm | large scale) = 0.6000
SSP245 ens mean: P(extreme) = 0.0143, P(extreme | storm | large scale) = 0.3927
"""


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


def parse_precip_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    hist_pattern = re.findall(r"HIST\s+(r\d+i1p1f1): P\(extreme\) = ([\d.]+), P\(extreme \| storm \| large scale\) = ([\d.]+)", content)
    ssp_pattern = re.findall(r"SSP245\s+(r\d+i1p1f1): P\(extreme\) = ([\d.]+), P\(extreme \| storm \| large scale\) = ([\d.]+)", content)
    
    hist_data = {m: {"P_extreme": float(p), "P_extreme_given_storm_largescale": float(s)} for m, p, s in hist_pattern}
    ssp_data = {m: {"P_extreme": float(p), "P_extreme_given_storm_largescale": float(s)} for m, p, s in ssp_pattern}
    # Get ensemble means
    hist_mean_match = re.search(r"Hist ens mean: P\(extreme\) = ([\d.]+), P\(extreme \| storm \| large scale\) = ([\d.]+)", content)
    ssp_mean_match = re.search(r"SSP245 ens mean: P\(extreme\) = ([\d.]+), P\(extreme \| storm \| large scale\) = ([\d.]+)", content)
    
    hist_mean = {"P_extreme": float(hist_mean_match.group(1)), "P_extreme_given_storm_largescale": float(hist_mean_match.group(2))}
    ssp_mean = {"P_extreme": float(ssp_mean_match.group(1)), "P_extreme_given_storm_largescale": float(ssp_mean_match.group(2))}
    # Return parsed data
    hist_data = {k: v for k, v in hist_data.items() if k in ssp_data}
    ssp_data = {k: v for k, v in ssp_data.items() if k in hist_data}
    return hist_data, ssp_data, hist_mean, ssp_mean


# === RATIO CALCULATION FUNCTION ===

def compute_ratios(hist_data, ssp_data, keys):
    ratios = {}
    for member in hist_data:
        if member in ssp_data:
            ratios[member] = {k: ssp_data[member][k] / hist_data[member][k] if hist_data[member][k] != 0 else np.nan for k in keys}
    return ratios


# === PLOTTING FUNCTION ===

def plot_ratios(index_ratios, precip_ratios, index_mean_ratio, precip_mean_ratio, keys_index, keys_precip, plotting_dir):
    import matplotlib.pyplot as plt
    import numpy as np
    import os

    members = list(index_ratios.keys())
    x = np.arange(len(members))
    width = 0.7

    fig, axs = plt.subplots(4, 1, figsize=(12, 16), sharex=True)

    plots = [
        (index_ratios, index_mean_ratio, keys_index[0], "Ratio of P(large scale)"),
        (index_ratios, index_mean_ratio, keys_index[1], "Ratio of P(storm | large scale)"),
        (precip_ratios, precip_mean_ratio, keys_precip[1], "Ratio of P(precipitation | storm | large scale)"),
        (precip_ratios, precip_mean_ratio, keys_precip[0], "Ratio of P(precipitation)"),
    ]

    for ax, (data, mean_dict, key, title) in zip(axs, plots):
        values = [data[m][key] for m in members]
        mean_value = mean_dict[key]

        # Plot member bars
        ax.bar(x, values, width=width, color='C0', label='Members')

        # Check if values have variability; fallback to bar if not
        values = [v for v in values if not np.isnan(v)]  # Remove NaNs
        if np.allclose(values, values[0]):
            ax.bar(len(members), mean_value, width=width, color='red', label='Ensemble Mean')
        else:
            ax.boxplot(
                values,
                positions=[len(members)],
                widths=0.5,
                vert=True,
                patch_artist=True,
                showfliers=False,
                boxprops=dict(facecolor='red', color='black'),
                medianprops=dict(color='black'),
                whiskerprops=dict(color='black', linestyle='--'),
                capprops=dict(color='black')
            )

        # Grid customization: dotted horizontal, no vertical
        ax.grid(axis='y', linestyle=':', linewidth=0.8)
        ax.grid(axis='x', visible=False)

        ax.set_title(title)
        ax.set_ylabel("Ratio")

    axs[-1].set_xticks(np.append(x, len(members)))
    axs[-1].set_xticklabels(members + ['Ens mean'], rotation=45)
    axs[0].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(plotting_dir, "risk_ratio_subplots.png"))
    print(f"Plot saved to {os.path.join(plotting_dir, 'risk_ratio_subplots.png')}")



# === MAIN ===

if __name__ == "__main__":
    # Parse files
    index_hist, index_ssp, index_hist_mean, index_ssp_mean = parse_index_file(os.path.join(directory, index_file))
    precip_hist, precip_ssp, precip_hist_mean, precip_ssp_mean = parse_precip_file(os.path.join(directory, precip_file))


    # Compute member ratios
    index_ratios = compute_ratios(index_hist, index_ssp, ["P_pattern", "P_storm_given_pattern"])
    precip_ratios = compute_ratios(precip_hist, precip_ssp, ["P_extreme", "P_extreme_given_storm_largescale"])
    
    
    print("Members in index:", set(index_ratios.keys()))
    print("Members in precip:", set(precip_ratios.keys()))

    # Compute ensemble mean ratios
    index_mean_ratio = {k: index_ssp_mean[k] / index_hist_mean[k] for k in index_hist_mean}
    precip_mean_ratio = {k: precip_ssp_mean[k] / precip_hist_mean[k] for k in precip_hist_mean}

    # Plotting
    plot_ratios(index_ratios, precip_ratios, index_mean_ratio, precip_mean_ratio,
                ["P_pattern", "P_storm_given_pattern"],
                ["P_extreme", "P_extreme_given_storm_largescale"],
                plotting_dir)


    print_summary = True  # Set to False to disable summary output
    if print_summary:
        # Print summary
        print("Index Ratios (SSP245 / HIST):")
        for member, ratios in index_ratios.items():
            print(f"{member}: {ratios}")

        print("\nPrecipitation Ratios (SSP245 / HIST):")
        for member, ratios in precip_ratios.items():
            print(f"{member}: {ratios}")

        print("\nEnsemble Mean Ratios:")
        print(f"Index: {index_mean_ratio}")
        print(f"Precipitation: {precip_mean_ratio}")
        # now compute the P(prec) = P(large scale)  * P(storm | large scale) * P(extreme | storm | large scale) of the ens mean
        index_mean_precip = index_mean_ratio["P_pattern"] * index_mean_ratio["P_storm_given_pattern"] * precip_mean_ratio["P_extreme_given_storm_largescale"]
        print(f"Ensemble Mean P(extreme precipitation) due to Mediterranean storms = {index_mean_precip:.4f}")
        print(f"Ensemble Mean P(extreme precipitation) = {precip_mean_ratio['P_extreme']:.4f}")
        

            
