import json
import os

import cv2
import requests
from gql import gql

from app import client, ROOT_DIR


def recognition(input):
    frame_data = json.loads(input)

    pipe = cv2.VideoCapture(frame_data["camera"]["url"] + "playlist.m3u8")
    frame_count = 0

    while frame_count < 40:
        frame_id = int(round(pipe.get(1)))
        success, raw_image = pipe.read()

        if success:
            if frame_id % 60 == 0:
                cv2.imwrite(os.path.join(ROOT_DIR, "recognized_frames_img/frame"+str(frame_data["video"]["name"])+".jpg"), raw_image)
                file = {"file": open(os.path.join(ROOT_DIR, "recognized_frames_img/frame"+str(frame_data["video"]["name"])+".jpg"), "rb")}
                response = requests.post("http://localhost:4000/api/upload-file", files=file)
                mutation = gql('''
                 mutation{
                   counterFrame(input:{
                     counterID:"''' + str(frame_data["id"]) + '''"
                     videoFrame:"''' + str(frame_data["video"]["fragments"][0]["picture"]["path"]) + '''"
                     cameraFrame:"''' + str(response.json()["path"]).replace("public/", "") + '''"
                   }){
                     id
                   }
                 }
                ''')
                client.execute(mutation)
                frame_count += 1
        else:
            print("error")