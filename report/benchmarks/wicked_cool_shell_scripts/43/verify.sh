grep -q "Your environment checks out fine." result_sh_out || echo "sh fail" > result_error
grep -q "Your environment checks out fine." result_hs_out || echo "hs fail" >> result_error
