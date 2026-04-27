#!/usr/bin/env python3
"""
Calculate speedup of hs vs PaSh from results_w30_updated.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Load data
data_path = Path(__file__).parent.parent / "data" / "results_w30_updated.csv"
df = pd.read_csv(data_path)

# Filter out invalid pash times (9999999999999 means PaSh couldn't run)
INVALID_PASH = 9999999999999
df_valid_pash = df[df['pash_time'] < INVALID_PASH].copy()

# Calculate speedups
df['speedup_hs_vs_sh'] = df['sh_time'] / df['hs_time']
df['speedup_hs_vs_pash'] = df['pash_time'] / df['hs_time']
df['speedup_pash_vs_sh'] = df['sh_time'] / df['pash_time']

df_valid_pash['speedup_hs_vs_sh'] = df_valid_pash['sh_time'] / df_valid_pash['hs_time']
df_valid_pash['speedup_hs_vs_pash'] = df_valid_pash['pash_time'] / df_valid_pash['hs_time']
df_valid_pash['speedup_pash_vs_sh'] = df_valid_pash['sh_time'] / df_valid_pash['pash_time']

# Extract benchmark group from name
def get_benchmark_group(name):
    name = name.lower()
    if name.startswith('noaa'):
        return 'NOAA'
    elif name.startswith('genomics'):
        return 'Genomics'
    elif name.startswith('unix_50'):
        return 'Unix50'
    elif name.startswith('dgsh'):
        return 'DGSH'
    elif name.startswith('covid'):
        return 'COVID-mts'
    elif name.startswith('nlp'):
        return 'NLP'
    elif name.startswith('sklearn'):
        return 'Sklearn'
    elif name.startswith('log-analysis'):
        return 'LogAnalysis'
    elif name.startswith('web-index'):
        return 'WebIndex'
    elif name.startswith('teraseq'):
        return 'TeraSeq'
    else:
        return 'Other'

df['benchmark_group'] = df['benchmark_name'].apply(get_benchmark_group)
df_valid_pash['benchmark_group'] = df_valid_pash['benchmark_name'].apply(get_benchmark_group)

# Print individual results
print("=" * 120)
print("Individual Benchmark Results")
print("=" * 120)
print(f"{'Benchmark':<25} {'sh_time':>10} {'hs_time':>10} {'pash_time':>10} {'hs vs sh':>10} {'hs vs pash':>11} {'pash vs sh':>11}")
print("-" * 120)

for _, row in df.iterrows():
    pash_str = f"{row['pash_time']:.1f}" if row['pash_time'] < INVALID_PASH else "N/A"
    speedup_hs_pash_str = f"{row['speedup_hs_vs_pash']:.2f}x" if row['pash_time'] < INVALID_PASH else "N/A"
    speedup_pash_sh_str = f"{row['speedup_pash_vs_sh']:.2f}x" if row['pash_time'] < INVALID_PASH else "N/A"
    print(f"{row['benchmark_name']:<25} {row['sh_time']:>10.1f} {row['hs_time']:>10.1f} {pash_str:>10} {row['speedup_hs_vs_sh']:>9.2f}x {speedup_hs_pash_str:>11} {speedup_pash_sh_str:>11}")

# Calculate geomean per benchmark group
print("\n" + "=" * 100)
print("Geomean Speedup by Benchmark Group")
print("=" * 100)
print(f"{'Benchmark Group':<20} {'# benchmarks':>12} {'hs vs sh':>12} {'hs vs pash':>14} {'pash vs sh':>14}")
print("-" * 100)

for group in df['benchmark_group'].unique():
    group_df = df[df['benchmark_group'] == group]
    group_valid_pash = df_valid_pash[df_valid_pash['benchmark_group'] == group]
    
    n_total = len(group_df)
    geomean_hs_sh = np.exp(np.mean(np.log(group_df['speedup_hs_vs_sh'])))
    
    if len(group_valid_pash) > 0:
        geomean_hs_pash = np.exp(np.mean(np.log(group_valid_pash['speedup_hs_vs_pash'])))
        geomean_pash_sh = np.exp(np.mean(np.log(group_valid_pash['speedup_pash_vs_sh'])))
        hs_pash_str = f"{geomean_hs_pash:.4f}x"
        pash_sh_str = f"{geomean_pash_sh:.4f}x"
    else:
        hs_pash_str = "N/A"
        pash_sh_str = "N/A"
    
    print(f"{group:<20} {n_total:>12} {geomean_hs_sh:>11.4f}x {hs_pash_str:>14} {pash_sh_str:>14}")

# Overall geomean
print("\n" + "=" * 80)
print("Overall Statistics")
print("=" * 80)

overall_geomean_hs_sh = np.exp(np.mean(np.log(df['speedup_hs_vs_sh'])))
overall_geomean_hs_pash = np.exp(np.mean(np.log(df_valid_pash['speedup_hs_vs_pash'])))
overall_geomean_pash_sh = np.exp(np.mean(np.log(df_valid_pash['speedup_pash_vs_sh'])))

print(f"Total benchmarks: {len(df)}")
print(f"Benchmarks where PaSh ran: {len(df_valid_pash)}")
print(f"Benchmarks where PaSh failed: {len(df) - len(df_valid_pash)}")
print()
print(f"Overall geomean speedup (hs vs sh):   {overall_geomean_hs_sh:.4f}x")
print(f"Overall geomean speedup (hs vs pash): {overall_geomean_hs_pash:.4f}x (where pash ran)")
print(f"Overall geomean speedup (pash vs sh): {overall_geomean_pash_sh:.4f}x (where pash ran)")

# Count wins
hs_faster_than_sh = (df['speedup_hs_vs_sh'] > 1).sum()
hs_faster_than_pash = (df_valid_pash['speedup_hs_vs_pash'] > 1).sum()
pash_faster_than_sh = (df_valid_pash['speedup_pash_vs_sh'] > 1).sum()

print()
print(f"hs faster than sh:   {hs_faster_than_sh}/{len(df)} benchmarks")
print(f"hs faster than pash: {hs_faster_than_pash}/{len(df_valid_pash)} benchmarks (where pash ran)")
print(f"pash faster than sh: {pash_faster_than_sh}/{len(df_valid_pash)} benchmarks (where pash ran)")

# Benchmarks where PaSh is faster than hs
print("\n" + "=" * 80)
print("Benchmarks where PaSh is faster than hs:")
print("=" * 80)
pash_wins = df_valid_pash[df_valid_pash['speedup_hs_vs_pash'] < 1]
for _, row in pash_wins.iterrows():
    print(f"  {row['benchmark_name']}: hs={row['hs_time']:.1f}s, pash={row['pash_time']:.1f}s, pash is {1/row['speedup_hs_vs_pash']:.2f}x faster")

# Benchmarks where PaSh is slower than sh
print("\n" + "=" * 80)
print("Benchmarks where PaSh is slower than sh:")
print("=" * 80)
pash_slower = df_valid_pash[df_valid_pash['speedup_pash_vs_sh'] < 1]
for _, row in pash_slower.iterrows():
    print(f"  {row['benchmark_name']}: sh={row['sh_time']:.1f}s, pash={row['pash_time']:.1f}s, pash is {1/row['speedup_pash_vs_sh']:.2f}x slower")

