#!/bin/bash
set -e

./wait-for-it.sh postgres:5432
./wait-for-it.sh kafka:9092

exec "$@"
