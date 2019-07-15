from flask import Flask, request, abort, render_template, send_file
import json
import requests
from google.cloud import storage
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, StickerMessage,
    ImageSendMessage
)

app = Flask(__name__)
access_token = '3yFDTvph2uKgKlNaGOeQRh3ir8xakFgFq\
    LWTQB8KhJ8ThVqwf83LKOBORTWyrtcCGD9jAiVu7ESJaHukqVp6oiLwnXGhMx+\
        v+GukGaNQLhKpuEb7zVktAPsTyhJZlAdiv/\
            CKmsFCrrwRpJFp0q9ZvAdB04t89/1O/w1cDnyilFU= '
line_bot_api = LineBotApi(access_token)

handler = WebhookHandler('6570a1b497e432c1e08a33d7853726b4')
BucketName = 'kohi_bot'


@app.route("/")
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
    app.logger.info("Request body: " + body)

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

    url = "https://api.line.me/v2/bot/message/"+event.message.id+"/content"
    headers = {
        'Authorization': "Bearer {}".format(access_token),
    }
    response = requests.request("GET", url, headers=headers)
    with open('/home/thcshiya/linebot_img/' +
              event.message.id+'.jpeg', 'wb') as fd:
        fd.write(response.content)

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BucketName)
    blob = bucket.blob(event.message.id+'.jpeg')
    try:
        blob.upload_from_filename(
            '/home/thcshiya/linebot_img/'+event.message.id+'.jpeg'
        )
    except Exception as identifier:
        print(identifier)
    url_line = blob.public_url
    line_bot_api.reply_message(
        event.reply_token, ImageSendMessage(
            original_content_url=url_line,
            preview_image_url=url_line))


@handler.add(MessageEvent, message=StickerMessage)
def sticker_msg(event):
    print(event)

    line_bot_api.reply_message(
        event.reply_token, StickerMessage(event.message.id,
                                          package_id=event.message.package_id,
                                          sticker_id=event.message.sticker_id))


if __name__ == "__main__":

    app.run("127.0.0.1", 5000, debug=False, ssl_context='adhoc')
