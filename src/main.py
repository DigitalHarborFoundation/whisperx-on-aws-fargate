import json
import logging
import os
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import dotenv

from transcribe import aws_utils, video_utils, whisper

VERSION = version("transcribe-recordings")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def transcribe_file(
    recording_filepath: Path,
    whisper_models: whisper.WhisperModels,
) -> dict:
    start = datetime.now()
    wav_filepath = video_utils.convert_mp4_to_wav(recording_filepath)
    wav_conversion_time = str(datetime.now() - start)
    md = whisper.transcribe_wav(wav_filepath, whisper_models)
    md["wav_conversion_time"] = wav_conversion_time
    # delete the cached WAV file
    wav_filepath.unlink()
    return md


def get_recordings_to_transcribe() -> list[Path]:
    # TODO implement me
    # this function could e.g. return a list of CloudPaths in S3
    return []


def transcribe_recordings():
    recording_files = get_recordings_to_transcribe()
    logger.info(f"Identified {len(recording_files)} recording files to transcribe.")
    working_dir = Path("data/tmp")
    working_dir.mkdir(parents=True, exist_ok=True)

    n_to_transcribe = len(recording_files)
    if n_to_transcribe > 0:
        whisper_models = whisper.load_models()
        n_processed = 0
        for recording_filepath in recording_files:
            logger.info(
                f"Generating transcript for {recording_filepath} ({n_processed + 1} / {n_to_transcribe})."
            )
            processing_start = datetime.now(timezone.utc)
            md = {
                "process_name": "transcribe-recordings",
                "process_version": VERSION,
                "processing_start_time": processing_start.isoformat(),
            }
            # transcribe the file
            transcription_md = transcribe_file(recording_filepath, whisper_models)
            md["processing_time"] = str(datetime.now(timezone.utc) - processing_start)
            md["whisper"] = transcription_md
            # TODO save the metadata dictionary somewhere
            n_processed += 1


def main():
    execution_environment_metadata = aws_utils.get_execution_environment_metadata()
    logger.info(f"Environment: {execution_environment_metadata}")
    if dotenv.load_dotenv(override=True):
        logger.info("Environment variables set from .env file.")

    transcribe_recordings()

    logger.info("Finished execution.")


if __name__ == "__main__":
    main()
