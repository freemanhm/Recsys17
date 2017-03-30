#!/usr/bin/env bash

SER_PATH=/nfs/isicvlnas01/users/ksharma/recsyslight

cd $SER_PATH

cd $SER_PATH/data_reduction
echo "Starting"
python clean_interactions.py
echo "Done"

<<COMMENT
python clean_interactions.py
echo "Finished clean"
python limit_interactions_target_users.py
echo "Finished limit target users"
python report_per_week_clean_interactions.py
echo "Finished report"
COMMENT

<<COMMENT
# cd $SER_PATH/data_preprocessing
# python preprocess_for_hmf.py

# cd $SER_PATH/statistics
# python distribution_stats.py


cd $SER_PATH/scoring
python run_baseline.py
COMMENT

<<COMMENT
python -m data_preprocessing/preprocess_for_hmf
COMMENT

<<COMMENT
if [ ! -d "./examples" ]
then
		mkdir ./examples
fi

if [ ! -d "./examples/preprocessing_cache" ]
then
		mkdir ./examples/preprocessing_cache
fi

if [ ! -d "./examples/dataset" ]
then
		mkdir ./examples/dataset
fi

if [ ! -d "./data_2017_filtered_interactions" ]
then
		mkdir ./data_2017_filtered_interactions
fi

if [ ! -d "./solutions" ]
then
		mkdir ./solutions
fi

if [ ! -d "./stats" ]
then
		mkdir ./stats
fi
COMMENT