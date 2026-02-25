#!/bin/bash
# NewsMarvin daily job: rebuild site + send digest
cd /Users/manuelzuniga/ai/newsmarvin
export $(grep -v '^#' .env | xargs)

echo "=== $(date) ===" >> /tmp/newsmarvin.log

/usr/bin/python3 aggregate.py >> /tmp/newsmarvin.log 2>&1
/usr/bin/python3 send_digest.py >> /tmp/newsmarvin.log 2>&1
