#!/bin/sh
source .venv/bin/activate
python -m flask --app main run -p 49000 --debug