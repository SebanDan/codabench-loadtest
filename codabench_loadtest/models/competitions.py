from __future__ import annotations

import random
import zipfile
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from codabench_loadtest.models.submissions import SubmissionPool, SubmissionZip


class CompetitionZip(BaseModel):
    id: int | None = Field(
        default=None, description="Unique identifier for the competition"
    )
    phase: int | None = Field(
        default=None, description="Unique identifier for the competition phase"
    )
    bundle_path: Path
    submission_pool: SubmissionPool

    @property
    def name(self) -> str:
        return self.bundle_path.stem

    @property
    def phase_id(self) -> int:
        if self.phase is None and self.id is None:
            raise ValueError("Competition phase ID is not set")
        return self.phase or self.id  # type: ignore

    def get_random_submission_zip(self) -> SubmissionZip:
        """Get a submission from the submission pool."""
        return self.submission_pool.get_random_submission_zip()

    @classmethod
    def from_dir(cls, directory: Path) -> CompetitionZip:
        competition_zips = list(directory.glob("*.zip"))
        if not competition_zips:
            raise FileNotFoundError(f"No competition zip found in {directory}")
        if len(competition_zips) > 1:
            raise ValueError(
                f"Expected exactly one competition zip in {directory}, found {len(competition_zips)}"
            )
        if not (directory / "submissions").is_dir():
            raise FileNotFoundError(
                f"Submissions directory not found in {directory}, expected at {directory / 'submissions'}"
            )
        return cls(
            bundle_path=competition_zips[0],
            submission_pool=SubmissionPool.from_dir(directory / "submissions"),
        )

    @model_validator(mode="after")
    def validate_competition_bundle(self):
        if not self.bundle_path.is_file():
            raise FileNotFoundError(f"Competition bundle not found: {self.bundle_path}")
        if self.bundle_path.suffix.lower() != ".zip":
            raise ValueError(
                f"Competition bundle must be a ZIP file: {self.bundle_path}"
            )
        try:
            with zipfile.ZipFile(self.bundle_path) as bundle:
                if "competition.yaml" not in bundle.namelist():
                    raise ValueError(
                        "Competition bundle must contain competition.yaml at its root"
                    )
                bad_file = bundle.testzip()
                if bad_file is not None:
                    raise ValueError(
                        f"Competition bundle contains a corrupt file: {bad_file}"
                    )
        except zipfile.BadZipFile as error:
            raise ValueError(f"Invalid competition ZIP: {self.bundle_path}") from error
        return self


class CompetitionPool(BaseModel):
    competitions: list[CompetitionZip]

    @classmethod
    def from_dir(
        cls, directory: Path, competition_filter: list[str] | None = None
    ) -> CompetitionPool:
        return cls(
            competitions=[
                CompetitionZip.from_dir(d)
                for d in directory.iterdir()
                if d.is_dir()
                and (not competition_filter or d.name in competition_filter)
            ]
        )

    def get_random_competition_id(self) -> CompetitionZip:
        if not self.competitions:
            raise ValueError("Competition pool is empty")
        competition_ids = [c for c in self.competitions if c.id is not None]
        if not competition_ids:
            raise ValueError("No competitions with valid IDs found")
        return random.choice(competition_ids)
