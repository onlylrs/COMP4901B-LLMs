# If you don't want to use WANDB for logging, simply ignore this line and the script will still print out metrics
setenv WANDB_DIR /homes/rliuar/COMP4901B/COMP4901B-LLMs/assignment1/wandb
setenv WANDB_CACHE_DIR /homes/rliuar/COMP4901B/COMP4901B-LLMs/assignment1/wandb/.cache
setenv WANDB_CONFIG_DIR /homes/rliuar/COMP4901B/COMP4901B-LLMs/assignment1/wandb/.config
setenv WANDB_DATA_DIR /homes/rliuar/COMP4901B/COMP4901B-LLMs/assignment1/wandb/.data
setenv WANDB_ARTIFACT_DIR /homes/rliuar/COMP4901B/COMP4901B-LLMs/assignment1/wandb/.artifact
setenv WANDB_API_KEY b9e2ee25592f7b3910f716cbfa60fcdf556c6d46


setenv CUDA_VISIBLE_DEVICES 4
python run_llama.py \
  --run_name run1-fix-loss \
  --option pretrain \
  --data_path train_100M \
  --block_size  256 \
  --batch_size 512 \
  --micro_batch_size 32 \
  --epochs 1 \
  --tokenized_dir train_100M/tokenized \
  --use_gpu  \
  --val_path dev \
  --val_tokenized_dir dev/tokenized \
  --val_per_steps 200 \
  --test_path  test \
  --test_tokenized_dir test/tokenized \
  --auto_resume \
  --warmup_steps 100 \
  --warmup_ratio 0.1 \
  --lr 1e-3 
# --overwrite_tokenized # if you want to overwrite the tokenized data