import atexit
import json
import os
import threading
import time
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from apscheduler.schedulers.background import BackgroundScheduler

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
client = Client(transport=RequestsHTTPTransport(url='http://localhost:4000/graphql'))

import frames_orig
import video_recognition
from video_counter import run as video_counter_run

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return "AI rest api server."


@app.route('/api')
def api_guid():
    return 'Guid.'


@app.route('/api/frames_orig', methods=['POST'])
def api_frames_orig():
    if request.method == 'POST':
        video_orig = request.get_data()
        response = frames_orig.frames_from_video(video_orig)
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        date_time = now.strftime("%Y-%m-%d %H:%M:%S")
        f = open(os.path.join(ROOT_DIR, 'frames_orig_logs/log-' + date + '.log'), 'a+', encoding='utf-8')
        f.write(date_time + '\n' + 'REQUEST:  ' + request.get_data(cache=True, as_text=True,
                                                                   parse_form_data=False) + '\n' + 'RESPONSE: ' + str(
            response) + '\n\n\n')
        f.close()

        return response


@app.route('/api/video_recognition', methods=['POST'])
def api_video_recognition():
    if request.method == 'POST':
        video_orig = request.get_data()
        video_recognition.recognition(video_orig)
        response = json.dumps(True)
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        date_time = now.strftime("%Y-%m-%d %H:%M:%S")
        f = open(os.path.join(ROOT_DIR, 'video_recognition_logs/log-' + date + '.log'), 'a+', encoding='utf-8')
        f.write(date_time + '\n' + 'REQUEST:  ' + request.get_data(cache=True, as_text=True,
                                                                   parse_form_data=False) + '\n' + 'RESPONSE: ' + str(
            response) + '\n\n\n')
        f.close()
        return response


def print_thread(n):
    print("Start thread #" + str(n) + " : " + datetime.now().time().strftime("%H:%M:%S"))
    timeout = time.time() + 5
    while True:
        if time.time() > timeout:
            print("Stop thread #" + str(n) + " : " + datetime.now().time().strftime("%H:%M:%S"))
            break


def run_counter(time_out_thread):
    counters_query = gql('''
    {
      counters {
          active
          camera {
            active
            address
            alignmentAngle
            createdAt
            id
            side
            srcID
            trimBottom1
            trimBottom2
            trimLeft1
            trimLeft2
            trimRight1
            trimRight2
            trimTop1
            trimTop2
            updatedAt
            url
          }
          count{
            active
            createdAt
            date
            id
            frame
            time
            updatedAt
          }
          createdAt
          creator {
            id
            name
            avatar
            active
          }
          dataFinish
          dataStart
          frames {
            active
            cameraFrame
            createdAt
            id
            isSimilar
            updatedAt
            videoFrame
          }
          id
          updatedAt
          video {
            id
            name
            fragments {
              id
              picture {
                id
                path
                active
              }
              active
            }
            active
          }
        }
    }
    ''')
    counters = client.execute(counters_query)["counters"]
    for counter in counters:
        is_similar = False
        for frame in counter["frames"]:
            if frame["isSimilar"]:
                is_similar = True
        if is_similar:
            counter_thread = threading.Thread(target=video_counter_run, args=(counter,time_out_thread,))
            counter_thread.start()


time_out = 30
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(run_counter, 'interval', seconds=time_out, args=((time_out-5), ))


if __name__ == "__main__":
    scheduler.start()
    app.run(host='0.0.0.0')
