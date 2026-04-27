from pathlib import Path
import csv
import math
import numpy as np

FIG_OUTDIR = Path(__file__).resolve().parent.parent / 'img'
TABLE_OUTDIR = Path(__file__).resolve().parent.parent / 'tables'
DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
DATA_CSVS = [DATA_DIR / 'output_1129.csv',
             DATA_DIR / 'output_1130.csv',
             DATA_DIR / 'output_1201.csv',
             DATA_DIR / 'output_1202.csv',
             DATA_DIR / 'output_teraseq_1.csv',
             DATA_DIR / 'output_teraseq_2.csv']

def mean_and_error(nums):
    mean = sum(nums)/len(nums)
    if len(nums) > 1:
        error = math.sqrt(sum([(n-mean)*(n-mean) for n in nums])/(len(nums)-1))
    else:
        error=None
    return mean, error

def read_lines(fname):
    with open(fname) as f:
        lines = f.read().strip().split('\n')
        nums = [float(l) for l in lines]
    return nums

def get_results(names):
    x = {}
    for data_csv in DATA_CSVS:
        with open(data_csv) as f:
            reader = csv.reader(f)
            for row in reader:
                name, has_error, _, sh_time, hs_time = row
                if name in names:
                    if has_error in ['true', 'True', True]:
                        # print(f'{name} has error')
                        pass
                    if not name in x:
                        x[name] = [[], []]
                    x[name][0].append(float(sh_time))
                    x[name][1].append(float(hs_time))
            not_present = [name for name in names if not name in x]
        if len(not_present) > 0:
            # print(f'{not_present} not present in data_csv')
            pass
    for name in x:
        sh_list = np.array(x[name][0]).mean()
        hs_list = np.array(x[name][1]).mean()
        x[name] = (sh_list, hs_list)
    return x

def draw_size_figure(plt, size_names, sh_numbers, hs_numbers):
    x = np.arange(len(size_names))
    sh_numbers = np.array(sh_numbers)
    hs_numbers = np.array(hs_numbers)
    plt.bar(x, sh_numbers/hs_numbers, align='center')
    plt.set_xlabel('Input sets')
    plt.set_ylabel('Relative speed up')
    plt.axhline(y=1, color='black', linestyle=':', linewidth=2, label='baseline')
    # for i, value in enumerate(sh_numbers):
    #     plt.text(i, 1 + .02, f"{sh_numbers[i]:.1f}", 
    #          ha='center', va='bottom', color='black', fontsize=10)
    plt.set_ylim(0, max(sh_numbers/hs_numbers) * 1.08)
    for i, value in enumerate(hs_numbers):
        plt.text(i, sh_numbers[i]/hs_numbers[i], f"{sh_numbers[i]:.1f}s/{hs_numbers[i]:.1f}s", 
                 ha='center', va='bottom', color='black', fontsize=8)
    plt.set_xticks(x, size_names)

def draw_size_scatter_figure(plt, size_names, sh_numbers, hs_numbers):
    single_x = np.arange(len(size_names))
    x = []
    y = []
    small_x = []
    small_y = []
    for size_i in range(len(sh_numbers)):
        for expr_j in range(len(sh_numbers[size_i])):
            if sh_numbers[size_i][expr_j] > 10:
                x.append(size_i)
                y.append(sh_numbers[size_i][expr_j]/hs_numbers[size_i][expr_j])
            else:
                small_x.append(size_i)
                small_y.append(sh_numbers[size_i][expr_j]/hs_numbers[size_i][expr_j])
    plt.scatter(x, y, color='black', s=20)
    plt.scatter(small_x, small_y, color='red', s=20)
    plt.axhline(y=1, color='black', linestyle=':', linewidth=2, label='Threshold')
    plt.set_xticks(single_x, size_names)
    plt.set_xlabel('Input sets')
    plt.set_ylabel('Relative speed up')
    
table_head_template = '''
\\begin{tabularx}{1.0\\linewidth}{llll}
\\toprule
Size & \\texttt{sh} time & \\sys time & Relative Runtime \\\\
\\midrule
'''
table_line_template = '{} & {} & {} & {}\\\\'
table_tail_template = '''
\\bottomrule
\\end{tabularx}
'''

def draw_size_table(names, results, out_file):
    table_outfile = TABLE_OUTDIR / out_file
    lines = []
    for n in names:
        sh_result = f'{results[n][0]:.2f}'
        hs_result = f'{results[n][1]:.2f}'
        relative = f'{results[n][1]/results[n][0]:.3f}'
        line = table_line_template.format(n.replace('_', '\\_'), sh_result, hs_result, relative)
        lines.append(line)

    with open(table_outfile, 'w') as f:
        f.write('\n'.join([table_head_template, *lines, table_tail_template]))

