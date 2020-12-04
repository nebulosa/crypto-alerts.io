#!/bin/sh
set -e #exit on error

mongodb_id="$(docker ps | awk '/mongo-auth/{print $1;exit;}')"

cd /restore
rm -rf dump/
unzip "${1}"

docker exec     "${mongodb_id}" rm -rf /dump
docker cp dump/ "${mongodb_id}":/dump
docker exec     "${mongodb_id}" mongorestore --drop -u app -p app --db app /dump/app/
