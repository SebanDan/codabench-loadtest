from braindecode.datasets.base import EEGWindowsDataset, BaseDataset
from braindecode.datasets import BaseConcatDataset
import mne
from mne_bids import get_bids_path_from_fname
import numpy as np
import pandas as pd
import random


class DatasetWrapper(BaseDataset):
    def __init__(self, dataset: EEGWindowsDataset, crop_size_samples: int, seed=None):
        self.dataset = dataset
        self.crop_size_samples = crop_size_samples
        self.rng = random.Random(seed)

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):  # pyright: ignore[reportIncompatibleMethodOverride]
        X, _, crop_inds = self.dataset[index]

        # P-factor label:
        p_factor = self.dataset.description["p_factor"]
        p_factor = float(p_factor)

        # Addtional information:
        infos = {
            "subject": self.dataset.description["subject"],
            "sex": self.dataset.description["sex"],
            "age": float(self.dataset.description["age"]),
            "task": self.dataset.description["task"],
            "session": self.dataset.description.get("session", None) or "",
            "run": self.dataset.description.get("run", None) or "",
        }

        # Randomly crop the signal to the desired length:
        i_window_in_trial, i_start, i_stop = crop_inds
        assert i_stop - i_start >= self.crop_size_samples, f"{i_stop=} {i_start=}"
        start_offset = self.rng.randint(0, i_stop - i_start - self.crop_size_samples)
        i_start = i_start + start_offset
        i_stop = i_start + self.crop_size_samples
        X = X[:, start_offset : start_offset + self.crop_size_samples]  # type: ignore

        return X, p_factor, (i_window_in_trial, i_start, i_stop), infos


def build_trial_table(events_df: pd.DataFrame) -> pd.DataFrame:
    """One row per contrast trial with stimulus/response metrics."""
    events_df = events_df.copy()
    events_df["onset"] = pd.to_numeric(events_df["onset"], errors="raise")
    events_df = events_df.sort_values("onset", kind="mergesort").reset_index(drop=True)

    trials = events_df[events_df["value"].eq("contrastTrial_start")].copy()
    stimuli = events_df[events_df["value"].isin(["left_target", "right_target"])].copy()
    responses = events_df[
        events_df["value"].isin(["left_buttonPress", "right_buttonPress"])
    ].copy()

    trials = trials.reset_index(drop=True)
    trials["next_onset"] = trials["onset"].shift(-1)
    trials = trials.dropna(subset=["next_onset"]).reset_index(drop=True)

    # Extract sorted arrays for efficient O(log n) searching
    stim_onsets_arr = stimuli["onset"].values
    resp_onsets_arr = responses["onset"].values
    resp_types_arr = responses["value"].values
    resp_feedback_arr = responses["feedback"].values
    trial_onsets_arr = trials["onset"].values
    trial_ends_arr = trials["next_onset"].values

    # Stimuli onsets: searchsorted O(log n) per trial
    stim_onsets = np.full(len(trials), np.nan)
    for i, (start, end) in enumerate(zip(trial_onsets_arr, trial_ends_arr)):
        j = np.searchsorted(stim_onsets_arr, start, side="left")
        if j < len(stim_onsets_arr) and stim_onsets_arr[j] < end:
            stim_onsets[i] = stim_onsets_arr[j]

    # Responses: searchsorted with conditional logic
    resp_onsets = np.full(len(trials), np.nan)
    resp_types = np.full(len(trials), None, dtype=object)
    resp_feedback = np.full(len(trials), None, dtype=object)
    
    for i, (start, end, stim_t) in enumerate(
        zip(trial_onsets_arr, trial_ends_arr, stim_onsets)
    ):
        search_start = stim_t if not np.isnan(stim_t) else start
        j = np.searchsorted(resp_onsets_arr, search_start, side="left")
        if j < len(resp_onsets_arr) and resp_onsets_arr[j] < end:
            resp_onsets[i] = resp_onsets_arr[j]
            resp_types[i] = resp_types_arr[j]
            resp_feedback[i] = resp_feedback_arr[j]

    # Compute RTs vectorized with np.where
    rt_from_stim = np.where(
        np.isnan(stim_onsets) | np.isnan(resp_onsets),
        np.nan,
        resp_onsets - stim_onsets,
    )
    rt_from_trial = np.where(
        np.isnan(resp_onsets), np.nan, resp_onsets - trials["onset"].values
    )

    # Map feedback to correct (vectorized boolean indexing)
    correct = np.full(len(trials), None, dtype=object)
    smiley = resp_feedback == "smiley_face"
    sad = resp_feedback == "sad_face"
    correct[smiley] = True
    correct[sad] = False

    return pd.DataFrame({
        "trial_start_onset": trial_onsets_arr,
        "trial_stop_onset": trial_ends_arr,
        "stimulus_onset": stim_onsets,
        "response_onset": resp_onsets,
        "rt_from_stimulus": rt_from_stim,
        "rt_from_trialstart": rt_from_trial,
        "response_type": resp_types,
        "correct": correct,
    })


