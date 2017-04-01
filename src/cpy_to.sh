#!/bin/bash

cd ..
SER_PATH=isicvl01:/nfs/isicvlnas01/users/ksharma/recsyslight

rsync -av attributes $SER_PATH
rsync -av data_preprocessing $SER_PATH
rsync -av data_reduction $SER_PATH
rsync -av hmf $SER_PATH
rsync -av scoring $SER_PATH
rsync -av src $SER_PATH
rsync -av utils $SER_PATH

<<COMMENT
NOT TO DO
rsync -av data_2017 $SER_PATH
rsync -av data_2017_filtered_interactions $SER_PATH
rsync -av examples $SER_PATH
rsync -av solutions $SER_PATH
rsync -av stats $SER_PATH
COMMENT