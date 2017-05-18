#!/usr/bin/env bash

folder=$1

workspace=/local/recsys/

# source /usr/usc/cuda/8.0/setup.sh

cd ${workspace}/hmf/

data_xing_noid_het=${workspace}/cache/xing_noid_het/
raw_xing=${workspace}/raw_data/xing/
raw_data_daily=${workspace}/raw_data_daily/

train_dir=${workspace}/pretrain/${model}


/local/recsys/anaconda2/bin/python run_hmf.py --dataset xing --data_dir $data_xing_noid_het --raw_data $raw_xing \
 --combine_att het --batch_size 64 --size 64 --keep_prob 0.5 --learning_rate 10 \
 --loss ce --n_sampled 5000 --n_resample 100 --no_user_id True \
 --steps_per_checkpoint 4000 --item_vocab_size 80000 --weighted_loss False \
 --n_epoch 1000  --train_dir ${train_dir}/c17_xinghetNoidm64h64d05l20Lcen_s5000n_re100t4000v80000n1000/ \
 --recommend True --top_N_items 250 --true_targets True --raw_data_daily ${raw_data_daily}/${folder} --new_users True


<<COMMENT
python run_hmf.py --dataset xing --data_dir $data_xing_noid_het --raw_data $raw_xing \
 --combine_att het --batch_size 64 --size 64 --keep_prob 0.5 --learning_rate 20 \
 --loss warp --n_sampled 5000 --n_resample 100 --no_user_id True \
 --steps_per_checkpoint 4000 --item_vocab_size 80000 --weighted_loss False \
 --n_epoch 1000  --train_dir ${train_dir}/c17_xinghetNoidm64h64d05l20Lwarpn_s5000n_re100t4000v80000n1000/ \
 --recommend True --top_N_items 250 --true_targets True --raw_data_daily ${raw_data_daily}/${folder} --new_users True

COMMENT



