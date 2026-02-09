all: fd_util set-diff

fd_util: fd_util.c
	gcc -Wall -O3 -DNDEBUG fd_util.c -o fd_util

set-diff: set-diff.c
	gcc -Wall -O3 -DNDEBUG set-diff.c -o set-diff

clean:
	rm -f fd_util set-diff
