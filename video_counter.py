from datetime import datetime
import time
import os
import cv2
import numpy
import requests
from gql import gql
from app import client, ROOT_DIR
from utils import image_hash_by_img, compare_hash
import hashlib


def run(counter, timeout):
    camera_path = counter["camera"]["url"]
    data_start = counter["dataStart"]
    data_start = counter["dataFinish"]
    frames = counter["frames"]
    width = 1280
    height = 720
    frame_to_recognize = []
    img_hash_to_recognize = []

    for frame in frames:
        if frame["isSimilar"]:
            resp = requests.get('http://localhost:4000/' + (frame["cameraFrame"]))
            image = numpy.asarray(bytearray(resp.content), dtype="uint8")
            frame_img = cv2.imdecode(image, cv2.IMREAD_COLOR)
            frame_to_recognize.append(frame_img)
    for it_frames_to_recognize in frame_to_recognize:
        # загружаем изображение и отображаем его
        (h, w) = it_frames_to_recognize.shape[:2]

        center = (w / 2, h / 2)

        # повернем изображение на 4 градуса
        M = cv2.getRotationMatrix2D(center, counter["camera"]["alignmentAngle"], 1.0)
        rotated_orig = cv2.warpAffine(it_frames_to_recognize, M, (w, h))

        cropped_orig = rotated_orig[counter["camera"]["trimTop1"]:counter["camera"]["trimBottom1"],
                       counter["camera"]["trimLeft1"]:counter["camera"]["trimRight1"]]

        img_hash_to_recognize.append(image_hash_by_img(cropped_orig))

    video_url = camera_path + "playlist.m3u8"
    pipe = cv2.VideoCapture(video_url)
    sum_of_all = 0

    last_frame_time = time.time() - 10
    delta_timeout = time.time() + timeout

    print("Counter ID:" + counter["id"] + " start at :" + datetime.now().time().strftime("%H:%M:%S"))

    while True:
        frame_id = int(round(pipe.get(1)))
        success, raw_image = pipe.read()

        if frame_id % 60 == 0:
            if success:
                if (time.time() - last_frame_time) > 10:
                    image = numpy.frombuffer(raw_image, dtype='uint8').reshape((height, width, 3))
                    (h, w) = image.shape[:2]
                    center = (w / 2, h / 2)
                    M = cv2.getRotationMatrix2D(center, counter["camera"]["alignmentAngle"], 1.0)
                    rotated = cv2.warpAffine(image, M, (w, h))
                    cropped = rotated[
                              counter["camera"]["trimTop1"]:counter["camera"]["trimBottom1"],
                              counter["camera"]["trimLeft1"]:counter["camera"]["trimRight1"]
                              ]

                    img_hash_video = image_hash_by_img(cropped)
                    diff_hash = compare_hash(img_hash_video, img_hash_to_recognize[0])

                    if diff_hash < 15:
                        now_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cv2.imwrite(os.path.join(ROOT_DIR, 'fake_frame/fake_frame_' + hashlib.md5((now_date_time + counter["id"]).encode()).hexdigest() + ".jpg"), raw_image)
                        file = {'file': open(os.path.join(ROOT_DIR, 'fake_frame/fake_frame_' + hashlib.md5((now_date_time + counter["id"]).encode()).hexdigest() + ".jpg"), 'rb')}
                        response = requests.post('http://localhost:4000/api/upload-file', files=file)
                        date_now = datetime.now().strftime("%Y-%m-%d")
                        time_now = datetime.now().strftime("%H:%M:%S")
                        mutation = gql('''
                            mutation{
                              counterCount(input:{
                                counterID: ''' + str(counter["id"]) + '''
                                frame: "''' + str(response.json()["path"]).replace("public/", "") + '''"
                                date: "''' + date_now + '''"
                                time: "''' + time_now + '''"
                              }){
                                id
                              }
                            }
                            ''')
                        client.execute(mutation)
                        sum_of_all += 1
                        last_frame_time = time.time()
            else:
                print("Ошибка захвата кадра")

        if time.time() > delta_timeout:
            break

    print("Counter ID:" + counter["id"] + " stop at : " + datetime.now().time().strftime("%H:%M:%S"))
    pipe.release()
