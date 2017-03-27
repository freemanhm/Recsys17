#!/usr/bin/env bash

SER_PATH=/nfs/isicvlnas01/users/ksharma/recsys
rm $SER_PATH/src/jobop.txt
rm $SER_PATH/src/joberr.txt

qsub -S /bin/bash -l gpu=0 -q isicvl01.q -o $SER_PATH/src/jobop.txt -e $SER_PATH/src/joberr.txt -V prep.sh

# qsub -S /bin/bash -l gpu=1 -o /nfs/isicvlnas01/users/ksharma/recsys/src/jobop.txt -e /nfs/isicvlnas01/users/ksharma/recsys/src/joberr.txt -V run_hmf.sh 32 1 True 1000 False
# bash run_hmf.sh 32 1 True 2 False
# bash run_hmf.sh 32 1 True 2 True

# qsub -S /bin/bash -l gpu=1 -o /nfs/isicvlnas01/users/ksharma/recsys/src/jobop.txt -e /nfs/isicvlnas01/users/ksharma/recsys/src/joberr.txt -V run_hmf.sh 32 1 True 1000 False
# qsub -S /bin/bash -l gpu=0 -q isicvl01.q -o /nfs/isicvlnas01/users/ksharma/recsys/src/jobop.txt -e /nfs/isicvlnas01/users/ksharma/recsys/src/joberr.txt -V run_hmf.sh 32 1 cd 1000 True