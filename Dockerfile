FROM python:3.10

WORKDIR /usr/etl

COPY ./pyproject.toml .
COPY ./README.md .
COPY ./src ./src

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

RUN python -m pip install --upgrade pip
RUN pip install poetry

RUN poetry install --without dev
RUN poetry run pip install "torch>=2" "torchaudio>=2" --index-url https://download.pytorch.org/whl/cpu
RUN poetry run pip install "faster-whisper==1.0.0" transformers
RUN poetry run pip install git+https://github.com/m-bain/whisperx.git

ENTRYPOINT ["poetry", "run", "python", "src/main.py"]