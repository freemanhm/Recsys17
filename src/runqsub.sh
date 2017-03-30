#!/usr/bin/env bash

SER_PATH=/nfs/isicvlnas01/users/ksharma/recsyslight/

jobopfile=/nfs/isicvlnas01/users/ksharma/recsyslight/src/jobop.txt
joberrfile=/nfs/isicvlnas01/users/ksharma/recsyslight/src/joberr.txt

#<<COMMENT
if [ -f $joberrfile ] ; then
    rm $SER_PATH/src/joberr.txt
fi
if [ -f $jobopfile ] ; then
    rm $SER_PATH/src/jobop.txt
fi
#COMMENT

# Data Prep
qsub -S /bin/bash -l gpu=1 -q glaive-isi.q -o /nfs/isicvlnas01/users/ksharma/recsyslight/src/jobop.txt -e /nfs/isicvlnas01/users/ksharma/recsyslight/src/joberr.txt -V prep.sh

# Training
# qsub -S /bin/bash -q isicvl01.q -o /nfs/isicvlnas01/users/ksharma/recsys/src/jobop.txt -e /nfs/isicvlnas01/users/ksharma/recsys/src/joberr.txt -V run_hmf.sh 32 1 True 1000 False

# Recommend
# qsub -S /bin/bash -l gpu=1 -q glaive-isi.q -o $SER_PATH/src/jobop.txt -e $SER_PATH/src/joberr.txt -V run_hmf.sh 32 1 True 1000 True