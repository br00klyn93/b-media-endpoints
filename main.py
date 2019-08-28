import requests
import datetime
import calendar
from flask import Flask
from flask import request
from flask import redirect
from flask import render_template
import json

app = Flask(__name__)

today = datetime.datetime.today().weekday()

@app.route('/')
def main():
    # Just redirect to homepage until it posts to authed
    return redirect("https://localhost:4443/", code=302)

@app.route('/auth_complete', methods=["POST"])
def authed():
    name = request.form["name"]
    new_token = request.form["access_token"]

    a_dict = {
        "optimal_time": optimal_time(new_token, name),
        "followers": get_stats("followers", new_token, name),
        "views_last": get_stats("views_last", new_token, name),
        "todays_imp": get_stats("todays_imp", new_token, name)
    }
    return a_dict

def optimal_time(token, name):
    r = requests.get("https://graph.facebook.com/v4.0/me/accounts?access_token="+str(token))
    f = r.json()

    for i in f["data"]:
        if i["name"] == name:
            n = requests.get("https://graph.facebook.com/v4.0/"+i["id"]+"?fields=instagram_business_account&access_token="+str(token))
            sec = n.json()

            # Setting up the period (aka two weeks ago) to search through
            start_date = 0
            end_date = 0

            start_date = (datetime.datetime.now() - datetime.timedelta(days=today)) - datetime.timedelta(days=14)
            start_date = start_date.replace(hour=00, minute=00,second=00)
            end_date = start_date + datetime.timedelta(days=7)
            end_date = end_date.replace(hour=23, minute=00,second=00)

            j = requests.get("https://graph.facebook.com/v4.0/"+sec["instagram_business_account"]["id"]+"/insights?metric=online_followers&period=lifetime&since="+str(start_date)+"&until="+str(end_date)+"&access_token="+str(token))

            fin = j.json()

            hours_day = []
            views = []

            days_fin = []
            hours = 0

            for days in fin["data"][0]["values"]:
                for times in days["value"]:
                    if hours <= 23:
                        hours_day.append(times)
                        views.append(days["value"][times])
                        hours+=1
                    else:
                        max = 0
                        first = True
                        for i in range(len(views)):
                            if first:
                                max = views[i]
                                first = False
                            else:
                                if views[i] > max:
                                    max = views[i]

                        temp = views.index(max)
                        days_fin.append(hours_day[temp])
                        views = []
                        hours_day = []
                        max = 0
                        temp = 0
                        hours = 0

            print(days_fin[5])
            return days_fin[5]

def get_stats(option, token, name):
    r = requests.get("https://graph.facebook.com/v4.0/me/accounts?access_token="+str(token))
    f = r.json()

    for i in f["data"]:
        if i["name"] == name:
            n = requests.get("https://graph.facebook.com/v4.0/"+i["id"]+"?fields=instagram_business_account&access_token="+str(token))
            sec = n.json()
    id = sec["instagram_business_account"]["id"]

    if option == "followers":
        z = requests.get("https://graph.facebook.com/v4.0/"+id+"?fields=business_discovery.username(brooklyn.mclaury){followers_count,media_count}&access_token="+str(token))
        print(z.json()["business_discovery"]["followers_count"])
        return z.json()["business_discovery"]["followers_count"]

    if option == "views_last":
        z = requests.get("https://graph.facebook.com/v4.0/"+id+"/media?access_token="+str(token))
        # print(z.json())
        recent_id = z.json()["data"][0]["id"]

        # print(recent_id)

        # print(recent_id)

        x = requests.get("https://graph.facebook.com/v4.0/"+str(recent_id)+"/insights?metric=impressions&period=lifetime&access_token="+str(token))
        # print(x.json()["data"]["values"]["value"])
        print(x.json()["data"][0]["values"][0]["value"])
        return x.json()["data"][0]["values"][0]["value"]

    if option == "todays_imp":
        z = requests.get("https://graph.facebook.com/v4.0/"+str(id)+"/insights?metric=impressions&period=day&access_token="+str(token))
        # print(z.json())
        # print(x.json()["data"]["values"]["value"])
        print(z.json()["data"][0]["values"][0]["value"] + z.json()["data"][0]["values"][1]["value"])
        return z.json()["data"][0]["values"][0]["value"] + z.json()["data"][0]["values"][1]["value"]

if __name__ == "__main__":
    app.run("0.0.0.0",port=5000)
