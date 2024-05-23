.PHONY: help install ensure-poetry build-docker run-docker remove-docker

export PATH := $(HOME)/.local/bin:$(PATH)

help:
	@echo "Relevant targets are 'install' and 'build-docker'."

install:
	@$(MAKE) ensure-poetry
	@poetry install
	@poetry run pip install "torch>=2" "torchaudio>=2" --index-url https://download.pytorch.org/whl/cpu
	@poetry run pip install "faster-whisper==1.0.0" transformers
	@poetry run pip install git+https://github.com/m-bain/whisperx.git


ensure-poetry:
	@# see issue: https://stackoverflow.com/questions/77019756/make-not-finding-executable-added-to-path-in-makefile
	@if ! command -v poetry &> /dev/null; then \
		echo "Installing poetry"; \
		curl -sSL https://install.python-poetry.org | python - ; \
		echo "Poetry installed, but you might need to update your PATH before Make will detect it."; \
	fi

build-docker:
	@docker build -t transcribe_recordings -f Dockerfile .

run-docker:
	@$(MAKE) remove-docker
	@docker run \
	--name transcribe_recordings_container \
	--mount type=bind,source=.env,target=/usr/etl/.env \
	transcribe_recordings:latest

remove-docker:
	@if docker ps -q --filter "name=transcribe_recordings_container" | grep -q .; then \
		echo "Stopping container"; \
		docker stop transcribe_recordings_container; \
	fi
	@if docker ps -a -q --filter "name=transcribe_recordings_container" | grep -q .; then \
		echo "Removing container"; \
		docker remove --volumes transcribe_recordings_container; \
	fi
