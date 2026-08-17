import zipfile

import pytest

from codabench_loadtest.models import CompetitionPool, CompetitionZip
from tests.conftest import DATA_DIR, IRIS


def test_competition_pool_from_dir_success():
    competition_pool = CompetitionPool.from_dir(DATA_DIR)

    assert len(competition_pool.competitions) == 2


def test_competition_zip_from_dir_success():
    competition_zip = CompetitionZip.from_dir(IRIS)

    assert competition_zip.name == "IRIS-bundle"
    assert len(competition_zip.submission_pool.submissions) == 1


def test_competition_zip_get_random_submission_zip_success():
    competition_zip = CompetitionZip.from_dir(IRIS)

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


@pytest.mark.parametrize(
    "competition_id, phase_id, expected_phase_id",
    [
        (1, 2, 2),
        (None, 2, 2),
        (1, None, 1),
        (None, None, ValueError),
    ],
)
def test_competition_properties(competition_id, phase_id, expected_phase_id):
    competition_zip = CompetitionZip.from_dir(IRIS)
    competition_zip.id = competition_id
    competition_zip.phase_id = phase_id

    if isinstance(expected_phase_id, type) and issubclass(expected_phase_id, Exception):
        with pytest.raises(expected_phase_id, match="Competition phase ID is not set"):
            competition_zip.get_phase_id()
    else:
        assert competition_zip.get_phase_id() == expected_phase_id


def test_competition_zip_from_dir_raises_when_no_zip(
    competition_missing_competition_zip,
):
    with pytest.raises(FileNotFoundError, match="No competition zip found"):
        CompetitionZip.from_dir(competition_missing_competition_zip)


def test_competition_zip_from_dir_raises_when_multiple_zips(competition_multiple_zips):
    with pytest.raises(ValueError, match="Expected exactly one competition zip"):
        CompetitionZip.from_dir(competition_multiple_zips)


def test_competition_zip_from_dir_raises_when_submissions_dir_missing(
    competition_missing_submissions_dir,
):
    with pytest.raises(FileNotFoundError, match="Submissions directory not found"):
        CompetitionZip.from_dir(competition_missing_submissions_dir)


def test_competition_zip_from_dir_raises_when_invalid_zip(competition_with_invalid_zip):
    with pytest.raises(ValueError, match="Invalid competition ZIP"):
        CompetitionZip.from_dir(competition_with_invalid_zip)


def test_competition_with_large_file():
    competition_zip = CompetitionZip.from_dir(IRIS)
    competition_submission_len = len(competition_zip.submission_pool.submissions)
    competition_zip.generate_large_submissions(large_file_size=1)
    assert (
        len(competition_zip.submission_pool.submissions)
        == competition_submission_len * 2
    )
    assert (
        len(
            [
                sub
                for sub in competition_zip.submission_pool.submissions
                if sub.zip_path.name.endswith("_large_submit.zip")
            ]
        )
        == competition_submission_len
    )
