# Run Mamba 3 through the standard eval harness
# lm_eval --model hf \
#   --model_args pretrained=state-spaces/mamba-3-1.5b \
#   --tasks hellaswag,arc_easy,arc_challenge,winogrande,piqa \
#   --device cuda:0 \
#   --batch_size 8
