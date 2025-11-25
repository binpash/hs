import os
import time
import subprocess

data_dir = "data/kaggle-captk-brats-preprocessing"
output_dir = "output/kaggle-captk-brats-preprocessing"

# Inlined from train_labels.csv - first 100 entries
train_brats_ids = [
    "00000",
    "00002",
    "00003",
    "00005",
    "00006",
    "00008",
    "00009",
    "00011",
    "00012",
    "00014",
    "00017",
    "00018",
    "00019",
    "00020",
    "00021",
    "00022",
    "00024",
    "00025",
    "00026",
    "00028",
    "00030",
    "00031",
    "00032",
    "00033",
    "00035",
    "00036",
    "00043",
    "00044",
    "00045",
    "00046",
    "00048",
    "00049",
    "00052",
    "00053",
    "00054",
    "00056",
    "00058",
    "00059",
    "00060",
    "00061",
    "00062",
    "00063",
    "00064",
    "00066",
    "00068",
    "00070",
    "00071",
    "00072",
    "00074",
    "00077",
    "00078",
    "00081",
    "00084",
    "00085",
    "00087",
    "00088",
    "00089",
    "00090",
    "00094",
    "00095",
    "00096",
    "00097",
    "00098",
    "00099",
    "00100",
    "00102",
    "00104",
    "00105",
    "00106",
    "00107",
    "00108",
    "00109",
    "00110",
    "00111",
    "00112",
    "00113",
    "00116",
    "00117",
    "00120",
    "00121",
    "00122",
    "00123",
    "00124",
    "00128",
    "00130",
    "00132",
    "00133",
    "00134",
    "00136",
    "00137",
    "00138",
    "00139",
    "00140",
    "00142",
    "00143",
    "00144",
    "00146",
    "00147",
    "00148",
    "00149",
]


t = time.time()


print("\n\n\n... STARTING TRAIN IMAGES ...\n\n\n")
for brats_id in train_brats_ids:
    t1 = time.time()
    print(f"\n... STARTING TO PREPROCESS BRATSID={brats_id} ...\n")

    # Setup paths
    modality_base_dir = os.path.join(data_dir, "train", brats_id)
    output_base_dir = os.path.join(output_dir, "train", brats_id)
    modality_file_map = {
        m: os.path.join(
            modality_base_dir,
            m,
            sorted(
                os.listdir(os.path.join(modality_base_dir, m)),
                key=lambda x: int(x.rsplit("-", 1)[1].split(".", 1)[0]),
            )[0],
        )
        for m in ["T1wCE", "T1w", "T2w", "FLAIR"]
    }

    subprocess.run(["mkdir", "-p", output_base_dir])

    os.environ["LD_LIBRARY_PATH"] = os.path.join(data_dir, "./squashfs-root/usr/lib")
    subprocess.run(
        [
            os.path.join(
                data_dir, "./squashfs-root/usr/bin/BraTSPipeline"
            ),  # Path to the CaPTk executable file
            "-t1c",
            modality_file_map[
                "T1wCE"
            ],  # Input structural T1-weighted post-contrast image
            "-t1",
            modality_file_map["T1w"],  # Input structural T1-weighted pre-contrast image
            "-t2",
            modality_file_map["T2w"],  # Input structural T2-weighted contrast image
            "-fl",
            modality_file_map["FLAIR"],  # Input structural FLAIR contrast image
            "-o",
            output_base_dir,  # Output directory for final output
            "-s",
            "0",  # Flag whether to skull strip or not (0=NO, 1=YES)
            "-b",
            "0",  # Flag whether to segment brain tumors or no (0=NO, 1=YES)
            "-i",
            "0",  # Flag whether to save intermediate files (0=NO, 1=YES)
            "-d",
            "0",  # Flag whether to print debugging information (0=NO, 1=YES)
        ],
        check=True,
    )
    os.environ["LD_LIBRARY_PATH"] = ""
    print(
        f"\n... IT TOOK {time.time() - t1:.3f} SECONDS TO COMPLETE BRATSID={brats_id}...\n"
    )


print(
    f"\n\n\n\n\nTIME TO FINISH 100 PATIENTS IS :   {time.time() - t:.4f} ...\n\n\n\n\n"
)
