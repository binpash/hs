import pandas as pd
import matplotlib.pyplot as plt
import argparse
import sys
import numpy as np
import re
from matplotlib.ticker import FuncFormatter

## Run with:
## ython3 scripts/generate_pash_vs_hs_barplots.py data_w30/results_w30.csv hs_pash_plot.pdf


# Set global font properties - sans serif for compact style
plt.rcParams.update({
    'font.size': 10,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Helvetica', 'sans-serif'],
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 8,
    'ytick.labelsize': 9,
    'legend.fontsize': 10,
    'figure.titlesize': 12
})

dgsh_name_mappings = {
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "17": "10",
}

nlp_name_mappings = {
    "1_1": "1",
    "2_1": "2",
    "2_2": "3",
    "3_1": "4",
    "3_2": "5",
    "3_3": "6",
    "4_3": "7",
    "4_3b": "8",
    "6_1": "9",
    "6_1_1": "10",
    "6_1_2": "11",
    "6_2": "12",
    "6_3": "13",
    "6_4": "14",
    "6_5": "15",
    "6_7": "16",
    "7_1": "17",
    "7_2": "18",
    "8_1": "19",
    "8_2_1": "20",
    "8_2_2": "21",
    "8_3_2": "22",
    "8_3_3": "23",
}


def get_category(benchmark_name):
    """Get category name for group labels."""
    name = benchmark_name.lower()
    if 'nlp' in name:
        return 'NLP'
    if 'dgsh' in name:
        return 'DGSH'
    if 'teraseq' in name:
        return 'TERA-Seq'
    if 'genomics' in name:
        return 'Genomics'
    if 'sklearn' in name:
        return 'Sklearn'
    if 'noaa' in name:
        return 'NOAA'
    if 'unix' in name:
        return 'Unix50'
    if 'covid' in name:
        return 'COVID-mts'
    if 'log' in name:
        return 'LogAnalysis'
    if 'web' in name:
        return 'WebIndex'
    return 'Other'

def get_display_name(benchmark_name):
    """Map CSV benchmark names to individual display labels (numbers only for NLP/DGSH)."""
    name = benchmark_name.lower()
    
    # TERA-Seq
    if 'teraseq' in name:
        return 'TERA-Seq'
    
    # Genomics
    if 'genomics' in name:
        return 'Genomics'
    
    # Sklearn
    if 'sklearn' in name:
        return 'Sklearn'
    
    # DGSH - return only the number
    if 'dgsh' in name:
        match = re.search(r'dgsh[_-](\d+)', name)
        if match:
            number = match.group(1)  # Just the number
            return dgsh_name_mappings[number]
        assert(False)
        return ''
    
    # NLP - return script ID with dots instead of underscores
    if 'nlp' in name:
        # Match pattern like nlp100x_6_1_1 or nlp100x_8.2_1
        # Capture everything after nlp\d+x_ or nlp\d+x-
        match = re.search(r'nlp\d+x[_-](.+)', name)
        if match:
            script_id = match.group(1)
            # Convert underscores to dots for display
            # e.g., "7_1" -> "7.1", "8.2_1" -> "8.2.1", "6_1_1" -> "6.1.1"
            # Handle both underscores and existing dots
            # display_id = script_id.replace('_', '.')
            clean_script_id = script_id.replace('.', '_')
            display_id = nlp_name_mappings[clean_script_id]
            return display_id
        assert(False)
        return ''
    
    # NOAA
    if 'noaa' in name:
        return 'NOAA'
    
    # Unix50
    if 'unix' in name:
        return 'Unix50'
    
    # COVID-mts
    if 'covid' in name:
        return 'COVID-mts'
    
    # LogAnalysis
    if 'log' in name:
        return 'LogAnalysis'
    
    # WebIndex
    if 'web' in name:
        return 'WebIndex'
    
    # Default
    return benchmark_name

