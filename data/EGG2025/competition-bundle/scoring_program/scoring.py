from competition_metrics import score_challenge1, score_challenge2, score_overall
import gzip
import json
import numpy as np
from pathlib import Path
import pickle
from sys import argv, stderr, exit


# data_dir = Path("/app/data/")
prediction_dir = Path("/app/input/res")
score_dir = Path("/app/output/")
# It seems that submission program is in /app/input/res
# sys.path.append(str(subm_dir))

if __name__ == "__main__":
    if len(argv) != 1:
        print("Error! argument on command line:", argv)
        exit(1)

    with gzip.open(prediction_dir / "predictions.pkz", "rb") as f:
        data = pickle.load(f)

    arr1_preds = data["arr1_preds"]
    arr1_trues = data["arr1_trues"]
    arr2_preds = data["arr2_preds"]
    arr2_trues = data["arr2_trues"]

    score1 = score_challenge1(arr1_trues, arr1_preds)
    score2 = score_challenge2(arr2_trues, arr2_preds)

    if not np.isfinite(score1):
        raise ValueError("Challenge 1 score is not finite")
    if not np.isfinite(score2):
        raise ValueError("Challenge 2 score is not finite")
    overall = score_overall(score1, score2)
    if not np.isfinite(overall):
        raise ValueError("Overall score is not finite")

    scores = {
        "overall": np.round(overall, 5).item(),
        "challenge1": np.round(score1, 5).item(),
        "challenge2": np.round(score2, 5).item(),
    }

    with open(score_dir / "scores.json", "w") as score_file:
        score_file.write(json.dumps(scores))
