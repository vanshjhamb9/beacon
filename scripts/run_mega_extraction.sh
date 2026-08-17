#!/bin/bash
# Mega Lead Extraction - runs every 20 minutes via cron
# Extracts leads from CSV with founder/CMO/CTO/VC enrichment

cd /home/ubuntu/beacon
export PYTHONPATH=/home/ubuntu/beacon/apps/api:/home/ubuntu/beacon

.venv/bin/python apps/api/app/scripts/mega_extract_and_store.py >> /var/log/mega_extraction.log 2>&1
