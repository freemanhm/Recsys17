#!/usr/bin/env bash
# path="/Users/karishmasharma/Documents/Recsys17/online/"
workspace=/local/recsys

fetch_path=${workspace}/online
token="QW1ldGh5c3RmMWI4ZTMxZi02YzVlLTQ0NTktYjZkZC0wMWIyZjM3YmQwMmQ="
# curl -vv -XGET -H "Authorization: Bearer ${token}" 'https://recsys.xing.com/api/team'
data_updates_file="$fetch_path/data_updates_file"

response=$(curl -XGET -H "Authorization: Bearer ${token}" 'https://recsys.xing.com/api/online/data/status')

seen=$(echo | grep -x "${response}" $data_updates_file)
echo $seen

if [[ $seen == "" ]]
then
var=$(echo $response | grep -Eo '[[:digit:]]{4}-[[:digit:]]{2}-[[:digit:]]{2}')
echo "${response}" >> $data_updates_file
folder="$fetch_path/$var"
mkdir $folder
curl -XGET -H "Authorization: Bearer ${token}" 'https://recsys.xing.com/api/online/data/items' > $folder/items.csv

curl -XGET -H "Authorization: Bearer ${token}" 'https://recsys.xing.com/api/online/data/users' > $folder/users.csv

curl -XGET -H "Authorization: Bearer ${token}" 'https://recsys.xing.com/api/online/data/interactions' > $folder/interactions.csv

# todo uncomment
mkdir ${workspace}/raw_data_daily/$var
python ${workspace}/recommendation/process.py -f $var
fi