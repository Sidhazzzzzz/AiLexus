#!/usr/bin/env bash
# Render build script — runs on every deploy

set -o errexit

pip install -r requirements.txt

cd anomaly_project

python manage.py collectstatic --no-input
python manage.py migrate
