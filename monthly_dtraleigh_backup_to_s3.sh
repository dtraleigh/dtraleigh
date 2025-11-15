#!/bin/bash
set -euo pipefail

# CONFIGURATION
DATE=$(date +%F)
PROJECT_NAME="dtraleigh"
PROJECT_DIR="/home/cophead567/apps/$PROJECT_NAME"
VENV_DIR="$PROJECT_DIR/env"
BACKUP_DIR="/tmp/${PROJECT_NAME}_backup_$DATE"
S3_BUCKET="s3://dtraleigh-django-backups/$DATE"
DB1_NAME="develop"
DB1_USER="develop"
DB2_NAME="parcels"
DB2_USER="dtraleigh_dba"

# Prepare
rm -rf "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup codebase (excluding venv, logs, and static/media files)
tar -czf "$BACKUP_DIR/codebase.tar.gz" -C "$PROJECT_DIR" . \
  --exclude='env*' \
  --exclude='*.log' \
  --exclude='static' \
  --exclude='media' \
  --exclude='tmp'

# Backup virtualenv
tar -czf "$BACKUP_DIR/venv.tar.gz" -C "$VENV_DIR" .

# Backup PostgreSQL databases using .pgpass
pg_dump -U "$DB1_USER" --host=localhost "$DB1_NAME" | gzip > "$BACKUP_DIR/${DB1_NAME}_db.sql.gz"
pg_dump -U "$DB2_USER" --host=localhost "$DB2_NAME" | gzip > "$BACKUP_DIR/${DB2_NAME}_db.sql.gz"

# Upload to S3
aws s3 cp "$BACKUP_DIR" "$S3_BUCKET" --recursive

# Cleanup local
rm -rf "$BACKUP_DIR"

echo "Backup complete: $DATE" >> ~/backup.log
