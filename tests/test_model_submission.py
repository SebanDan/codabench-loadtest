import io
import zipfile

from codabench_loadtest.models import SubmissionPool
from tests.conftest import IRIS


def test_generate_heavy_space_adds_expected_padding_size():
    submission_pool = SubmissionPool.from_dir(IRIS)
    submission = submission_pool.submissions[0]
    original_size = submission.bytes_size()

    # Small volume for a quick test
    submission.generate_heavy_space(extra_size_mb=1, chunk_mb=1)

    assert submission.zip_bytes is not None
    body = submission.get_zip_bytes()
    assert isinstance(body, io.BytesIO)

    with zipfile.ZipFile(body, "r") as zf:
        names = zf.namelist()
        assert "padding_large_file.bin" in names

        padding_info = zf.getinfo("padding_large_file.bin")
        assert padding_info.file_size == 1024 * 1024

    # The total size of the zip file should be at least 1MB larger than the original
    assert submission.bytes_size() >= original_size + 1024 * 1024
