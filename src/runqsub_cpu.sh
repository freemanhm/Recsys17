#!/usr/bin/env bash

SER_PATH=/nfs/isicvlnas01/users/ksharma/recsyslight/

JO_LOCAL=/nfs/isicvlnas01/users/ksharma/recsyslight/src/jobop_local_cpu.txt
JE_LOCAL=/nfs/isicvlnas01/users/ksharma/recsyslight/src/joberr_local_cpu.txt

JO_ONLINE=/nfs/isicvlnas01/users/ksharma/recsyslight/src/jobop_ol_cpu.txt
JE_ONLINE=/nfs/isicvlnas01/users/ksharma/recsyslight/src/joberr_ol_cpu.txt

# Training and Recommendations
qsub -S /bin/bash -l gpu=0 -q isicvl01.q -o $JO_LOCAL -e $JE_LOCAL -V hmf_31_1_1000_train_rec_local_eval.sh
qsub -S /bin/bash -l gpu=0 -q isicvl01.q -o $JO_ONLINE -e $JE_ONLINE -V hmf_31_1_1000_train_rec_online_subm.sh

# qsub -S /bin/bash -l gpu=0 -q isicvl01.q -o $JO_ONLINE -e $JE_ONLINE -V prep.sh


<<COMMENT
if [ -f $joberrfile ] ; then
    rm $SER_PATH/src/joberr.txt
fi
if [ -f $jobopfile ] ; then
    rm $SER_PATH/src/jobop.txt
fi

-q isicvl01.q
-q glaive-isi.q

# Data Prep
# qsub -S /bin/bash -l gpu=1 -q glaive-isi.q -o /nfs/isicvlnas01/users/ksharma/recsyslight/src/jobop.txt -e /nfs/isicvlnas01/users/ksharma/recsyslight/src/joberr.txt -V prep.sh

COMMENT