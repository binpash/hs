import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass
from config import *
from itertools import groupby

plt.rcParams['pdf.fonttype'] = 42

data_path = DATA_DIR / "misspeculation_log"
fig_outfile = FIG_OUTDIR / "cpu_time.pdf"

@dataclass
class Execution:
    cmd: str
    exec_id: str
    start: float
    end: float
    spec: bool

@dataclass
class FullTrace:
    execs: list[Execution]
    commits: dict[str,float]

    def total_time(self):
        s = 0
        for exe in self.execs:
            s += exe.end - exe.start
        return s

    def finals(self):
        finals = {}
        for e in self.execs:
            if e.cmd not in finals:
                finals[e.cmd] = e
            if finals[e.cmd].end < e.end:
                finals[e.cmd] = e
        return finals

    def effective_exec_count(self):
        return len(self.finals())

    def wasted_exec_count(self):
        return len(self.execs) - self.effective_exec_count()
    
    def effective_time(self):
        s = 0
        for exe in self.finals().values():
            s += exe.end - exe.start
        return s

    def wasted_time(self):
        return self.total_time() - self.effective_time()

    def exec_count_overhead(self):
        return self.wasted_exec_count()/(self.effective_exec_count()+self.wasted_exec_count())
    
    def exec_time_overhead(self):
        return self.wasted_time() / self.effective_time()
    
def parse_execs(entries):
    opened = {}
    execs = []
    commits = {}
    for e in entries:
        if e.startswith('start'):
            s, cmd, exec_id, remain = [x.strip() for x in e.split(',')]
            spec, timestamp = remain.split()
            spec, timestamp = spec == 'True', float(timestamp)
            assert exec_id not in opened
            opened[cmd] = Execution(cmd, exec_id, timestamp, -1, spec)
        elif e.startswith('canon_done'):
            s, cmd, remain = [x.strip() for x in e.split(',')]
            exec_id, timestamp = remain.split()
            timestamp = float(timestamp)
            assert cmd in opened
            exe = opened[cmd]
            del opened[cmd]
            exe.end = timestamp
            assert exec_id == exe.exec_id
            execs.append(exe)
            commits[cmd] = timestamp
        elif e.startswith('spec_done'):
            s, cmd, remain = [x.strip() for x in e.split(',')]
            exec_id, timestamp = remain.split()
            timestamp = float(timestamp)
            assert cmd in opened
            exe = opened[cmd]
            assert exe.spec
            assert exe.exec_id == exec_id
            exe.end = timestamp
        elif e.startswith('spec_commit'):
            s, cmd, remain = [x.strip() for x in e.split(',')]
            exec_id, timestamp = remain.split()
            timestamp = float(timestamp)
            assert cmd in opened
            exe = opened[cmd]
            del opened[cmd]
            assert exe.end > 0
            execs.append(exe)
            commits[cmd] = timestamp
        elif e.startswith('reset'):
            s, cmd, remain = [x.strip() for x in e.split(',')]
            _, timestamp = remain.split()
            timestamp = float(timestamp)
            assert cmd in opened
            exe = opened[cmd]
            assert exe.spec
            if exe.end < 0:
                exe.end = timestamp
            del opened[cmd]
            execs.append(exe)
        else:
            breakpoint()
    if len(opened) > 0:
        print(f'opened is not empty')
        breakpoint()
    return FullTrace(execs, commits)

def read_log(fname):
    with open(fname) as f:
        execs = []
        logtext = f.read()
        loglines = logtext.split('\n')
        entries = []
        for line in loglines:
            prefix = '[EXEC_TIME_LOG] '
            if prefix not in line:
                continue
            e = line[line.index(prefix) + len(prefix):]
            entries.append(e)
        fulltrace = parse_execs(entries)
        return fulltrace

def read_logs():
    bs = open(data_path / "manifest").read().split()
    all_traces = []
    for b in bs:
        fpath = data_path / b / "stderr_hs"
        if not fpath.exists():
            fpath = data_path / b / "stderr_hs1"
        fulltrace = read_log(fpath)
        all_traces.append((b, fulltrace))
        print('{:<20}{:>10.3f}{:>10}{:>10.3f}{:>10.3f}{:>10.3f}'.format(
            b,
            fulltrace.total_time(),
            len(fulltrace.commits),
            fulltrace.wasted_time()/fulltrace.total_time(),
            fulltrace.effective_exec_count() + fulltrace.wasted_exec_count(),
            fulltrace.wasted_exec_count()/fulltrace.effective_exec_count(),
        ))

    bs = []
    cs = []
    ts = []
    for benchmark_group, trace_list in groupby(all_traces,
                                               lambda t: t[0].split('/')[0]):
        trace_list = list(trace_list)
        trace_list = [t[1] for t in trace_list]
        c_overhead = sum(map(lambda t: t.exec_count_overhead(), trace_list))/len(trace_list)
        t_overhead = sum(map(lambda t: t.exec_time_overhead(), trace_list))/len(trace_list)
        print('{:<20} {:>10.3f}, {:>10.3f}'.format(benchmark_group, c_overhead, t_overhead/(t_overhead+1)))
        if benchmark_group == 'nlp10x' or benchmark_group == 'nlp100x':
            continue
        bs.append(benchmark_group)
        cs.append(c_overhead)
        ts.append(t_overhead)
    return bs, np.array(cs), np.array(ts)

namemap = {'max_temp': 'NOAA', 'bio4': 'Genomics',
           'sklearn': 'Sklearn', 'sklearn_large': 'SklearnLarge',
           'dgsh': 'DGSH', 'bus-analytics': 'COVID-mts',
           'log-analysis': 'LogAnalysis',
           'nlp': 'NLP', 'web-index': 'WebIndex',
           'teraseq': 'TeraSeq', 'unix_50': 'Unix50'}
    
def draw_things(names, count_overhead, time_overhead):
    fig, ax1 = plt.subplots(1, 1, figsize=(6, 3))
    x = np.array(range(len(names)))
    width=0.4
    ax1.bar(x-0.5*width, count_overhead*100, width=width, label='Relative Misspeculation Count')
    ax1.bar(x+0.5*width, time_overhead*100, width=width, label='Relative Misspeculation Time')
    ax1.set_xticks(x)
    ax1.set_xticklabels([namemap[n] for n in names], rotation=45, ha='right')
    ax1.set_xlabel('Benchmark Set')
    ax1.set_ylabel('Relative Misspeculation (%)')

    plt.legend()
    plt.tight_layout()  # Adjust spacing to prevent overlap
    plt.savefig(fig_outfile)
        
if __name__ == '__main__':
    bs, cs, ts = read_logs()
    draw_things(bs, cs, ts)


