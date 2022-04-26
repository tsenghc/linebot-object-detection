import json
import os
import subprocess
import sys
import time
import yolov3_imgdetection
import cv2
import numpy as np
import requests
from flask import Flask, abort, render_template, request, send_file
from google.cloud import storage
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (ImageMessage, ImageSendMessage, MessageEvent,
                            StickerMessage, TextMessage, TextSendMessage)

app = Flask(__name__)
access_token = ''
line_bot_api = LineBotApi(access_token)

handler = WebhookHandler('')
BucketName = 'kohi_bot'


@app.route("/", methods=['POST'])
def hello():
    return "BOT:Hello HAHAHA!"


@app.route("/linebotimg")
def img():
    return "BOT:IMG WOW!"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your \
            channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def text_msg(event):
    print(event)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


@handler.add(MessageEvent, message=ImageMessage)
def img_msg(event):
    print(event)
    imgpath = "/home/thcshiya/linebot_img/"
    url = "https://api.line.me/v2/bot/message/"+event.message.id+"/content"
    headers = {
        'Authorization': "Bearer {}".format(access_token),
    }
    response = requests.request("GET", url, headers=headers)
    with open(imgpath + event.message.id+'.jpeg', 'wb') as fd:
        fd.write(response.content)
        print("GetIMG Done!")

    try:
        count = 0
        if os.path.isfile(imgpath + event.message.id+'.jpeg'):
            detect(imgpath+event.message.id+'.jpeg')
            while not os.path.isfile(imgpath + event.message.id+'_yolo.jpeg'):
                time.sleep(0.05)
                count += 1
                if count >= 100:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="detec overtime!!!"))
                    print("detec overtime!!!")
                    raise Exception
            print("detection Done!")
        else:
            print("fall")
    except Exception as identifier:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=identifier))
        print(identifier)

    try:
        detected_img_url = str(uploadimg(event.message.id,
                                         imgpath, BucketName))
        print(detected_img_url)
    except Exception as identifier:
        print(identifier)

    try:
        userid = json.loads(str(event))["source"]["userId"]
        print(userid)
        line_bot_api.push_message(userid, ImageSendMessage(
            original_content_url=detected_img_url,
            preview_image_url=detected_img_url))

    except Exception as identifier:
        print(identifier)


def detect(img_path):
    print("detection start!")
    yolo_weight = 'yolov3/yolov3.weights'
    yolo_classes = 'yolov3/coco.names'
    yolo_config = 'yolov3/yolov3.cfg'
    inpHeight = 416
    inpWidth = 416
    yolov3 = yolov3_imgdetection.yolo_detection(yolo_weight,
                                                yolo_classes,
                                                yolo_config,
                                                inpWidth,
                                                inpHeight)
    yolov3.detector(img_path, False, True)


def uploadimg(msgid, img_path, bucket):
    print("uploading....")
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket)
    blob = bucket.blob(msgid+'_yolo.jpeg')
    try:
        blob.upload_from_filename(
            img_path+msgid+'_yolo.jpeg'
        )
        print("detected upload Done!")
        url_line = blob.public_url
        return url_line
    except Exception as identifier:
        print(identifier)


@handler.add(MessageEvent, message=StickerMessage)
def sticker_msg(event):
    print(event)

    line_bot_api.reply_message(
        event.reply_token, StickerMessage(event.message.id,
                                          package_id=event.message.package_id,
                                          sticker_id=event.message.sticker_id))


if __name__ == "__main__":

    app.run("127.0.0.1", 5000, debug=True, ssl_context='adhoc')
