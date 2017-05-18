#!/usr/bin/env bash

token="QW1ldGh5c3RmMWI4ZTMxZi02YzVlLTQ0NTktYjZkZC0wMWIyZjM3YmQwMmQ="
folder=$1 # eg "2017-05-11"
# workspace="./2017-05-11"
workspace=/local/recsys/raw_data_daily/${folder}
log_submission="${workspace}/submission_completion_log.txt"
touch $log_submission

resp=$(curl -silent -XGET -H "Authorization: Bearer ${token}" 'https://recsys.xing.com/api/online/data/status')
echo $resp >> $log_submission

cp ${workspace}/"neg_filtered_online_submission.txt" ${workspace}/"submission-$folder.csv"
resp=$(curl -XPOST -H "Authorization: Bearer ${token}" 'https://recsys.xing.com/api/online/submission' --data-binary @"${workspace}/submission-$folder.csv")
echo $resp >> $log_submission

resp=$(curl -silent -XGET -H "Authorization: Bearer ${token}" 'https://recsys.xing.com/api/online/submission')
echo $resp >> $log_submission