def get_category_order(name):
    """Get category for ordering benchmarks according to Table 1."""
    name = name.lower()
    
    # Table 1 order:
    # 1. TERA-Seq
    # 2. Genomics
    # 3. Sklearn
    # 4. DGSH
    # 5. NLP
    # 6. NOAA
    # 7. Unix50
    # 8. COVID-mts
    # 9. LogAnalysis
    # 10. WebIndex
    # 11. Microbenchmarks
    
    if 'teraseq' in name:
        return (1, name)
    if 'genomics' in name:
        return (2, name)
    if 'sklearn' in name:
        return (3, name)
    if 'dgsh' in name:
        # Extract number for sub-ordering
        match = re.search(r'dgsh[_-](\d+)', name)
        dgsh_num = int(match.group(1)) if match else 999
        return (4, dgsh_num, name)
    if 'nlp' in name:
        # Extract script ID for sub-ordering
        match = re.search(r'nlp\d+x[_-](.+)', name)
        if match:
            script_id = match.group(1)
            # Create a sortable key from script ID
            # Order: 1_1, 2_1, 2_2, 3_1, 3_2, 3_3, 4_3, 4_3b, 6_1, 6_1_1, 6_1_2, 6_2, 6_3, 6_4, 6_5, 6_7, 7_1, 7_2, 8_1, 8.2_1, 8.2_2, 8.3_2, 8.3_3
            nlp_order_map = {
                '1_1': 1, '2_1': 2, '2_2': 3, '3_1': 4, '3_2': 5, '3_3': 6,
                '4_3': 7, '4_3b': 8, '6_1': 9, '6_1_1': 10, '6_1_2': 11,
                '6_2': 12, '6_3': 13, '6_4': 14, '6_5': 15, '6_7': 16,
                '7_1': 17, '7_2': 18, '8_1': 19, '8.2_1': 20, '8.2_2': 21,
                '8.3_2': 22, '8.3_3': 23
            }
            nlp_order = nlp_order_map.get(script_id, 999)
            return (5, nlp_order, name)
        return (5, 999, name)
    if 'noaa' in name:
        return (6, name)
    if 'unix' in name:
        return (7, name)
    if 'covid' in name:
        return (8, name)
    if 'log' in name:
        return (9, name)
    if 'web' in name:
        return (10, name)
    return (11, name)  # Microbenchmarks/Other

