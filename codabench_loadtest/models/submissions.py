from __future__ import annotations

import io
import os
import random
import shutil
import tempfile
import zipfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator


class SubmissionZip(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    zip_path: Path
    zip_bytes: bytes | io.BytesIO | None = None
    is_temporary: bool = Field(
        default=False,
    )  # Flag to indicate if the zip is a temporary file

    @property
    def zip_name(self) -> str:
        return self.zip_path.name

    def bytes_size(self) -> int:
        return self.zip_path.stat().st_size

    @classmethod
    def create_large_submission(
        cls, submission: SubmissionZip, extra_size_mb: int, chunk_mb: int = 50
    ) -> SubmissionZip:
        """Create a new SubmissionZip with a large temporary file added."""
        chunk = os.urandom(chunk_mb * 1024 * 1024)
        tmp_dir = tempfile.mkdtemp()
        tmp_path = Path(tmp_dir) / f"{submission.zip_path.stem}_large_submit.zip"
        try:
            with (
                zipfile.ZipFile(submission.zip_path, "r") as source_zf,
                zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_STORED) as new_zf,
            ):
                for item in source_zf.namelist():
                    new_zf.writestr(item, source_zf.read(item))

                with new_zf.open("padding_large_file.bin", "w") as target:
                    written = 0
                    while written < extra_size_mb * 1024 * 1024:
                        n = min(
                            chunk_mb * 1024 * 1024,
                            extra_size_mb * 1024 * 1024 - written,
                        )
                        target.write(chunk[:n])
                        written += n
        except Exception as e:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise e

        new_submission = cls(zip_path=tmp_path)
        new_submission.is_temporary = True
        return new_submission

    def __del__(self):
        """Clean up the temporary file if it was created."""
        if self.is_temporary and self.zip_path.exists():
            shutil.rmtree(self.zip_path.parent, ignore_errors=True)

    @model_validator(mode="after")
    def validate_submission_zip(self):
        if not self.zip_path.is_file():
            raise ValueError(f"Submission zip not found: {self.zip_path}")
        return self


class SubmissionPool(BaseModel):
    submissions: list[SubmissionZip] = Field(default_factory=list)

    @classmethod
    def from_dir(cls, directory: Path) -> SubmissionPool:
        zips = [SubmissionZip(zip_path=p) for p in sorted(directory.glob("*.zip"))]
        if not zips:
            raise ValueError(f"No submission zip found in {directory}")
        return cls(submissions=zips)

    def generate_large_submissions(self, large_file_size: int) -> None:
        """Generate large temporary files for each submission in the pool."""
        generated_submissions = [
            SubmissionZip.create_large_submission(
                submission, extra_size_mb=large_file_size
            )
            for submission in self.submissions
        ]
        self.submissions.extend(generated_submissions)

    def get_random_submission_zip(self) -> SubmissionZip:
        if not self.submissions:
            raise ValueError("Submission pool is empty")
        return random.choice(self.submissions).model_copy(
            update={"is_temporary": False}
        )