def _to_float_or_none(x):
    return None if pd.isna(x) else float(x)


def _to_int_or_none(x):
    return None if pd.isna(x) else int(x)


def _to_str_or_none(x):
    return None if (x is None or (isinstance(x, float) and np.isnan(x))) else str(x)


def annotate_trials_with_target(
    raw,
    target_field="rt_from_stimulus",
    epoch_length=2.0,
    require_stimulus=True,
    require_response=True,
):
    """Create 'contrast_trial_start' annotations with float target in extras."""
    fnames = raw.filenames
    assert len(fnames) == 1, "Expected a single filename"
    bids_path = get_bids_path_from_fname(fnames[0])
    events_file = bids_path.update(suffix="events", extension=".tsv").fpath

    events_df = (
        pd.read_csv(events_file, sep="\t")
        .assign(onset=lambda d: pd.to_numeric(d["onset"], errors="raise"))
        .sort_values("onset", kind="mergesort")
        .reset_index(drop=True)
    )

    trials = build_trial_table(events_df)

    if require_stimulus:
        trials = trials[trials["stimulus_onset"].notna()].copy()
    if require_response:
        trials = trials[trials["response_onset"].notna()].copy()

    if target_field not in trials.columns:
        raise KeyError(f"{target_field} not in computed trial table.")

    onsets = trials["trial_start_onset"].to_numpy(float)
    durations = np.full(len(trials), float(epoch_length), dtype=float)
    descs = ["contrast_trial_start"] * len(trials)

    # Extract columns as arrays for vectorized access
    target_vals = trials[target_field].values
    rt_stim_vals = trials["rt_from_stimulus"].values
    rt_trial_vals = trials["rt_from_trialstart"].values
    stim_onset_vals = trials["stimulus_onset"].values
    resp_onset_vals = trials["response_onset"].values
    correct_vals = trials["correct"].values
    resp_type_vals = trials["response_type"].values

    # Build extras with list comprehension (faster than apply)
    extras = [
        {
            "target": _to_float_or_none(target_vals[i]),
            "rt_from_stimulus": _to_float_or_none(rt_stim_vals[i]),
            "rt_from_trialstart": _to_float_or_none(rt_trial_vals[i]),
            "stimulus_onset": _to_float_or_none(stim_onset_vals[i]),
            "response_onset": _to_float_or_none(resp_onset_vals[i]),
            "correct": _to_int_or_none(correct_vals[i]),
            "response_type": _to_str_or_none(resp_type_vals[i]),
        }
        for i in range(len(trials))
    ]
    new_ann = mne.Annotations(
        onset=onsets,
        duration=durations,
        description=descs,
        orig_time=raw.info["meas_date"],
        extras=extras,
    )
    raw.set_annotations(new_ann)
    return raw


