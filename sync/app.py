import os
import requests
import boto3
import base64
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

LOOKBACK_HOURS = 4
QUERY_DAYS = 1

ssm = boto3.client("ssm")


def get_parameter(name):
    return ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]


def init_garmin_session():
    session_b64 = get_parameter("/cycling/garmin/session")
    os.environ["GARTH_TOKEN"] = session_b64

    import garth
    print("Logged in to Garmin as " + garth.client.username)

def get_intervals_auth(api_key):
    b64_auth = base64.b64encode(f"API_KEY:{api_key}".encode()).decode('ascii')
    return {"Authorization": f"Basic {b64_auth}"}

def get_intervals_activities(athlete_id, api_key):
    since = (datetime.now() - timedelta(days=QUERY_DAYS)).strftime("%Y-%m-%d")

    response = requests.get(
        f"https://intervals.icu/api/v1/athlete/{athlete_id}/activities",
        headers=get_intervals_auth(api_key),
        params={"oldest": since}
    )

    response.raise_for_status()
    return response.json()


def download_fit(api_key, activity_id):
    url = f"https://intervals.icu/api/v1/activity/{activity_id}/fit-file"
    response = requests.get(url, headers=get_intervals_auth(api_key))
    response.raise_for_status()

    with open(f"/tmp/{activity_id}.fit", "wb") as f:
        f.write(response.content)

    return response.content

def get_activity_details(api_key, activity_id):
    url = f"https://intervals.icu/api/v1/activity/{activity_id}"
    response = requests.get(url, headers=get_intervals_auth(api_key))
    response.raise_for_status()
    return response.json()

def valid_activity(activity_details):
    from_wahoo = activity_details["source"].lower() == "wahoo"
    since = datetime.now(ZoneInfo(key='Etc/UTC')) - timedelta(hours=LOOKBACK_HOURS)
    sync_date = datetime.fromisoformat(activity_details["icu_sync_date"])
    in_range = sync_date > since
    return from_wahoo and in_range


def upload_to_garmin(fit_file):
    import garth
    from garth.exc import GarthHTTPError
    try:
        with open(fit_file, 'rb') as f:
            garth.client.upload(f)

        print("Upload successful")
    except GarthHTTPError as e:
        error_str = str(e)
        status_code = getattr(getattr(e, "response", None), "status_code", None)
        if status_code == 409 or "409" in error_str:
            print("Duplicate ignored.")
        elif status_code == 401 or "401" in error_str or "unauthorized" in error_str.lower():
            raise Exception("Garmin session expired. Run `uvx garth login` again.")
        else:
            raise

def lambda_handler(event, context):
    intervals_key = get_parameter("/cycling/intervals/api_key")
    athlete_id = get_parameter("/cycling/intervals/athlete_id")

    init_garmin_session()

    activities = get_intervals_activities(athlete_id, intervals_key)

    for activity in activities:
        activity_id = activity["id"]
        print(f"Processing activity {activity_id}")

        if valid_activity(get_activity_details(intervals_key, activity_id)):
            print(f"Activity {activity_id} is valid, downloading FIT file...")
            fit_data = download_fit(intervals_key, activity_id)
            upload_to_garmin(f"/tmp/{activity_id}.fit")

    return {"status": "complete"}
