import gc
import io
import zipfile

from codabench_loadtest.models import SubmissionPool, SubmissionZip
from tests.conftest import IRIS


def test_generate_heavy_space_adds_expected_padding_size():
    submission_pool = SubmissionPool.from_dir(IRIS)
    submission = submission_pool.submissions[0]
    original_size = submission.bytes_size()

    # Small volume for a quick test
    submission = SubmissionZip.create_large_submission(
        submission, extra_size_mb=1, chunk_mb=1
    )

    body = io.BytesIO(submission.zip_path.read_bytes())
    assert isinstance(body, io.BytesIO)

    with zipfile.ZipFile(body, "r") as zf:
        assert "padding_large_file.bin" in zf.namelist()
        assert zf.getinfo("padding_large_file.bin").file_size == 1024 * 1024

    # The total size of the zip file should be at least 1MB larger than the original
    assert submission.bytes_size() >= original_size + 1024 * 1024
    assert submission.is_temporary is True
    assert "large_submit" in submission.zip_path.name
    assert submission.zip_path.exists()


def test_model_copy_does_not_delete_temporary_folder():
    submission_pool = SubmissionPool.from_dir(IRIS)
    large = SubmissionZip.create_large_submission(
        submission_pool.submissions[0], extra_size_mb=1, chunk_mb=1
    )
    tmp_path = large.zip_path
    copy = large.model_copy(update={"is_temporary": False})
    assert copy.is_temporary is False  # Field not copied
    del copy
    gc.collect()

    assert large.zip_path.exists()
    del large
    gc.collect()
    assert not tmp_path.exists()


def test_model_copy_does_not_delete_temporary_folder_from_pool():
    submission_pool = SubmissionPool.from_dir(IRIS)
    submission_pool.generate_large_submissions(large_file_size=1)
    submission_pool.submissions = [
        s
        for s in submission_pool.submissions
        if s.zip_path.name.endswith("_large_submit.zip")
    ]
    selected_large = submission_pool.get_random_submission_zip()

    tmp_path = selected_large.zip_path
    assert "large_submit" in selected_large.zip_path.name
    assert selected_large.is_temporary is False  # Field not copied
    del selected_large
    gc.collect()

    assert tmp_path.exists()
