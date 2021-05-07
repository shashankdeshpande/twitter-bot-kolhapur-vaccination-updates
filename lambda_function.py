import os
import json
import pytz
import tweepy
import requests
from datetime import datetime
from collections import OrderedDict

def tweepy_auth():
    CONSUMER_KEY = os.environ['TWITTER_CONSUMER_KEY']
    CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']
    ACCESS_TOKEN = os.environ['TWITTER_ACCESS_TOKEN']
    ACCESS_TOKEN_SECRET = os.environ['TWITTER_ACCESS_TOKEN_SECRET']
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    t_api = tweepy.API(auth)
    return t_api

def get_notified_sids():
    try:
        with open("/tmp/notified_sids.json") as f:
            sids = json.load(f)
    except:
        sids = []
    return sids

def save_notified_sids(sids):
    with open("/tmp/notified_sids.json", "w") as f:
        json.dump(sids, f, indent=4)

def get_vaccine_availability():
    data = []
    try:
        current_date = datetime.now(pytz.timezone('Asia/Calcutta'))
        current_date = current_date.strftime("%d-%m-%Y")
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        url = f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id=371&date={current_date}"
        resp = requests.get(url, headers=headers)
        resp = resp.json()['centers']

        for center in resp:
            for session in center['sessions']:
                if session['available_capacity'] and session["min_age_limit"] == 18:
                    msg = [
                            "#VaccineFor18Plus #KolhapurVaccineUpdate",
                            f"Center: {center['name']}, {center['address']} - {center['pincode']}",
                            f"Vaccine: {session['vaccine']}", 
                            f"Available Capacity: {session['available_capacity']}",
                            f"Date: {session['date']}",
                            "\n",
                            "Please refer https://www.cowin.gov.in for details.",
                            "#Unite2FightCorona #IndiaFightsCorona"
                        ]
                    session['msg'] = "\n".join(msg)
                    data.append(session)

        data = sorted(data, key=lambda x: (datetime.strptime(x["date"], "%d-%m-%Y"), - x["available_capacity"]))
    except Exception as e:
        print(e)
    return data

def post_tweets(data):
    t_api = tweepy_auth()
    sids = get_notified_sids()
    for each in data:
        if each['session_id'] not in sids:
            t_api.update_status(each['msg'])
            sids.append(each['session_id'])
    save_notified_sids(sids)

def lambda_handler(event, context):
    data = get_vaccine_availability()
    post_tweets(data)
    return {
        'statusCode': 200,
        'body': json.dumps(f'Successful..!!')
    }
