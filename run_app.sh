#!/bin/bash

python3 -m uvicorn settings:create_app --host 0.0.0.0 --port 7000 --factory --reload --reload-exclude env
