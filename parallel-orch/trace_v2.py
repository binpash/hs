import re
import os.path
import sys
from dataclasses import dataclass

# Global TODOs:
# handle pwd, such that open and stat can work

def parse_info(l):
    return 0

@dataclass
class RFile:
    fname: str

@dataclass
class WFile:
    fname: str

# openat
r_first_path_set = set(['execve', 'stat', 'lstat', 'access', 'statfs'])
w_first_path_set = set(['mkdir'])
r_fd_path_set = set(['fstatat', 'newfstatat'])
w_fd_path_set = set(['unlinkat'])
ignore_set = set(['getpid'])

def parse_string(s):
    s = s.strip()
    assert s[0] == '"' and s[-1] == '"'
    return bytes(s[1:-1], "utf-8").decode("unicode_escape")

def between(s, d1, d2):
    return s.find(d1) + len(d1), s.rfind(d2)

def get_path_first_path(args):
    a, _ = args.split(sep=',', maxsplit=1)
    return parse_string(a)

def parse_r_first_path(args, ret):
    return RFile(get_path_first_path(args))

def parse_w_first_path(args, ret):
    path = get_path_first_path(args)    
    if is_ret_enoent(ret):
        return RFile(path)
    else:
        return WFile(path)

def is_open_flag(flags):
    if 'O_RDONLY' in flags:
        return 'r'
    else:
        return 'w'

def is_absolute(path):
    return path[0] == '/'

def is_ret_enoent(ret):
    return 'ENOENT' in ret

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
    if is_open_flag(flags) == 'r':
        return RFile(total_path)
    if is_ret_enoent(ret):
        return RFile(total_path)
    return WFile(total_path)

def parse_chdir(args, ret):
    return None

def get_path_from_fd_path(args):
    a0, a1, _ = args.split(sep=',', maxsplit=2)
    a1 = parse_string(a1)
    if a1[0] == '/':
        return a1
    else:
        begin, end = between(a0, '<', '>')
        a0 = a0[begin:end]
        return os.path.join(a0, a1)

def parse_r_fd_path(args, ret):
    return RFile(get_path_from_fd_path(args))

def parse_w_fd_path(args, ret):
    if is_ret_enoent(ret):
        return RFile(get_path_from_fd_path(args))
    else:
        return WFile(get_path_from_fd_path(args))
    
def parse_syscall(syscall, args, ret):
    if syscall in r_first_path_set:
        return parse_r_first_path(args, ret)
    elif syscall in w_first_path_set:
        return parse_w_first_path(args, ret)
    elif syscall == 'openat':
        return parse_openat(args, ret)
    elif syscall == 'chdir':
        return parse_chdir(args, ret)
    elif syscall in r_fd_path_set:
        return parse_r_fd_path(args, ret)
    elif syscall in w_fd_path_set:
        return parse_w_fd_path(args, ret)
    elif syscall in ignore_set:
        return None
    else:
        raise ValueError('Unclassified syscall ' + syscall)

def strip_prefix(l):
    if l[0].isdigit():
        return l.split(' ', maxsplit=1)[1]
    else:
        return l

def handle_info(l):
    if '+++' in l:
        return True, parse_info(l)
    elif '---' in l:
        return True, None
    else:
        return False, None
        
def parse_line(l):
    is_info, info = handle_info(l)
    if is_info:
        return info
    if not len(l):
        return None
    l = strip_prefix(l)
    lparen = l.find('(')
    rparen = l.rfind(')')
    equals = l.rfind('=')
    syscall = l[:lparen]
    args = l[lparen+1:rparen]
    ret = l[equals+1]
    return parse_syscall(syscall, args, ret)

    
def main(fname):
    with open(fname) as f:
        s = f.read()
    for l in s.split('\n'):
        print(parse_line(l))

debug_g = r'''
start: ESCAPED_STRING

%import common.ESCAPED_STRING
'''
if __name__ == '__main__':
    # parser = lark.Lark(debug_g)
    # parser.parse('"lskjkf"')
    main(sys.argv[1])
