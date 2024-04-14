fail=;
if (target_option=k; case ${target_option-} in ?) ;; *) echo "am__make_running_with_option: internal error: invalid" "target option '${target_option-}' specified" >&2; exit 1;; esac; has_opt=no; sane_makeflags=$MAKEFLAGS; if { if test -z '0'; then false; elif test -n 'x86_64-pc-linux-gnu'; then true; elif test -n '4.3' && test -n '/checkout'; then true; else false; fi; }; then sane_makeflags=$MFLAGS; else case $MAKEFLAGS in *\\[\ \	]*) bs=\\; sane_makeflags=`printf '%s\n' "$MAKEFLAGS" | sed "s/$bs$bs[$bs $bs	]*//g"`;; esac; fi; skip_next=no; strip_trailopt () { flg=`printf '%s\n' "$flg" | sed "s/$1.*$//"`; }; for flg in $sane_makeflags; do test $skip_next = yes && { skip_next=no; continue; }; case $flg in *=*|--*) continue;; -*I) strip_trailopt 'I'; skip_next=yes;; -*I?*) strip_trailopt 'I';; -*O) strip_trailopt 'O'; skip_next=yes;; -*O?*) strip_trailopt 'O';; -*l) strip_trailopt 'l'; skip_next=yes;; -*l?*) strip_trailopt 'l';; -[dEDm]) skip_next=yes;; -[JT]) skip_next=yes;; esac; case $flg in *$target_option*) has_opt=yes; break;; esac; done; test $has_opt = yes); then \
  failcom='fail=yes';
else
  failcom='exit 1';
fi;
dot_seen=no;
target=`echo all-recursive | sed s/-recursive//`;
case "all-recursive" in
  distclean-* | maintainer-clean-*) list='lib po doc' ;;
  *) list='lib po doc' ;;
esac;
for subdir in $list; do
  echo "Making $target in $subdir";
  if test "$subdir" = "."; then
    dot_seen=yes;
    local_target="$target-am";
  else
    local_target="$target";
  fi;
  (CDPATH="${ZSH_VERSION+.}:" && cd $subdir && make $local_target) \
  || eval $failcom;
done;
if test "$dot_seen" = "no"; then
  make  "$target-am" || exit 1;
fi; test -z "$fail"