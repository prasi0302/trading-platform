import json
import hashlib
import hmac
import base64
import urllib.request
from datetime import datetime
import os


def handler(event, context):
    webhook_url = os.environ['WEBHOOK_URL']
    secret = os.environ['WEBHOOK_SECRET']

    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
    incident_id = f"cloudwatch-alarm-{int(datetime.utcnow().timestamp())}"

    alarm_name = event.get('detail', {}).get('alarmName', 'Unknown Alarm')
    alarm_desc = event.get('detail', {}).get('configuration', {}).get('description', '')

    payload = {
        "eventType": "incident",
        "incidentId": incident_id,
        "action": "created",
        "priority": "HIGH",
        "title": f"CloudWatch Alarm: {alarm_name}",
        "description": (
            f"Alarm '{alarm_name}' triggered. {alarm_desc}. "
            "IAM AccessDeniedException errors detected in Market Data Service logs. "
            "Possible IAM policy deletion or restriction."
        ),
        "service": "trading-platform",
        "timestamp": timestamp,
        "data": {
            "metadata": {
                "region": "us-east-1",
                "environment": "production",
                "alarm_name": alarm_name,
                "source": "cloudwatch"
            }
        }
    }

    payload_str = json.dumps(payload)
    message = f"{timestamp}:{payload_str}"
    signature = base64.b64encode(
        hmac.HMAC(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')

    req = urllib.request.Request(
        webhook_url,
        data=payload_str.encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'x-amzn-event-timestamp': timestamp,
            'x-amzn-event-signature': signature,
        },
        method='POST'
    )

    try:
        resp = urllib.request.urlopen(req)
        print(f"Webhook sent: {resp.status}")
    except Exception as e:
        print(f"Webhook error: {e}")

    return {'statusCode': 200}
