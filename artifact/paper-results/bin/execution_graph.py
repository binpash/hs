import numpy as np
import matplotlib 
import matplotlib.pyplot as plt
from config import *
from itertools import repeat, chain
from dataclasses import dataclass
from cpu_time import read_log, Execution
from matplotlib.patches import Rectangle, Patch

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['hatch.linewidth'] = 5.0  # Make hatch lines thicker
plt.rcParams['hatch.color'] = 'white'    # Set hatch color

data_path = DATA_DIR / "misspeculation_log"
fig_outfile = FIG_OUTDIR / "execution_bars.pdf"

# @dataclass
# class Execution:
#     cmd: str
#     start: float
#     end: float
#     spec: bool


fulltrace = read_log(data_path / "max_temp" / "medium" / "stderr_hs")

data = fulltrace.execs
commit = list(fulltrace.commits.values())
x = list(fulltrace.commits.keys())
fig, ax = plt.subplots(figsize=(3, 5))

start_time = data[0].start
finals = {}
for e in data:
    e.start -= start_time
    e.end -= start_time
    if e.cmd not in finals:
        finals[e.cmd] = e
    if finals[e.cmd].end < e.end:
        finals[e.cmd] = e

commit = [x - start_time for x in commit]

rects = []
for i in range(10):
    rect = Rectangle(
        (0, 5*i + 0.7),
        560,          # width
        4.6,          # height
        linewidth=0,  # border width (0 for no border)
        edgecolor='none',
        facecolor='lightblue',
        alpha=0.3,    # transparency
        zorder=-1     # place behind other elements
    )
    rects.append(rect)
    ax.add_patch(rect)
proxy = Patch(facecolor='lightblue', 
                    edgecolor='blue',
                    alpha=0.5,
                    label='Iteration')
ax.legend(handles=[proxy])
        
data_wrong = [e for e in data if e not in finals.values() and e.cmd in x]
data_right = [e for e in data if e not in data_wrong and e.spec and e.cmd in x]
data_canon = [e for e in data if e not in data_wrong and e not in data_right and e.cmd in x]
bars = ax.barh([x.index(e.cmd) for e in data_wrong], [e.end-e.start for e in data_wrong], left=[e.start for e in data_wrong], 
               height=0.5, color='red', edgecolor='black', linewidth=0.5, label='wrong speculation')
for b in bars:
    b._hatch_color = matplotlib.colors.to_rgba('white')
bars = ax.barh([x.index(e.cmd) for e in data_right], [e.end-e.start for e in data_right], left=[e.start for e in data_right], 
               height=0.5, color='lightgreen', edgecolor='black', linewidth=0.5, label='correct speculation')
for b in bars:
    b._hatch_color = matplotlib.colors.to_rgba('white')
bars = ax.barh([x.index(e.cmd) for e in data_canon], [e.end-e.start for e in data_canon], left=[e.start for e in data_canon], 
               height=0.5, color='green', edgecolor='black', linewidth=0.5, label='direct execution')
# bars = ax.barh(list(range(len(x))), [1] * len(x), left=np.array(commit) - 0.5, 
#                height=0.8, color='blue', label='commit')

dots = ax.scatter(commit, list(range(len(x))), marker='o',
               color='blue', s=7, label='commit')
ax.grid(axis='x', linestyle='--', linewidth=1, alpha=0.7)
ax.set_yticks([])
ax.set_yticklabels([])
ax.set_ylim(-0.5, 40.5)
ax.set_xlim(0, 400)
ax.set_xlabel('Time')
ax.invert_yaxis()
ax.legend()
plt.tight_layout()
plt.savefig(fig_outfile)
