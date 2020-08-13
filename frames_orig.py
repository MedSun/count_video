import json
import os
import cv2
import requests
from app import ROOT_DIR


def frames_from_video(res):
    response = json.loads(res)

    video_name = response["video_name"]
    video_file = response["video_file"]

    video_cap = cv2.VideoCapture(video_file)
    success, image = video_cap.read()

    if success:
        path = os.path.join(ROOT_DIR, 'frames_orig_images/' + video_name + '.jpg')

        cv2.imwrite(path, image)
        file = {'file': open(path, "rb")}
        response = requests.post("http://localhost:4000/api/upload-file", files=file)

        return json.dumps({"pic": response.json()["path"]})
    else:
        print("Ошибка при создании опорного кадра для ролика " + video_name)
        return json.dumps("")