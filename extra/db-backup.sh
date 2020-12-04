#!/bin/sh
set -e #exit on error

mongodb_id="$(docker ps | awk '/mongo-auth/{print $1;exit;}')"

docker exec -i "${mongodb_id}" rm -rf /dump
docker exec -i "${mongodb_id}" mongodump -u app -p app --db app && rm -rf /dump
docker cp "${mongodb_id}":/dump /dump

mkdir -p /backups
zip   -r /backups/dump."$(date +"%d.%b.%Y.%H:%M:%S")".zip /dump

find /backups -type f -iname "*.zip" -printf "%T@ %P\n"   | \
    sort -nr | awk -v maxBackups="${1}" 'NR > maxBackups' | cut -d' ' -f 2- | xargs rm -rf