def main():
    parser = argparse.ArgumentParser(description='Plot 2-bar comparison for window 30')
    parser.add_argument('input_csv', type=str, help='Path to input CSV file')
    parser.add_argument('output_file', type=str, help='Path to output image file')
    args = parser.parse_args()

    # Read CSV
    try:
        df = pd.read_csv(args.input_csv)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    # Calculate speedups (over sh)
    df['speedup_hs'] = df['sh_time'] / df['hs_time']
    df['speedup_pash'] = df['sh_time'] / df['pash_time']
    
    # Map to display names and categories
    df['display_name'] = df['benchmark_name'].apply(get_display_name)
    df['category'] = df['benchmark_name'].apply(get_category)
    
    # Sort according to Table 1 order
    df['sort_key'] = df['benchmark_name'].apply(get_category_order)
    df = df.sort_values('sort_key')
    df = df.reset_index(drop=True)

    # Setup plot - more compact
    num_benchmarks = len(df)
    width = 0.3  # Slightly narrower bars for compact style
    
    fig, ax = plt.subplots(figsize=(16, 3.5))  # Shorter plot
    
    # Create custom x positions that group benchmarks by family
    # Smaller spacing within families, larger spacing between families
    indices = []
    current_pos = 0
    spacing_within_family = 0.7  # Tighter spacing within same family
    spacing_between_families = 1.1  # Tighter spacing between different families
    
    prev_category = None
    for i in range(num_benchmarks):
        current_category = df.iloc[i]['category']
        
        if prev_category is not None and current_category != prev_category:
            # Different family - add larger spacing
            current_pos += spacing_between_families
        elif i > 0:
            # Same family - add smaller spacing
            current_pos += spacing_within_family
        
        indices.append(current_pos)
        prev_category = current_category
    
    indices = np.array(indices)
    
    # Plot bars - only hS and PaSh (more compact style)
    rects1 = ax.bar(indices - width/2, df['speedup_pash'], width, 
                    label='PaSh', color='#FFDAB9', edgecolor='black', linewidth=0.4)
    rects2 = ax.bar(indices + width/2, df['speedup_hs'], width, 
                    label='hS', color='#ADD8E6', edgecolor='black', linewidth=0.4)
    
    # # --- Existing speedup bars ---
    # rects1 = ax.bar(indices - width, df['speedup_pash'], width,
    #                 label='PaSh', color='#FFDAB9', edgecolor='black', linewidth=0.4)
    # rects2 = ax.bar(indices, df['speedup_hs'], width,
    #                 label='hS', color='#ADD8E6', edgecolor='black', linewidth=0.4)

    # # --- Add secondary axis for absolute sh_time ---
    # ax2 = ax.twinx()

    # # Plot sh_time as a third bar (shifted to the right)
    # rects3 = ax2.bar(indices + width, df['sh_time'], width,
    #                 label='sh time', edgecolor='black', linewidth=0.4)

    # # Label for right y-axis
    # ax2.set_ylabel("sh time (s)", fontsize=12)

    # # Make right y-axis ticks match left style
    # ax2.tick_params(axis='y', labelsize=13)

    # # Optional: automatically scale time axis
    # ax2.set_ylim(0, df['sh_time'].max() * 1.15)


    # Set x-axis limits to remove whitespace on left and right
    # Add small padding (0.5) on each side
    ax.set_xlim(indices[0] - 0.5, indices[-1] + 0.5)

    # Configure Y-axis (Log scale with base 2)
    # ax.set_yscale('log', base=2)
    
    # Set y-axis limits
    ax.set_ylim(0, 10)
    ax.set_ylabel("Speedup vs bash", fontsize=14)

    
    # Set y-axis ticks including 0.125, 0.25, 0.5, 1, 2, 4, 8, 16
    # ticks = []
    # power = -3  # Start from 0.125 (2^-3)
    # while 2 ** power <= 16:
    #     ticks.append(2 ** power)
    #     power += 1
    # ax.set_yticks(ticks)
    
    # Format y-axis labels
    # def format_tick(x, pos):
    #     if x >= 1:
    #         return f"{int(x)}"
    #     elif x == 0.125:
    #         return "0.125"
    #     elif x == 0.25:
    #         return "0.25"
    #     elif x == 0.5:
    #         return "0.5"
    #     else:
    #         return f"{x:.2f}"
    
    # ax.yaxis.set_major_formatter(FuncFormatter(format_tick))
    
    # Make y-axis labels larger
    ax.tick_params(axis='y', labelsize=13)
        
    # Baseline line at y=1 (more compact style)
    ax.axhline(y=1.0, color='black', linestyle='--', linewidth=1.2, label='Baseline (bash)')

    # No y-axis label (using Speedup/Slowdown instead)
    # No title
    
    # Set individual labels (numbers only for NLP/DGSH, full names for others) - larger font
    ax.set_xticks(indices)
    labels = ax.set_xticklabels(df['display_name'], rotation=45, ha='right', fontsize=10)
    
    # Set rotation for all labels based on category
    for i, label in enumerate(labels):
        cat = df.iloc[i]['category']
        if cat not in ['NLP', 'DGSH']:
            # Single benchmarks: larger, more rotated, and bold
            label.set_fontweight('bold')
            label.set_fontsize(11)  # Larger font
            label.set_rotation(20)  # Rotated 20 degrees
        else:
            # NLP and DGSH sublabels: also rotate to 20 degrees, larger font
            label.set_fontsize(10)
            label.set_rotation(20)
    
    # Add group labels (hyperlabels) for NLP and DGSH families - bring closer
    current_category = None
    category_start_idx = None
    
    for i in range(len(df)):
        cat = df.iloc[i]['category']
        if cat != current_category:
            # If we have a previous category group, add the hyperlabel
            if current_category in ['NLP', 'DGSH'] and category_start_idx is not None:
                # Calculate the center of the group using actual x positions
                group_start_x = indices[category_start_idx]
                group_end_x = indices[i - 1]
                group_center = (group_start_x + group_end_x) / 2
                # Add the hyperlabel lower (moved down a couple of mm) - same size as bold labels
                ax.text(group_center, -0.12, current_category, 
                       transform=ax.get_xaxis_transform(),
                       ha='center', va='top', fontsize=11, fontweight='bold')
            
            # Start a new category group
            current_category = cat
            category_start_idx = i
    
    # Handle the last group
    if current_category in ['NLP', 'DGSH'] and category_start_idx is not None:
        group_start_x = indices[category_start_idx]
        group_end_x = indices[-1]
        group_center = (group_start_x + group_end_x) / 2
        ax.text(group_center, -0.09, current_category,
               transform=ax.get_xaxis_transform(),
               ha='center', va='top', fontsize=11, fontweight='bold')
    
    ax.legend(fontsize=13, loc='upper right', frameon=True, fancybox=False, edgecolor='black', ncol=3)

    # Combine legends from both axes
    # handles1, labels1 = ax.get_legend_handles_labels()
    # handles2, labels2 = ax2.get_legend_handles_labels()
    # ax.legend(handles1 + handles2, labels1 + labels2,
    #           fontsize=13, loc='upper right',
    #           frameon=True, fancybox=False, edgecolor='black', ncol=3)



    ax.grid(axis='y', linestyle='--', alpha=0.25, linewidth=0.5)

    # Tighten margins - more compact
    plt.tight_layout()
    plt.subplots_adjust(left=0.06, right=0.98, bottom=0.18, top=0.95)
    
    print(f"Saving plot to {args.output_file}")
    plt.savefig(args.output_file, dpi=300)

if __name__ == "__main__":
    main()