def add_aux_anchors(raw, stim_desc="stimulus_anchor", resp_desc="response_anchor"):
    ann = raw.annotations
    mask = ann.description == "contrast_trial_start"
    if not np.any(mask):
        return raw

    stim_onsets, resp_onsets = [], []
    stim_extras, resp_extras = [], []

    for idx in np.where(mask)[0]:
        ex = ann.extras[idx] if ann.extras is not None else {}
        t0 = float(ann.onset[idx])

        stim_t = ex["stimulus_onset"]
        resp_t = ex["response_onset"]

        if stim_t is None or (isinstance(stim_t, float) and np.isnan(stim_t)):
            rtt = ex["rt_from_trialstart"]
            rts = ex["rt_from_stimulus"]
            if rtt is not None and rts is not None:
                stim_t = t0 + float(rtt) - float(rts)

        if resp_t is None or (isinstance(resp_t, float) and np.isnan(resp_t)):
            rtt = ex["rt_from_trialstart"]
            if rtt is not None:
                resp_t = t0 + float(rtt)

        if (stim_t is not None) and not (isinstance(stim_t, float) and np.isnan(stim_t)):
            stim_onsets.append(float(stim_t))
            stim_extras.append(dict(ex, anchor="stimulus"))
        if (resp_t is not None) and not (isinstance(resp_t, float) and np.isnan(resp_t)):
            resp_onsets.append(float(resp_t))
            resp_extras.append(dict(ex, anchor="response"))

    new_onsets = np.array(stim_onsets + resp_onsets, dtype=float)
    if len(new_onsets):
        aux = mne.Annotations(
            onset=new_onsets,
            duration=np.zeros_like(new_onsets, dtype=float),
            description=[stim_desc] * len(stim_onsets) + [resp_desc] * len(resp_onsets),
            orig_time=raw.info["meas_date"],
            extras=stim_extras + resp_extras,
        )
        raw.set_annotations(ann + aux)
    return raw


def add_extras_columns(
    windows_concat_ds,
    original_concat_ds,
    desc="contrast_trial_start",
    keys=(
        "target",
        "rt_from_stimulus",
        "rt_from_trialstart",
        "stimulus_onset",
        "response_onset",
        "correct",
        "response_type",
    ),
):
    float_cols = {
        "target",
        "rt_from_stimulus",
        "rt_from_trialstart",
        "stimulus_onset",
        "response_onset",
    }

    for win_ds, base_ds in zip(windows_concat_ds.datasets, original_concat_ds.datasets):
        ann = base_ds.raw.annotations
        idx = np.where(ann.description == desc)[0]
        if idx.size == 0:
            continue

        per_trial = [
            {
                k: (
                    ann.extras[i][k]
                    if ann.extras is not None and k in ann.extras[i]
                    else None
                )
                for k in keys
            }
            for i in idx
        ]

        md = win_ds.metadata.copy()
        first = md["i_window_in_trial"].to_numpy() == 0
        trial_ids = first.cumsum() - 1
        n_trials = trial_ids.max() + 1 if len(trial_ids) else 0
        assert n_trials == len(
            per_trial
        ), f"Trial mismatch: {n_trials} vs {len(per_trial)}"

        for k in keys:
            vals = [per_trial[t][k] if t < len(per_trial) else None for t in trial_ids]
            if k == "correct":
                ser = pd.Series(
                    [None if v is None else int(bool(v)) for v in vals],
                    index=md.index,
                    dtype="Int64",
                )
            elif k in float_cols:
                ser = pd.Series(
                    [np.nan if v is None else float(v) for v in vals],
                    index=md.index,
                    dtype="Float64",
                )
            else:  # response_type
                ser = pd.Series(vals, index=md.index, dtype="string")

            # Replace the whole column to avoid dtype conflicts
            md[k] = ser

        win_ds.metadata = md.reset_index(drop=True)
        if hasattr(win_ds, "y"):
            y_np = win_ds.metadata["target"].astype(float).to_numpy()
            win_ds.y = y_np[:, None]  # (N, 1)

    return windows_concat_ds


def keep_only_recordings_with(desc, concat_ds):
    kept = []
    for ds in concat_ds.datasets:
        if np.any(ds.raw.annotations.description == desc):
            kept.append(ds)
        else:
            print(
                f"[warn] Recording {ds.raw.filenames[0]} does not contain event '{desc}'"
            )
    return BaseConcatDataset(kept)
