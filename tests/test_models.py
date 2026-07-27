from pathlib import Path

import pytest

from codabench_loadtest.models import CompetitionPool, CompetitionZip

DATA_DIR = Path(__file__).resolve().parent / "data"


def test_competition_pool_from_dir_success():
    competition_pool = CompetitionPool.from_dir(DATA_DIR)

    assert len(competition_pool.competitions) == 2


def test_competition_zip_from_dir_success():
    competition_dir = DATA_DIR / "IRIS"
    competition_zip = CompetitionZip.from_dir(competition_dir)

    assert competition_zip.name == "IRIS-bundle"
    assert len(competition_zip.submission_pool.submissions) == 1


def test_competition_zip_get_random_submission_zip_success():
    competition_dir = DATA_DIR / "IRIS"
    competition_zip = CompetitionZip.from_dir(competition_dir)

    submission_zip = competition_zip.get_random_submission_zip()

    assert submission_zip.zip_name == "classical_code_submission.zip"


@pytest.mark.parametrize(
    "competition_filter, expected_count, expected_names",
    [
        (["IRIS"], 1, ["IRIS-bundle"]),
        (["IRIS", "MNIST"], 2, ["IRIS-bundle", "MNIST-bundle"]),
        (["NonExistentCompetition"], 0, []),
        (
            [],
            2,
            ["IRIS-bundle", "MNIST-bundle"],
        ),  # No filter should return all competitions
        (
            None,
            2,
            ["IRIS-bundle", "MNIST-bundle"],
        ),  # None filter should return all competitions
    ],
)
def test_competition_filtering(competition_filter, expected_count, expected_names):
    competition_pool = CompetitionPool.from_dir(
        DATA_DIR, competition_filter=competition_filter
    )

    assert len(competition_pool.competitions) == expected_count
    actual_names = [
        comp.name
        for comp in competition_pool.competitions
        if comp.name in expected_names
    ]
    assert len(actual_names) == expected_count
