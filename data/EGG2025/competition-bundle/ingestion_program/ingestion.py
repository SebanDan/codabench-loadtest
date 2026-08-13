from braindecode.preprocessing import (
    create_fixed_length_windows,
    Preprocessor,
    preprocess,
    create_windows_from_events,
)
from braindecode.datasets.base import BaseConcatDataset
from eegdash import EEGChallengeDataset
import gzip

# from joblib import Parallel, delayed
import math
import mne
import numpy as np
import pandas as pd
from pathlib import Path
import pickle
from ingestion_helper import (
    DatasetWrapper,
    annotate_trials_with_target,
    add_aux_anchors,
    keep_only_recordings_with,
    add_extras_columns,
)
import sys
from sys import argv, stderr, exit
import torch
from torch.utils.data import SequentialSampler
from torch.utils.data import DataLoader
import gc


data_dir = Path("/app/data/")  # where the data are stored locally on the compute worker
output_dir = Path("/app/output/")  # where to store output files
program_dir = Path("/app/program")  # where this program is located
submission_dir = Path("/app/ingested_program")  # where the submission files are located
# submission is also in /app/output/submission.py

sys.path.append(str(program_dir))
sys.path.append(str(submission_dir))

# Suppress warnings for cleaner output
# import warnings
# warnings.filterwarnings("ignore")
# mne.set_log_level("CRITICAL")


SFREQ = 100
BATCH_SIZE = 512
EPOCH_LEN_S = 2.0

# Use GPU if available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_records(filename):
    """Load records from a compressed pickle file."""
    with gzip.open(filename, "rb") as f:
        return pickle.load(f)  # type: ignore


