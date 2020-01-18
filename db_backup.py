import datetime
import os
import subprocess

import boto3
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PGDUMP_EXECUTABLE = '/usr/bin/pg_dump'

PG_HOST = os.environ.get('PG_HOST', '')
PG_DATABASE = os.environ.get('PG_DATABASE', '')
PG_USER = os.environ.get('PG_USER', '')
PG_PASSWORD = os.environ.get('PG_PASSWORD', '')
PG_PORT = os.environ.get('PG_PORT', '')
PGCONNECT_TIMEOUT = 5

S3_REGION = os.environ.get('S3_REGION, 'us-west-1')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '')
S3_BUCKET_PATH = os.environ.get('S3_BUCKET_PATH', '')

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL')
SLACK_EMOJI = os.environ.get('SLACK_EMOJI')
SLACK_SUCCESS_MSG = os.environ.get(
    'SLACK_SUCCESS_MSG', 'Backup was successful'
)
SLACK_FAILURE_MSG = os.environ.get('SLACK_FAILURE_MSG', 'Backup failed')
SLACK_BOT_NAME = os.environ.get('SLACK_BOT_NAME', 'backup_bot')


def dump_db(output_file_name):
    TEMP_FILE_NAME = '/tmp/{}'.format(output_file_name)
    cmd = [
        PGDUMP_EXECUTABLE,
        '--clean',
        '--if-exists',
        '-Fc',  # custom
        '-x',  # no priviliges
        '-h', PG_HOST,
        '-d', PG_DATABASE,
        '-U', PG_USER,
        '-p', str(PG_PORT),
    ]
    try:
        with open(TEMP_FILE_NAME, 'w') as backup_file:
            completed_process = subprocess.run(
                cmd,
                stdout=backup_file,
                stderr=subprocess.PIPE,
                env={'PGPASSWORD': PG_PASSWORD,
                     'PGCONNECT_TIMEOUT': str(PGCONNECT_TIMEOUT)}
            )
    except Exception as e:  # noqa
        return False, str(e)
    try:
        completed_process.check_returncode()
    except subprocess.CalledProcessError as e:
        if completed_process.stderr:
            return False, completed_process.stderr.decode('utf-8')
        return False, str(e)
    return True, None


def upload_to_s3(file_name):
    TEMP_FILE_NAME = '/tmp/{}'.format(file_name)
    if S3_BUCKET_PATH is None:
        object_name = file_name
    else:
        object_name = '{}/{}'.format(S3_BUCKET_PATH, file_name)
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(TEMP_FILE_NAME, S3_BUCKET_NAME, object_name)
    except Exception as e:
        return False, str(e)
    return True, None


def generate_file_name():
    return '{}.dump'.format(
        datetime.datetime.utcnow().strftime(
            '%Y-%m-%d.%H:%M:%S'
        )
    )


def report_to_slack(is_success, error_details=None):
    if is_success:
        text = SLACK_SUCCESS_MSG
        color = 'good'
    else:
        text = SLACK_FAILURE_MSG
        color = 'danger'
    payload = {
        'attachments': [
            {
                'color': color,
            }
        ],
        'username': SLACK_BOT_NAME
    }
    if error_details:
        payload['attachments'][0]['pretext'] = text
        payload['attachments'][0]['text'] = error_details
    else:
        payload['attachments'][0]['text'] = text

    if SLACK_CHANNEL is not None:
        payload.update({'channel': SLACK_CHANNEL})
    if SLACK_EMOJI is not None:
        payload.update({'icon_emoji': SLACK_EMOJI})
    r = requests.post(SLACK_WEBHOOK_URL, json=payload)
    return r.text


def main():
    output_file_name = generate_file_name()
    status, error = dump_db(output_file_name=output_file_name)
    if status:
        status, error = upload_to_s3(file_name=output_file_name)
    if SLACK_WEBHOOK_URL:
        report_to_slack(status, error_details=error)


if __name__ == '__main__':
    main()

