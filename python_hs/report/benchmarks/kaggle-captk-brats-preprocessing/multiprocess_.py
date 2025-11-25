"""
Multiprocess version of CaPTk BraTS preprocessing.

Corresponds to benchmark.py but uses multiprocessing.Process instead of
subprocess.run for the main BraTSPipeline calls. Each patient is processed
in a separate process via multiprocessing.
"""

import multiprocessing
import os
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


def run_captk(brats_id):
    """Run BraTSPipeline for a single patient."""
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
    env = os.environ.copy()
    os.environ["LD_LIBRARY_PATH"] = os.path.join(data_dir, "./squashfs-root/usr/lib")
    subprocess.run(
        [
            os.path.join(data_dir, "./squashfs-root/usr/bin/BraTSPipeline"),
            "-t1c",
            modality_file_map["T1wCE"],
            "-t1",
            modality_file_map["T1w"],
            "-t2",
            modality_file_map["T2w"],
            "-fl",
            modality_file_map["FLAIR"],
            "-o",
            output_base_dir,
            "-s",
            "0",
            "-b",
            "0",
            "-i",
            "0",
            "-d",
            "0",
        ],
        check=True,
        env=env,
    )


if __name__ == "__main__":
    for b_id in train_brats_ids:
        kwargs = dict(brats_id=b_id)
        p = multiprocessing.Process(target=run_captk, kwargs=kwargs)
        p.start()
        p.join()
