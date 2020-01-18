et -ev
# if you're running virtualenv - activate it
source /home/ubuntu/db_backup/venv/bin/activate

# read env variable
source /home/ubuntu/staging_env
python3.7 /home/ubuntu/db_backup/db_backup.py
