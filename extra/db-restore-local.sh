#!/bin/sh
set -e #exit on error

mongodb_id="$(docker ps | awk '/mongo-auth/{print $1;exit;}')"

current_dir="$(cd "$(dirname "${0}")" && pwd)"
rm -rf    "${current_dir}/restore"
mkdir     "${current_dir}/restore"
cp "${1}" "${current_dir}/restore"

cd "${current_dir}/restore"
unzip *.zip

docker exec     "${mongodb_id}" rm -rf /dump
docker cp dump/ "${mongodb_id}":/dump
docker exec     "${mongodb_id}" mongorestore --drop -u app -p app --db app /dump/app/

rm -rf    "${current_dir}/restore"
