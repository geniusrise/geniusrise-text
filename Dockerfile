FROM nvidia/cuda:12.2.0-devel-ubuntu20.04 AS base

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN useradd --create-home genius

RUN apt-get update \
 && apt-get install -y software-properties-common build-essential curl wget vim git libpq-dev pkg-config \
 && add-apt-repository ppa:deadsnakes/ppa \
 && apt-get update \
 && apt-get install -y python3.10 python3.10-dev python3.10-distutils \
 && apt-get clean
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
 && python3.10 get-pip.py

RUN apt-get update && apt-get install -y git && apt-get clean

RUN pip install torch
RUN pip install --upgrade geniusrise
ENV AWS_DEFAULT_REGION=ap-south-1
ENV AWS_SECRET_ACCESS_KEY=oRs4RUJT7wU1cSoCfcR2BYQT9MeQL8R9dc4lBVQL
ENV AWS_ACCESS_KEY_ID=AKIASC32JQZNC5UZ4GKT
ENV HUGGINGFACE_ACCESS_TOKEN=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
ENV GENIUS=/home/genius/.local/bin/genius

COPY --chown=genius:genius . /app/

RUN pip3.10 install -r requirements.txt
RUN pip install multiprocess==0.70.15
USER genius

CMD ["genius", "--help"]
