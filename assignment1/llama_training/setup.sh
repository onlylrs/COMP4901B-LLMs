#!/usr/bin/env bash

conda create -n llama_hw python=3.11
conda activate llama_hw

cd ../data_preprocess
python -m pip install -r requirements.txt
cd ../llama_training

# Modify this command depending on your system's environment.
# As written, this command assumes you have CUDA on your machine, but
# refer to https://pytorch.org/get-started/previous-versions/ for the correct
# command for your system.
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
python -m pip install tqdm==4.66.1
python -m pip install requests==2.31.0
python -m pip install importlib-metadata==3.7.0
python -m pip install filelock==3.0.12
python -m pip install scikit-learn==1.2.2
python -m pip install numpy==1.26.3
python -m pip install tokenizers==0.13.3
python -m pip install sentencepiece==0.1.99
python -m pip install wandb