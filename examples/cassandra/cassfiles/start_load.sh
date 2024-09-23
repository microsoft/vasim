#!/bin/bash

IP_ADDR=docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' some-cassandra1
DC=datacenter1

CYCLERATE=500000
MAINCYC=5000000
THREADS=64
for i in {1..3};
do
	FOLDER=`date "+%m-%d-%y-%X"`
	echo $FOLDER
	mkdir $FOLDER
	./nb5 nova-keyvalue default.readonly  cyclerate=$CYCLERATE main-cycles=$MAINCYC thread-count=$THREADS  hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to $FOLDER --logs-dir $FOLDER/logs
done
