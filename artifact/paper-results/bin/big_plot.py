#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gmean
from config import *


plt.rcParams['pdf.fonttype'] = 42

fig_outfile = FIG_OUTDIR / "main_results.pdf"

noaa_names = ['max_temp/tiny',
              'max_temp/small',
              'max_temp/medium',
              'max_temp/large']
genomics_names = ['bio4/small',
                  'bio4/medium',
                  'bio4/large']
unix_50_names = ['unix_50/full',
                 'unix_50/full10m',
                 'unix_50/full100m']
dgsh_names = [#'dgsh/1',
              #'dgsh/1-10x',
              # 'dgsh/1-100x',
              'dgsh/1-1000x',
              'dgsh/2',
              'dgsh/3',
              'dgsh/4',
              #'dgsh/5',
              #'dgsh/5-10x',
              # 'dgsh/5-100x',
              'dgsh/5-1000x',
              #'dgsh/6',
              #'dgsh/6-10x',
              # 'dgsh/6-100x',
              'dgsh/6-1000x',
              #'dgsh/7',
              #'dgsh/7-10x',
              #'dgsh/7-100x',
              'dgsh/7-1000x',
              #'dgsh/8',
              #'dgsh/8-10x',
              #'dgsh/8-100x',
              'dgsh/8-1000x',
              'dgsh/9',
              #'dgsh/17',
              #'dgsh/17-10x',
              #'dgsh/17-100x',
              'dgsh/17-1000x',
              'dgsh/18']
covid_mts_names = ['bus-analytics/full',
                   'bus-analytics/full-100M',
                   'bus-analytics/full-10G']
log_analysis_names = ['log-analysis/small',
                      'log-analysis/medium',
                      'log-analysis/full']
nlp_orig_names = ['nlp/1_1',
                  'nlp/2_1',
                  'nlp/2_2',
                  'nlp/3_1',
                  'nlp/3_2',
                  'nlp/3_3',
                  'nlp/4_3',
                  'nlp/4_3b',
                  'nlp/6_1',
                  'nlp/6_1_1',
                  'nlp/6_1_2',
                  'nlp/6_2',
                  'nlp/6_3',
                  'nlp/6_4',
                  'nlp/6_5',
                  'nlp/6_7',
                  'nlp/7_1',
                  'nlp/7_2',
                  'nlp/8_1',
                  'nlp/8.2_1',
                  'nlp/8.2_2',
                  'nlp/8.3_2',
                  'nlp/8.3_3']
nlp_10x_names = [name.replace('nlp', 'nlp10x') for name in nlp_orig_names]
nlp_100x_names = [name.replace('nlp', 'nlp100x') for name in nlp_orig_names]
sklearn_names = ['sklearn',
                 'sklearn_large']
web_index_names = ['web-index/web-index-100m']
teraseq_names = ['teraseq/dRNASeq', 'teraseq/mouse_SIRV', 'teraseq/5TERA3',
                 'teraseq/Akron5Seq', 'teraseq/RNASeq', 'teraseq/TERA3',
                 'teraseq/5TERA', 'teraseq/5TERA-short', 'teraseq/RiboSeq']

fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(8, 3), constrained_layout=True)

names = teraseq_names
results = get_results(names)
taraseq_sh_values = [results[n][0] for n in names]
teraseq_hs_values = [results[n][1] for n in names]

names = dgsh_names
results = get_results(names)
dgsh_sh_values = [results[n][0] for n in names]
dgsh_hs_values = [results[n][1] for n in names]

names = nlp_100x_names
results = get_results(names)
nlp_sh_values = [results[n][0] for n in names]
nlp_hs_values = [results[n][1] for n in names]

draw_size_scatter_figure(axes[0], ['TERA-seq', 'DGSH', 'NLP'],
                         [taraseq_sh_values, dgsh_sh_values, nlp_sh_values],
                         [teraseq_hs_values, dgsh_hs_values, nlp_hs_values])

labels = ['Genomics', 'NOAA', 'Unix50', 'COVID-mts', 'LogAnalysis', 'Sklearn', 'WebIndex']
names = [genomics_names, noaa_names, unix_50_names, covid_mts_names, log_analysis_names, sklearn_names,
         web_index_names]
ax = axes[1]
ys = []
for label, name_list in zip(labels, names):
    results = get_results(name_list)
    sh_values = np.array([results[n][0] for n in name_list])
    hs_values = np.array([results[n][1] for n in name_list])
    y = (sh_values/hs_values).max()
    ys.append(y)
x = np.arange(len(labels))
ax.bar(x, ys)
plt.axhline(y=1, color='black', linestyle=':', linewidth=2, label='baseline')
ax.set_xticks(x, labels, rotation=45, ha='right')

plt.savefig(fig_outfile)
