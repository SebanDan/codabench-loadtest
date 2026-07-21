from __future__ import annotations

import io
import os
import random
import zipfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SubmissionZip(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    zip_path: Path
    zip_bytes: bytes | io.BytesIO | None = None

    def get_zip_bytes(self) -> bytes | io.BytesIO:
        return self.zip_bytes or self.zip_path.read_bytes()

    @property
    def zip_name(self) -> str:
        return self.zip_path.name

    def bytes_size(self) -> int:
        """Return the size of the zip file in bytes."""
        body = self.get_zip_bytes()
        if isinstance(body, bytes):
            return len(body)

        # If it's a BytesIO, we need to get the size differently
        pos = body.tell()
        body.seek(0, os.SEEK_END)
        size = body.tell()
        body.seek(pos)
        return size

    def generate_heavy_space(
        self, extra_size_mb: int = 1024, chunk_mb: int = 50
    ) -> None:
        buffer = io.BytesIO()
        filler = os.urandom(chunk_mb * 1024 * 1024)

        with (
            zipfile.ZipFile(self.zip_path, "r") as source_zf,
            zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as new_zf,
        ):
            for item in source_zf.namelist():
                new_zf.writestr(item, source_zf.read(item))

            with new_zf.open("padding_large_file.bin", "w") as target:
                written = 0
                while written < extra_size_mb * 1024 * 1024:
                    n = min(
                        chunk_mb * 1024 * 1024, extra_size_mb * 1024 * 1024 - written
                    )
                    target.write(filler[:n])
                    written += n

        buffer.seek(0)
        self.zip_bytes = buffer

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

    def get_random_submission_zip(self) -> SubmissionZip:
        if not self.submissions:
            raise ValueError("Submission pool is empty")
        return random.choice(self.submissions)
