import re
import os.path
import sys
from typing import Tuple
from dataclasses import dataclass

# Global TODOs:
# handle pwd, such that open and stat can work

# not handled: listxattr, llistxattr, getxattr, lgetxattr, pivot_root, mount, umount2
# setxattr lsetxattr removexattr lremovexattr, fanotify_mark, renameat2, chroot, quotactl
# handled individually openat, open, chdir, clone, rename
# TODO: link, symlink, renameat, symlinkat
r_first_path_set = set(['execve', 'stat', 'lstat', 'access', 'statfs',
                        'readlink', 'execve'])
w_first_path_set = set(['mkdir', 'rmdir', 'truncate', 'creat', 'chmod', 'chown',
                        'lchown', 'utime', 'mknod', 'utimes', 'acct', 'unlink'])
r_fd_path_set = set(['fstatat', 'newfstatat', 'statx', 'name_to_handle_at',
                     'readlinkat', 'faccessat', 'execveat'])
w_fd_path_set = set(['unlinkat', 'utimensat', 'mkdirat', 'mknodat', 'fchownat', 'futimeat',
                     'unlinkat', 'linkat', 'fchmodat', 'utimensat'])
ignore_set = set(['getpid', 'getcwd'])


@dataclass
class ExitStatus:
    exitcode: int
    
def parse_info(l):
    if "exited" in l:
        start = len("+++ exited with ")
        end = -len(" +++")
        return ExitStatus(int(l[start:end]))
    elif 'killed' in l:
        return ExitStatus(-1)
    else:
        raise ValueError

@dataclass
class RFile:
    fname: str
    def __init__(self, fname):
        self.fname = os.path.normpath(fname)

@dataclass
class WFile:
    fname: str
    def __init__(self, fname):
        self.fname = os.path.normpath(fname)

class Context:
    def __init__(self):
        self.line_dict = {}
        self.curdir_dict = {}
        self.pid_group_dict = {}

    def do_clone(self, parent, child):
        self.pid_group_dict[child] = parent
        
    def set_dir(self, path, pid=None):
        self.curdir_fallback = path
        if pid and pid in self.pid_group_dict:
            pid = self.pid_group_dict[pid]
        if pid:
            self.curdir_dict[pid] = path

    def get_dir(self, pid: int):
        if pid in self.pid_group_dict:
            pid = self.pid_group_dict[pid]
        if not pid in self.curdir_dict:
            self.curdir_dict[pid] = self.curdir_fallback
        return self.curdir_dict[pid]

    def push_half_line(self, pid: int, l):
        index = l.find('<unfinished')
        self.line_dict[pid] = l[:index].strip()

    def pop_complete_line(self, pid: int, l):
        index = l.find('resumed>') + len('resumed>')
        total_line = self.line_dict[pid] + l[index:].strip()
        del self.line_dict[pid]
        return total_line

def parse_string(s):
    s = s.strip()
    # handling cases such as utimensat
    # if the open fails we will mark the file
    # as a read when we handle return value anyway so it's fine
    if s == 'NULL':
        return ''
    assert s[0] == '"' and s[-1] == '"'
    return bytes(s[1:-1], "utf-8").decode("unicode_escape")

def between(s, d1, d2):
    return s.find(d1) + len(d1), s.rfind(d2)

def is_absolute(path):
    return path[0] == '/'

def is_ret_err(ret: str):
    ret = ret.strip()
    return ret[0] == '-'

def convert_absolute(cur_dir, path):
    if is_absolute(path):
        return path
    else:
        return os.path.join(cur_dir, path)

def get_path_first_path(pid, args, ctx):
    a = parse_string(args.split(sep=',', maxsplit=1)[0])
    return convert_absolute(ctx.get_dir(pid), a)

def parse_r_first_path(pid, args, ret, ctx):
    return RFile(get_path_first_path(pid, args, ctx))

def parse_w_first_path(pid, args, ret, ctx):
    path = get_path_first_path(pid, args, ctx)
    if is_ret_err(ret):
        return RFile(path)
    else:
        return WFile(path)

def get_path_at(pid, positions, args, ctx):
    args = args.split(sep=',')
    if isinstance(positions, list):
        rets = []
        for x in args:
            rets.append(convert_absolute(ctx.get_dir(pid), parse_string(x)))
        return rets
    else:
        return convert_absolute(ctx.get_dir(pid), parse_string(x))

def parse_rename(pid, args, ret, ctx):
    path_a, path_b = get_path_at(pid, [0, 1], args, ctx)
    return WFile(path_a), WFile(path_b)

def parse_link(pid, args, ret, ctx):
    path_a, path_b = get_path_at(pid, [0, 1], args, ctx)
    return RFile(path_a), WFile(path_b)

def parse_renameat(pid, args, ret, ctx):
    

def parse_chdir(pid, args, ret, ctx):
    new_path = get_path_first_path(pid, args, ctx)
    if not is_ret_err(ret):
        ctx.set_dir(new_path, pid)
    return RFile(new_path)

def handle_open_flag(flags):
    if 'O_RDONLY' in flags:
        return 'r'
    else:
        return 'w'

