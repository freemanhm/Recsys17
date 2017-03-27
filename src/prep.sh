#!/usr/bin/env bash

SER_PATH=/nfs/isicvlnas01/users/ksharma/recsys/
<<COMMENT
# cd $SER_PATH/data_2017
# python limit_interactions_weeks.py

# cd $SER_PATH/data_preprocessing
# python preprocess_for_hmf.py

# cd $SER_PATH/statistics
# python distribution_stats.py
COMMENT

cd $SER_PATH/scoring
python run_baseline.py


<<COMMENT
python -m data_preprocessing/preprocess_for_hmf
COMMENT