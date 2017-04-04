#!/bin/bash

SER_PATH=isicvl01:/nfs/isicvlnas01/users/ksharma/temprec/examples/train/hmf_r17_xing_31lr1teFalse
# rsync -av $SER_PATH/online_submission.txt ../solutions
rsync -av $SER_PATH/neg_filtered_online_submission.txt ../solutions