def handle_open_common(total_path, flags, ret):
    if handle_open_flag(flags) == 'r':
        return RFile(total_path)
    if is_ret_err(ret):
        return RFile(total_path)
    return WFile(total_path)

def parse_openat(args, ret):
    if args.count(',') <= 2:
        dfd, path, flags = args.split(',', maxsplit=2)
    else:
        dfd, path, flags, _ = args.split(',', maxsplit=3)
    path = parse_string(path)
    if is_absolute(path):
        total_path = path
    else:
        begin, end = between(dfd, '<', '>')
        pwd = dfd[begin:end]
        total_path = os.path.join(pwd, path)
    return handle_open_common(total_path, flags, ret)

def parse_open(pid, args, ret, ctx):
    total_path = get_path_first_path(pid, args, ctx)
    flags = args.split(',')[1]
    return handle_open_common(total_path, flags, ret)
    
def get_path_from_fd_path(args):
    a0, a1, _ = args.split(sep=',', maxsplit=2)
    a1 = parse_string(a1)
    if len(a1) and a1[0] == '/':
        return a1
    else:
        begin, end = between(a0, '<', '>')
        a0 = a0[begin:end]
        return os.path.join(a0, a1)

def parse_r_fd_path(args, ret):
    return RFile(get_path_from_fd_path(args))

def parse_w_fd_path(args, ret):
    if is_ret_err(ret):
        return RFile(get_path_from_fd_path(args))
    else:
        return WFile(get_path_from_fd_path(args))

def has_clone_fs(flags):
    if 'CLONE_FS' in flags:
        return True
    else:
        return False

def parse_clone(pid, args, ret, ctx):
    try:
        child = int(ret)
    except ValueError:
        child = -1
    if child < 0:
        return
    arg_list = [x.strip() for x in args.split(',')]
    flags = [arg for arg in arg_list if arg.startswith('flags=')][0]
    flags = flags[len('flags='):]
    if has_clone_fs(flags):
        ctx.do_clone(pid, child)
    
def parse_syscall(pid, syscall, args, ret, ctx):
    if syscall in r_first_path_set:
        return parse_r_first_path(pid, args, ret, ctx)
    elif syscall in w_first_path_set:
        return parse_w_first_path(pid, args, ret, ctx)
    elif syscall == 'openat':
        return parse_openat(args, ret)
    elif syscall == 'chdir':
        return parse_chdir(pid, args, ret, ctx)
    elif syscall == 'open':
        return parse_open(pid, args, ret, ctx)
    elif syscall in r_fd_path_set:
        return parse_r_fd_path(args, ret)
    elif syscall in w_fd_path_set:
        return parse_w_fd_path(args, ret)
    elif syscall == 'rename':
        return parse_rename(pid, args, ret, ctx)
    elif syscall == 'clone':
        return parse_clone(pid, args, ret, ctx)
    elif syscall in ignore_set:
        return None
    else:
        raise ValueError('Unclassified syscall ' + syscall)

def strip_pid(l):
    if l[0].isdigit():
        pair = l.split(maxsplit=1)
        return int(pair[0]), pair[1]
    else:
        raise ValueError('expect pid')

def handle_info(l):
    if '+++' in l:
        return True, parse_info(l)
    elif '---' in l:
        return True, None
    else:
        return False, None

def parse_line(l, ctx):
    pid, l = strip_pid(l)
    is_info, info = handle_info(l)
    if is_info:
        return info
    if not len(l):
        return None
    if "<unfinished" in l:
        ctx.push_half_line(pid, l)
        return None
    elif "resumed>" in l:
        l = ctx.pop_complete_line(pid, l)
    lparen = l.find('(')
    equals = l.rfind('=')
    rparen = l[:equals].rfind(')')
    assert lparen >= 0 and equals >= 0 and rparen >= 0
    syscall = l[:lparen]
    ret = l[equals+1:]
    args = l[lparen+1:rparen]
    return parse_syscall(pid, syscall, args, ret, ctx)

def parse_exit_code(trace_object) -> int:
    if len(trace_object) < 1:
        return None
    l = trace_object[0]
    first_pid, _ = strip_pid(l)
    for l in trace_object:
        pid, tmpl = strip_pid(l)
        is_info, info = handle_info(tmpl)
        if is_info and pid == first_pid and isinstance(info, ExitStatus):
            return info.exitcode
    raise ValueError("No exitcode")

def parse_and_gather_cmd_rw_sets(trace_object) -> Tuple[set, set]:
    ctx = Context()
    ctx.set_dir(os.getcwd())
    read_set = set()
    write_set = set()
    for l in trace_object:
        record = parse_line(l, ctx)
        if type(record) is RFile and record.fname != '/dev/tty':
            read_set.add(record.fname)
        elif type(record) is WFile and record.fname != '/dev/tty':
            write_set.add(record.fname)
    return read_set, write_set

def main(fname):
    ctx = Context()
    ctx.set_dir(os.getcwd())
    with open(fname) as f:
        for l in f:
            record = parse_line(l, ctx)
            if record:
                print(record)

if __name__ == '__main__':
    main(sys.argv[1])
