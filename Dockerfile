# FROM python:3.9.17-buster
# FROM 763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-training:1.13.1-gpu-py39-cu117-ubuntu20.04-sagemaker
FROM 763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-training:1.13.1-gpu-py39-cu117-ubuntu20.04-ec2
WORKDIR /
RUN apt-get update && apt-get install -y git

RUN git clone https://github.com/bigcode-project/bigcode-evaluation-harness.git && \
    mv bigcode-evaluation-harness/* . && \
    rm -rf bigcode-evaluation-harness && \
    pip install -e .
