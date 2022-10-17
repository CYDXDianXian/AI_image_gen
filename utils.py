import os
import base64
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from hoshino import aiorequests

fontpath = os.path.join(os.path.dirname(__file__), 'fonts/SourceHanSansCN-Medium.otf')


def text_to_image(text: str) -> Image.Image:
    font = ImageFont.truetype(fontpath, 24)
    padding = 10
    margin = 4
    text_list = text.split('\n')
    max_width = 0
    for text in text_list:
        w, h = font.getsize(text)
        max_width = max(max_width, w)
    wa = max_width + padding * 2
    ha = h * len(text_list) + margin * (len(text_list) - 1) + padding * 2
    i = Image.new('RGB', (wa, ha), color=(255, 255, 255))
    draw = ImageDraw.Draw(i)
    for j in range(len(text_list)):
        text = text_list[j]
        draw.text((padding, padding + j * (margin + h)), text, font=font, fill=(0, 0, 0))
    return i


def image_to_base64(img: Image.Image, format='PNG') -> str:
    output_buffer = BytesIO()
    img.save(output_buffer, format)
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data).decode()
    return 'base64://' + base64_str


def get_image_hash(content):
    ls_f = base64.b64encode(BytesIO(content).read())
    imgdata = base64.b64decode(ls_f)
    pic_hash = hash(imgdata)
    return pic_hash


def key_worlds_removal(msg):
    return msg.replace('以图生图', '').replace('以图绘图', '')


async def get_image_and_msg(bot, ev):
    url = ''
    for i in ev.message:
        if i['type'] == 'image':
            url = i["data"]["url"]
    if url:
        resp = await aiorequests.get(url)
        resp_cont = await resp.content
        image = Image.open(BytesIO(resp_cont))
        return image, get_image_hash(resp_cont), ev.message.extract_plain_text().strip()
    else:
        msg_id = None
        for i in ev.message:
            if i.type == 'reply':
                msg_id = i['data']['id']
        if msg_id is not None:
            reply_msg = (await bot.get_msg(message_id=msg_id))['message']
            for i in reply_msg:
                if i['type'] == 'image':
                    url = i["data"]["url"]
            if url:
                resp = await aiorequests.get(url)
                resp_cont = await resp.content
                image = Image.open(BytesIO(resp_cont))
                return image, get_image_hash(resp_cont), ''.join(seg['data']['text'] for seg in reply_msg if seg['type'] == 'text')
    return None, None, None

