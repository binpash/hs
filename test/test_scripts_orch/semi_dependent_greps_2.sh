grep foo ./output_orch/in1 > ./output_orch/out1
grep bar ./output_orch/in2 > ./output_orch/out2
grep baz ./output_orch/in3 > ./output_orch/out2
grep baz ./output_orch/out2 > ./output_orch/out3
grep bar ./output_orch/out3 > ./output_orch/out4
grep baz ./output_orch/out3 > ./output_orch/out5
grep foo ./output_orch/out1 > ./output_orch/out2
grep foo ./output_orch/out2 > ./output_orch/out6