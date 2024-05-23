# WhisperX on AWS Fargate

[![License](https://img.shields.io/github/license/DigitalHarborFoundation/whisperx-on-aws-fargate)](https://github.com/DigitalHarborFoundation/whisperx-on-aws-fargate/blob/main/LICENSE)

A Dockerized transcription pipeline using [WhisperX](https://github.com/m-bain/whisperX), originally intended for offline transcription and diarization of Zoom recordings.

The Docker container is run as AWS ETL job via AWS ECS and AWS Fargate to transcribe stored recordings. As this is a public sample, it omits the following critical details:
 - Downloading or otherwise loading into memory the mp4 recordings.
 - Saving the transcription metadata.

It would be straightforward to fork this repository to load the data from an appropriate source e.g. S3 or any other external storage. 

## Installation

 - Install the [AWS Copilot CLI](https://aws.github.io/copilot-cli/docs/overview/)

For local development:
 - Install [Poetry](https://python-poetry.org/docs/)
 - Install [FFmpeg](https://ffmpeg.org/)
 - Install dependencies, using make: `make install`

Not all of the Python dependencies are in the pyproject.toml dependency list, since it wasn't clear to the developers how to include some of the more complex deps (i.e. PyTorch and WhisperX).

## Execution

To re-deploy (because of changes to the Dockerfile, manifests, or code):

```bash
copilot deploy
```

To invoke the job manually:

```bash
copilot job run 
```

To view the most recent logs:

```bash
copilot job logs
```

## Environment

Environment variables needed:
 - `HF_TOKEN`

To change their values during execution on AWS, you'll need to update the `transcribe-recordings` JSON secret in AWS Secrets Manager.
Sample secret value: `{"HF_TOKEN": "hf_exampleToken"}`

For local development, place the key-value pairs in a `.env` file in this directory.

To add a new secret (see [guide](https://aws.github.io/copilot-cli/docs/developing/secrets/)), you'll need to tag it with `copilot-application` and `copilot-environment` tags, with their values set to `transcribe-recordings` and `transcribe-recordings-env` respectively.

The user's HuggingFace token (`HF_TOKEN`) will need to have accepted the user agreements for the two pyannote models, linked below.

## Models

This tool uses [WhisperX](https://github.com/m-bain/whisperX) for transcription, segmentation, and diarization.
All of the models are hosted on the HuggingFace model hub.

 - For transcription: [`openai/whisper-large-v2`](https://huggingface.co/openai/whisper-large-v2)
 - For segmentation: [`pyannote/segmentation-3.0`](https://huggingface.co/pyannote/segmentation-3.0)
 - For diarization: [`pyannote/speaker-diarization-3.1`](https://huggingface.co/pyannote/speaker-diarization-3.1)
 
 ## Development notes

The Docker image is currently ~2GB, thanks to the hefty Python dependencies.
To reduce task start-up time, we might consider including the models (which are cached to `data/models`) in the built Docker image.

Important caveat: this basic example uses a single CPU core to transcribe audio. In our experiments, it is 2-4x slower than real-time transcription. It should be straightforward to parallelize execution for batch processing of recordings.

Primary code contributor:

 - Zachary Levonian (<zach@levi.digitalharbor.org>)

Other contributors:

 - Jionghao Lin (jionghao [at] cmu [dot] edu)
