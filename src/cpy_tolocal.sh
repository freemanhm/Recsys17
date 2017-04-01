#!/bin/bash

SER_PATH=isicvl01:/nfs/isicvlnas01/users/ksharma/recsys
rsync -av $SER_PATH/solutions/raw_rec ../solutions
