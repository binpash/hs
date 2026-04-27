from ctypes import *


class word_desc(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n131
    """

    _fields_ = [("word", c_char_p), ("flags", c_int)]


class REDIRECTEE(Union):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n154
    """

    _fields_ = [("dest", c_int), ("filename", POINTER(word_desc))]


class redirect(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n161
    """


# we do this because we need to reference redirect in redirect
redirect._fields_ = [
    ("next", POINTER(redirect)),
    ("redirector", REDIRECTEE),
    ("rflags", c_int),
    ("flags", c_int),
    ("instruction", c_int),
    ("redirectee", REDIRECTEE),
    ("here_doc_eof", c_char_p),
]


class word_list(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n137
    """


# we do this because we need to reference word_list in word_list
word_list._fields_ = [("next", POINTER(word_list)), ("word", POINTER(word_desc))]


class for_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n259
    """


class pattern_list(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n243
    """


class case_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n251
    """

    _fields_ = [
        ("flags", c_int),
        ("line", c_int),
        ("word", POINTER(word_desc)),
        ("clauses", POINTER(pattern_list)),
    ]


class while_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n302
    """


class if_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n294
    """


class connection(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n229
    """


class function_def(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n346
    """


class group_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n356
    """


class select_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n282
    """


class arith_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n364
    """

    _fields_ = [("flags", c_int), ("line", c_int), ("exp", POINTER(word_list))]


class cond_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n328
    """


# we do this because we need to reference cond_com in cond_com
cond_com._fields_ = [
    ("flags", c_int),
    ("line", c_int),
    ("type", c_int),
    ("op", POINTER(word_desc)),
    ("left", POINTER(cond_com)),
    ("right", POINTER(cond_com)),
]


class arith_for_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n270
    """


class subshell_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n361
    """


class coproc_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n382
    """


class simple_com(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n337
    """

    _fields_ = [
        ("flags", c_int),
        ("line", c_int),
        ("words", POINTER(word_list)),
        ("redirects", POINTER(redirect)),
    ]


class value(Union):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n202
    """

    _fields_ = [
        ("For", POINTER(for_com)),
        ("Case", POINTER(case_com)),
        ("While", POINTER(while_com)),
        ("If", POINTER(if_com)),
        ("Connection", POINTER(connection)),
        ("Simple", POINTER(simple_com)),
        ("Function_def", POINTER(function_def)),
        ("Group", POINTER(group_com)),
        ("Select", POINTER(select_com)),
        ("Arith", POINTER(arith_com)),
        ("Cond", POINTER(cond_com)),
        ("ArithFor", POINTER(arith_for_com)),
        ("Subshell", POINTER(subshell_com)),
        ("Coproc", POINTER(coproc_com)),
    ]


class command(Structure):
    """
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h#n197
    """

    _fields_ = [
        ("type", c_int),
        ("flags", c_int),
        ("line", c_int),
        ("redirects", POINTER(redirect)),
        ("value", value),
    ]


# we do this because we need to reference command in for_com
for_com._fields_ = [
    ("flags", c_int),
    ("line", c_int),
    ("name", POINTER(word_desc)),
    ("map_list", POINTER(word_list)),
    ("action", POINTER(command)),
]

# we do this because we need to reference pattern_list and command in pattern_list
pattern_list._fields_ = [
    ("next", POINTER(pattern_list)),
    ("patterns", POINTER(word_list)),
    ("action", POINTER(command)),
    ("flags", c_int),
]

# we do this because we need to reference command in while_com
while_com._fields_ = [
    ("flags", c_int),
    ("test", POINTER(command)),
    ("action", POINTER(command)),
]

# we do this because we need to reference command in if_com
if_com._fields_ = [
    ("flags", c_int),
    ("test", POINTER(command)),
    ("true_case", POINTER(command)),
    ("false_case", POINTER(command)),
]

# we do this because we need to reference command in connection
connection._fields_ = [
    ("ignore", c_int),
    ("first", POINTER(command)),
    ("second", POINTER(command)),
    ("connector", c_int),
]


# we do this because we need to reference command in group_com
group_com._fields_ = [("ignore", c_int), ("command", POINTER(command))]

# we do this because we need to reference command in function_def
function_def._fields_ = [
    ("flags", c_int),
    ("line", c_int),
    ("name", POINTER(word_desc)),
    ("command", POINTER(command)),
    ("source_file", c_char_p),
]

# we do this because we need to reference command in select_com
select_com._fields_ = [
    ("flags", c_int),
    ("line", c_int),
    ("name", POINTER(word_desc)),
    ("map_list", POINTER(word_list)),
    ("action", POINTER(command)),
]

# we do this because we need to reference command in arith_for_com
arith_for_com._fields_ = [
    ("flags", c_int),
    ("line", c_int),
    ("init", POINTER(word_list)),
    ("test", POINTER(word_list)),
    ("step", POINTER(word_list)),
    ("action", POINTER(command)),
]

# we do this because we need to reference command in subshell_com
subshell_com._fields_ = [
    ("flags", c_int),
    ("line", c_int),
    ("command", POINTER(command)),
]

# we do this because we need to reference command in coproc_com
coproc_com._fields_ = [
    ("flags", c_int),
    ("name", c_char_p),
    ("command", POINTER(command)),
]
