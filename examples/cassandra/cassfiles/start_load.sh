#!/bin/bash

# The goal of this script is to create an interesting CPU trace.

IP_ADDR=`docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' some-cassandra1`
DC=datacenter1

MAINCYC=5000000
THREADS=64
FOLDER=`date "+%m-%d-%y-%X"`_'additive'
mkdir $FOLDER
echo "Outputing benchmark CSVs to $FOLDER"

CYCLERATE=15000
./nb5 rdwr_keyvalue default.readonly  cyclerate=$CYCLERATE main-cycles=$MAINCYC thread-count=$THREADS  hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to $FOLDER --logs-dir $FOLDER/logs
./nb5 rdwr_keyvalue default.writeonly  cyclerate=$CYCLERATE main-cycles=$MAINCYC thread-count=$THREADS  hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to $FOLDER --logs-dir $FOLDER/logs
./nb5 rdwr_keyvalue default.mixed  cyclerate=$CYCLERATE main-cycles=$MAINCYC thread-count=$THREADS  hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to $FOLDER --logs-dir $FOLDER/logs
CYCLERATE=30000
./nb5 rdwr_keyvalue default.writeonly  cyclerate=$CYCLERATE main-cycles=$MAINCYC thread-count=$THREADS  hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to $FOLDER --logs-dir $FOLDER/logs
CYCLERATE=20000
./nb5 rdwr_keyvalue default.writeonly  cyclerate=$CYCLERATE main-cycles=$MAINCYC thread-count=$THREADS  hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to $FOLDER --logs-dir $FOLDER/logs
CYCLERATE=50000
./nb5 rdwr_keyvalue default.readonly  cyclerate=$CYCLERATE main-cycles=$MAINCYC thread-count=$THREADS  hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to $FOLDER --logs-dir $FOLDER/logs
./nb5 rdwr_keyvalue default.writeonly  cyclerate=$CYCLERATE main-cycles=$MAINCYC thread-count=$THREADS  hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to $FOLDER --logs-dir $FOLDER/logs
./nb5 rdwr_keyvalue default.readonly  cyclerate=$CYCLERATE main-cycles=$MAINCYC thread-count=$THREADS  hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to $FOLDER --logs-dir $FOLDER/logs
CYCLERATE=13000
./nb5 rdwr_keyvalue default.readonly  cyclerate=$CYCLERATE main-cycles=$MAINCYC thread-count=$THREADS  hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to $FOLDER --logs-dir $FOLDER/logs