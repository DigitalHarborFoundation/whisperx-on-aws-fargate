import logging
import os
from collections import namedtuple
from datetime import datetime
from pathlib import Path

import numpy as np
import whisperx

WhisperModels = namedtuple(
    "WhisperModels",
    ["device", "transcribe_model", "align_model", "align_metadata", "diarize_model"],
)
logger = logging.getLogger(__name__)


def load_models() -> WhisperModels:
    device = "cpu"
    language = "en"
    # compute_type = "float16"  # change to "int8" if low on GPU mem (may reduce accuracy)
    compute_type = "int8"
    model_cache_dir = Path("data/models")
    model_cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Will cache most models at '{model_cache_dir}'.")

    # 1. Transcribe with original whisper (batched)
    transcribe_model = whisperx.load_model(
        "large-v2",
        device,
        compute_type=compute_type,
        language="en",
        download_root=str(model_cache_dir),
    )
    align_model, align_metadata = whisperx.load_align_model(
        language,
        device=device,
        model_dir=str(model_cache_dir),
    )
    HF_TOKEN = os.environ["HF_TOKEN"]
    # whisperx.DiarizationPipeline() uses pyannote.audio.Pipeline.from_pretrained(model_name, use_auth_token=use_auth_token)
    # from_pretrained() takes a cache_dir argument, not currently propagated by whisperx
    try:
        diarize_model = whisperx.DiarizationPipeline(
            use_auth_token=HF_TOKEN, device=device
        )
    except AttributeError:
        raise ValueError(
            f"Unable to download model with token '{HF_TOKEN}'. Check logs for more info."
        )
    logger.info("Loaded Whisper models.")
    return WhisperModels(
        device,
        transcribe_model,
        align_model,
        align_metadata,
        diarize_model,
    )


def transcribe_wav(wav_filepath: Path, models: WhisperModels) -> dict:
    """
    This function transcribes, segments, and diarizes an audio file.


    References:
        1. What is speaker diarization? https://docs.nvidia.com/deeplearning/nemo/user-guide/docs/en/stable/asr/speaker_diarization/intro.html

    The code in this method is adapted from examples in the README: https://github.com/m-bain/whisperX/blob/main/README.md
    That code is licensed BSD-4-Clause.
    """

    # note: load_audio depends on ffmpeg
    s = datetime.now()
    audio: np.ndarray = whisperx.load_audio(wav_filepath)
    audio_loading_time = str(datetime.now() - s)

    # 1. Transcribe with original whisper (batched)
    # can optionally set batch_size here; 16 is the default, lower values will use less memory
    s = datetime.now()
    whisper_result_dict = models.transcribe_model.transcribe(audio)
    transcription_time = str(datetime.now() - s)

    # Speech Diarization
    # 2. Align whisper output
    s = datetime.now()
    align_result_dict = whisperx.align(
        whisper_result_dict["segments"],
        models.align_model,
        models.align_metadata,
        audio,
        models.device,
        return_char_alignments=False,
    )
    alignment_time = str(datetime.now() - s)

    # 3. Assign speaker labels
    # add min/max number of speakers if known
    s = datetime.now()
    diarize_segments = models.diarize_model(audio)
    diarization_time = str(datetime.now() - s)

    s = datetime.now()
    diarize_result_dict = whisperx.assign_word_speakers(
        diarize_segments, align_result_dict
    )
    speaker_assignment_time = str(datetime.now() - s)

    processing_times = {
        "audio_loading_time": audio_loading_time,
        "transcription_time": transcription_time,
        "alignment_time": alignment_time,
        "diarization_time": diarization_time,
        "speaker_assignment_time": speaker_assignment_time,
    }
    logger.info(f"Finished processing '{wav_filepath}': {processing_times}")
    md = {
        "processing_times": processing_times,
        "transcript": whisper_result_dict,
        "align": align_result_dict,
        "diarize": diarize_result_dict,
    }
    return md


if __name__ == "__main__":
    """
    This script tests the transcribe_wav function.
    It takes a single argument: the filepath to an mp4 or wav file.
    Sample invocation: `poetry run python src/transcribe/whisper.py data/tests/this_is_a_test_recording/video1485756545.mp4`

    Sample memory usage on an Apple M2 Pro:
    RSS: 1045.296875 MiB
    VMS: 404210.421875 MiB
    Max RSS: 2607.75 MiB
    """
    import resource
    import sys

    import dotenv
    import psutil

    from transcribe import video_utils

    assert dotenv.load_dotenv(), "Need a .env file in order to populate the HF_TOKEN."

    logging.basicConfig(level=logging.INFO)
    input_filepath = Path(sys.argv[-1])
    if not input_filepath.exists():
        logger.error(f"File {input_filepath} does not exist.")
        sys.exit(1)
    if input_filepath.suffix == ".mp4":
        # convert to wav
        wav_filepath = input_filepath.parent / (input_filepath.stem + ".wav")
        video_utils.convert_mp4_to_wav(input_filepath, wav_filepath)
    else:
        wav_filepath = input_filepath

    whisper_models = load_models()
    md = transcribe_wav(wav_filepath, whisper_models)
    print(md)

    # attempt to infer memory usage
    memory_info = psutil.Process().memory_info()
    logger.info(f"RSS: {memory_info.rss / 1024 ** 2} MiB")
    logger.info(f"VMS: {memory_info.vms / 1024 ** 2} MiB")

    # attempt to infer max RSS using this OS-dependent command
    logger.info(
        f"Max RSS: {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2} MiB"
    )
