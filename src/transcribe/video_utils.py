from pathlib import Path

from moviepy.editor import VideoFileClip


def convert_mp4_to_wav(mp4_filepath: Path, wav_filepath: Path | None = None) -> Path:
    # NOTE: given that ffmpeg is a dependency already, it might be faster to use `ffmpeg -i {mp4_filepath} {wav_filepath}` and remove the moviepy dependency
    if wav_filepath is None:
        wav_filepath = mp4_filepath.parent / (mp4_filepath.stem + ".wav")
    video = VideoFileClip(str(mp4_filepath))
    audio = video.audio
    audio.write_audiofile(str(wav_filepath))
    return wav_filepath
