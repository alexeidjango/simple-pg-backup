# Simple Postgres DB backup script

Written during one of those nights when you realize you're writing the same script for the 10th time on the 10th project, so it's time to finally write it down and keep somewhere.

Script runs `pg_dump`on selected DB, uploads resulting archive to S3 and optonally notifies in Slack channel. Driven by environment variables, so can be run against multiple DB instances.

## How to run

- Have Python installed (the script was tested with Python3.7, but technically should work with 2.7 and any 3+)
- Install dependencies:
  - if you're using virtualenv, activate it;
  - run `python3.7 -m pip install -r requirements.txt`
- Actually run the script `python3.7 db_backup.py`

The script expects the following env variables to be set:

- `PG_HOST` - hostname of Postgres dB
- `PG_DATABASE` - name of DB to backup
- `PG_PORT` - DB port (usually `5432`)
- `PG_USER` / `PG_PASSWORD` - credentials of the DB user who has access to the DB
- `S3_REGION` - (optional, defaults to `us-west-1`) 
- `S3_BUCKET_NAME` - name of the bucket to place backups
- `S3_BUCKET_PATH` - path (folder) in the bucket where to place backup file (e.g. `backups/production`)
- `SLACK_WEBHOOK` - (optional) - webhook URL  of the Slack channel where to report backup status
- `SLACK_CHANNEL` - (optional) - Slack channel (or user) where to report, in a form of "#channel" or "@user". If omitted - will post to channel to which incoming webhook was originally attached
- `SLACK_EMOJI` - (optional) - use it if you want to override Slack bot's avatar; accepts Slack's built-in or custom emoji code (e.g. `:robot_face:`). If omitted, defaults to default bot's avatar
- `SLACK_BOT_NAME`- (optional) - overrides default bot name
- `SLACK_SUCCESS_MSG` - (optional) - custom message to post if backup was successful
- `SLACK_FAILURE_MSG`- (optional)- custom message to post if backup failed

## Running with Cron

Cron runs it's commands in it's clean shell, thus it doesn't pass environment variables set by a user to it's commands. In this case it makes sense to create an env file in a form of:

`/home/ubuntu/backup_env`

```bash
export PG_DATABASE=your_pd_db_name
export PG_HOST=your.pg.host
export PG_PASSWORD=your_pg_password
export PG_PORT=5432
export PG_USER=your_pg_user
export S3_BUCKET_NAME=your_s3_bucket_name
export S3_BUCKET_PATH=bucket_path
export SLACK_BOT_NAME="Backup Bot"
export SLACK_CHANNEL='#auto-db-backup'
export SLACK_EMOJI=':robot_face:'
export SLACK_FAILURE_MSG=":warning: Production DB backup failed"
export SLACK_SUCCESS_MSG="Production DB backup completed successfully."
export SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR_SLACK_HOOK
```

then create runner script, e.g.

`/home/ubuntu/db_backup.sh`

```bash
#!/bin/bash
set -ev
# if you're running virtualenv - activate it
source /home/ubuntu/db_backup/venv/bin/activate

# read env variable
source /home/ubuntu/staging_env
python3.7 /home/ubuntu/db_backup/db_backup.py
```

and then add the following crontab:

```bash
0 3,15 * * * ubuntu /home/ubuntu/db_backup.sh
```

