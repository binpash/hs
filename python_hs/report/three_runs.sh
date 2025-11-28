mkdir -p grand_three_runs/

# echo "Nemo Started!"
# bash nemo.sh &> grand_three_runs/nemo_log
# echo "Nemo Done!"

echo "Biostars Started!"
bash biostars.sh &> grand_three_runs/biostars_log
echo "Biostars Done!"

echo "Bioinfo Started!"
bash bioinfo.sh &> grand_three_runs/bioinfo_log
echo "Bioinfo Done!"

# TODO: Bioinfo after
# TODO: Rainbowcake after
# TODO: Captk if time.