if __name__ == "__main__":
    if len(argv) != 1:
        print("Error! argument on command line:", argv)
        exit(1)

    #################################################################
    # Challenge 1
    # -----------

    # First load the model to make a quick check before starting
    # the lengthy dataloading process
    print("Loading model on warmup dataset for challenge 1", file=stderr)
    from submission import Submission  # type: ignore

    sub = Submission(SFREQ, DEVICE)
    model_1 = sub.get_model_challenge_1()
    model_1.eval()

    print("Loading warmup dataset for challenge 1", file=stderr)
    records = load_records(program_dir / "records_r5_ch1.pkl.gz")
    ch1 = EEGChallengeDataset(
        download=False,
        release="R5",
        query=dict(
            task="contrastChangeDetection",
        ),
        cache_dir=data_dir,  # type: ignore
        records=records,
    )
    ch1_desc = pd.read_pickle(Path(program_dir / "description_r5_ch1.pkl"))
    ch1.set_description(ch1_desc, overwrite=True)

    print("Preprocess dataset", file=stderr)
    preprocessors = [
        Preprocessor(
            annotate_trials_with_target,
            apply_on_array=False,
            target_field="rt_from_stimulus",
            epoch_length=EPOCH_LEN_S,
            require_stimulus=True,
            require_response=True,
        ),
        Preprocessor(add_aux_anchors, apply_on_array=False),
    ]
    # try save_dir to save time later
    preprocess(ch1, preprocessors, n_jobs=-1)

    # Create 2-second epochs from valid contrast trial starts only
    print("Create windows", file=stderr)
    # kept 2 seconds to ensure that dummy submission EEGNet output 1 value
    PRE_STIM = 0.00  # seconds before stimulus
    MAX_RT = 2.00  # cap the interval to cover responses up to this RT
    POST_RESP = 0.00  # tail after the response

    # Keep only recordings that actually contain stimulus anchors
    dbch1 = keep_only_recordings_with("stimulus_anchor", ch1)

    # Create single-interval windows (stim-locked, long enough to include the response)
    single_windows = create_windows_from_events(
        dbch1,
        mapping={"stimulus_anchor": 0},
        trial_start_offset_samples=int(-PRE_STIM * SFREQ),
        trial_stop_offset_samples=int((MAX_RT + POST_RESP) * SFREQ),
        preload=True,
    )

    # Bring extras (incl. target/RT/correct) into the window metadata
    single_windows = add_extras_columns(
        single_windows,
        dbch1,
        desc="stimulus_anchor",
        keys=(
            "target",
            "rt_from_stimulus",
            "rt_from_trialstart",
            "stimulus_onset",
            "response_onset",
            "correct",
            "response_type",
        ),
    )

    print("Wrap the data into a PyTorch-compatible dataset", file=stderr)
    test_loader_ch1 = DataLoader(
        single_windows,
        batch_size=BATCH_SIZE,
        sampler=SequentialSampler(single_windows),
        shuffle=False,
        drop_last=False,
        num_workers=8,
        pin_memory=True,
        persistent_workers=True
    )

    print("Evaluate model", file=stderr)
    
    y_preds, y_trues = [], []
    with torch.inference_mode():
        for batch in test_loader_ch1:
            X, y, infos = batch
            X = X.to(dtype=torch.float32, device=DEVICE, non_blocking=True)
            y = y.to(dtype=torch.float32, device=DEVICE, non_blocking=True)

            y_pred = model_1.forward(X)
            
            # Conserve sur GPU ou sous forme de liste plate
            y_preds.append(y_pred.reshape(-1))
            y_trues.append(y.reshape(-1))

    # Un seul rapatriement global vers le CPU à la fin !
    arr1_preds = torch.cat(y_preds).cpu().numpy()
    arr1_trues = torch.cat(y_trues).cpu().numpy()
    #arr1_preds, arr1_trues = np.array(y_preds), np.squeeze(np.array(y_trues))

    print("Free memory", file=stderr)
    del model_1
    del test_loader_ch1
    del single_windows
    del dbch1
    del ch1
    gc.collect()

    #################################################################
    # Challenge 2
    # -----------
    # Load model for an early error detection
    print("Loading model on warmup dataset for challenge 2", file=stderr)
    from submission import Submission  # type: ignore

    sub = Submission(SFREQ, DEVICE)
    model_2 = sub.get_model_challenge_2()
    model_2.eval()

    print("Loading warmup dataset for challenge 2", file=stderr)
    records = load_records(program_dir / "records_r5_ch2.pkl.gz")
    ch2 = EEGChallengeDataset(
        download=False,
        release="R5",
        query=dict(
            task="RestingState",
        ),
        description_fields=[
            "subject",
            "session",
            "run",
            "task",
            "age",
            "gender",
            "sex",
            "p_factor",
        ],
        cache_dir=data_dir,  # type: ignore
        records=records,
    )
    ch2_desc = pd.read_pickle(program_dir / "description_r5_ch2.pkl")
    ch2.set_description(ch2_desc, overwrite=True)

    print("Preprocess dataset", file=stderr)
    bdch2 = BaseConcatDataset(
        [
            ds
            for ds in ch2.datasets
            if ds.raw.n_times >= 4 * SFREQ and not math.isnan(ds.description["p_factor"])  # type: ignore
        ]
    )
    print("Create windows", file=stderr)
    windows_ds = create_fixed_length_windows(
        bdch2,
        window_size_samples=4 * SFREQ,
        window_stride_samples=2 * SFREQ,
        drop_last_window=True,
    )
    windows_ds = BaseConcatDataset(
        [DatasetWrapper(ds, crop_size_samples=2 * SFREQ) for ds in windows_ds.datasets]  # type: ignore
    )

    print("Wrap the data into a PyTorch-compatible dataset", file=stderr)
    test_loader_ch2 = DataLoader(
        windows_ds,
        batch_size=BATCH_SIZE,
        num_workers=8,
        sampler=SequentialSampler(windows_ds),
        shuffle=False,
        drop_last=False,
        pin_memory=True,
        persistent_workers=True
    )

    print("Evaluate model", file=stderr)
    y_preds, y_trues = [], []
    with torch.inference_mode():
        for batch in test_loader_ch2:
            X, y, crop_inds, infos = batch
            X = X.to(dtype=torch.float32, device=DEVICE, non_blocking=True)
            y = y.to(dtype=torch.float32, device=DEVICE, non_blocking=True)

            # Forward pass
            y_pred = model_2.forward(X)
            
            y_preds.append(y_pred.reshape(-1).cpu().numpy())
            y_trues.append(y.reshape(-1).cpu().numpy())

    arr2_preds = np.concatenate(y_preds)
    arr2_trues = np.concatenate(y_trues)

    print("Free memory", file=stderr)
    del model_2
    del test_loader_ch2
    del windows_ds
    del bdch2
    del ch2
    gc.collect()

    output_predictions = {
        "arr1_preds": arr1_preds,
        "arr1_trues": arr1_trues,
        "arr2_preds": arr2_preds,
        "arr2_trues": arr2_trues,
    }
    # print(output_predictions, file=stderr)

    with gzip.open(output_dir / "predictions.pkz", "wb") as preds_file:
        pickle.dump(output_predictions, preds_file, protocol=pickle.HIGHEST_PROTOCOL)
        # preds_file.write(json.dumps(output_predictions).encode("utf-8"))
    print("Checking existing files in /app/output", file=stderr)
    p = Path("/app/output").glob("**/*")
    for file in p:
        print(file, file=stderr)
