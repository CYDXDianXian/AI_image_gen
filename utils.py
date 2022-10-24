import asyncio
import base64
import calendar
import json
import math
from pathlib import Path
import random
from io import BytesIO
import re
import time
import traceback
import uuid
from PIL import Image, ImageFont, ImageDraw
from hoshino import R, aiorequests
from . import db
from hoshino.typing import Message, MessageSegment
from .config import get_config
from base64 import b64decode, b64encode

save_image_path = Path(R.img('AI_setu').path) # 图片保存在res/img/AI_setu目录下
Path(save_image_path).mkdir(parents = True, exist_ok = True) # 创建路径
fontpath = Path(__file__).parent / "fonts" / "SourceHanSansCN-Medium.otf" # 字体文件的路径

per_page_num = get_config("base", "per_page_num") # 获取每页图片数量

def pic2b64(pic: Image) -> str:
    '''
    图片转base64
    '''
    buf = BytesIO()
    pic.save(buf, format='JPEG', quality=90)
    base64_str = base64.b64encode(buf.getvalue()).decode()
    return 'base64://' + base64_str

def text_to_image(text: str) -> Image.Image:
    font = ImageFont.truetype(str(fontpath), 24) # Path是路径对象，必须转为str之后ImageFont才能读取
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
    return MessageSegment.image(pic2b64(i)) # 图片转base64并转cq码


def key_worlds_removal(msg):
    return msg.replace('以图生图', '').replace('以图绘图', '')


def isContainChinese(string: str) -> bool:
    for char in string:
        if ('\u4e00' <= char <= '\u9fa5'):
            return True
    return False


def generate_code(code_len=6):
    all_char = '0123456789qazwsxedcrfvtgbyhnujmikolp'
    index = len(all_char) - 1
    code = ''
    for _ in range(code_len):
        num = random.randint(0, index)
        code += all_char[num]
    return code


async def save_pic(image, pic_hash):
    error_msg = ""
    pic_dir = ""
    try:
        if db.get_pic_exist_hash(pic_hash): # 检查图片是否存在
            id = re.search(r"\d+", str(db.get_pic_id_hash(pic_hash))).group(0) # group(0) 返回匹配到的完整字符串
            error_msg = f"上传失败，ID为【{id}】号的图片已存在！"
            return pic_dir,error_msg
        datetime = calendar.timegm(time.gmtime())
        img_name = str(datetime)+'.jpg'
        pic_dir = save_image_path / img_name # 拼接图片路径
        image.save(pic_dir) # 以给定的文件名保存此图像。如果没有格式指定时，使用的格式由文件名确定
    except Exception as e:
        error_msg = "图片保存失败"
        traceback.print_exc()
        return pic_dir,error_msg
    return pic_dir,error_msg

async def check_pic_(gid,uid,msg,page):
    error_msg = ""
    num = page*per_page_num
    if msg == "本群":
        msglist = db.get_pic_list_group(gid,num)
    elif msg == "个人":
        msglist = db.get_pic_list_personal(uid,num)
    elif msg == "全部":
        msglist = db.get_pic_list_all(num)
    else:
        error_msg = "参数错误"
        return resultmes,error_msg
    if len(msglist) == 0:
        error_msg = f"无法找到{msg}图片信息"
        return resultmes,error_msg
    resultmes = f"您正在查看{msg}的第【{page}】页图片\n"
    resultmes += await img_make(msglist,page)
    return resultmes,error_msg

async def get_image_and_msg(bot, ev):
    url = ''
    for i in ev.message:
        if i['type'] == 'image':
            url = i["data"]["url"]
    if url:
        resp = await aiorequests.get(url)
        resp_cont = await resp.content
        image = Image.open(BytesIO(resp_cont)).convert("RGB") # 载入图片并转换色彩空间为RGB
        return image, hash(resp_cont), ev.message.extract_plain_text().strip()
    else:
        msg_id = None
        for i in ev.message:
            if i['type'] == 'reply':
                msg_id = i['data']['id']
        if msg_id is not None:
            reply_msg = Message((await bot.get_msg(message_id=msg_id))['message']) # 将CQ码转为字典，以便提取消息内容
            for i in reply_msg:
                if i['type'] == 'image':
                    url = i['data']['url']
            if url:
                resp = await aiorequests.get(url)
                resp_cont = await resp.content

                image = Image.open(BytesIO(resp_cont)).convert("RGB") # 载入图片并转换色彩空间为RGB
                return image, hash(resp_cont), ''.join(seg['data']['text'] for seg in reply_msg if seg['type'] == 'text')
    return None, None, None

async def get_imgdata(tags,way=1,shape="Portrait",strength=get_config('NovelAI', 'strength'),b_io=None): # way=1时为get，way=0时为post
    error_msg =""  # 报错信息
    resultmes = ""

    # 设置API
    api_url = get_config('NovelAI', 'api')
    token = get_config('NovelAI', 'token')
    try:
        if way:
            url = (f"{api_url}got_image") + (f"?tags={tags}")+ (f"&token={token}")
            response = await aiorequests.get(url, timeout=180)
        else:
            url = (f"{api_url}got_image2image") + (f"?tags={tags}") +(f"&shape={shape}")+(f"&strength={strength}")+(f"&token={token}")
            response = await aiorequests.post(url,data=b64encode(b_io.getvalue()), timeout=180) # 上传图片
        imgdata = await response.content # 获取图片的二进制数据
        if len(imgdata) < 5000:
            error_msg = "token冷却中~"
    except Exception as e:
        error_msg = f"超时了~"
    i=999
    error_msg = ""
    try:
        msg=""
        msgdata = json.loads(re.findall(r'{"steps".+?}',str(imgdata))[0]) # 使用r''来声明原始字符串，避免转义
        msg = f'\nseed:{msgdata["seed"]}   scale:{msgdata["scale"]}'
    except Exception as e:
        traceback.print_exc()
        error_msg = f"获取图片信息失败，服务器未返回数据"
        return resultmes,error_msg
    try:
        img = Image.open(BytesIO(imgdata)).convert("RGB") # 载入图片并转换色彩空间为RGB
        imgmes = pic2b64(img) # 将图片转为base64
    except Exception as e:
        error_msg += f"处理图像失败：{e}"
        return resultmes,error_msg
    resultmes = f"{MessageSegment.image(imgmes)}{msg}\ntags:{tags}" # MessageSegment.image(imgmes)将图片转为CQ码
    return resultmes,error_msg

async def get_xp_list_(msg,gid,uid):
    error_msg =""  #报错信息
    resultmes = ""
    if msg == "本群":
        xp_list = db.get_xp_list_group(gid)
    elif msg == "个人":
        xp_list = db.get_xp_list_personal(gid,uid)
    else:
        error_msg = "参数错误，请输入本群xp排行或个人xp排行"
        return resultmes,error_msg
    resultmes = f'{msg}的XP排行榜为：\n'
    if len(xp_list)>0:
        for xpinfo in xp_list:
            keyword, num = xpinfo
            resultmes += f'关键词：{keyword} || 次数：{num}\n'
    else:
        resultmes = f'暂无{msg}的XP信息'
    return resultmes,error_msg

async def get_xp_pic_(msg,gid,uid):
    error_msg =""  #报错信息
    resultmes = ""
    if msg == "本群":
        xp_list = db.get_xp_list_kwd_group(gid)
    elif msg == "个人":
        xp_list = db.get_xp_list_kwd_personal(gid,uid)
    else:
        error_msg = "参数错误，请输入本群xp缝合或个人xp缝合"
        return resultmes,error_msg
    if len(xp_list)>0:
        keywordlist = []
        for (a,) in xp_list:
            keywordlist.append(a)
        tags = (',').join(keywordlist)
        resultmes = tags
    else:
        error_msg = f'暂无{msg}的XP信息'
    return resultmes,error_msg

async def get_Real_CUGAN(image, modelname):
    '''
    Real-CUGAN图片超分

    来构造请求并获取返回的重建后的图像

    Args:
        json_data (dict): 对图片编码后的数据

    Returns:
        str: 返回的json格式数据
    '''
    api = get_config("image4x", "Real-CUGAN-api") # 获取api地址
    b_io = BytesIO()
    image.save(b_io, format='JPEG', quality=90)
    i_b64 = "data:image/jpeg;base64," + base64.b64encode(b_io.getvalue()).decode()
    params = {
        "data": [
            i_b64,
            modelname,
            2
            ]
        }
    res = await (await aiorequests.post(url=api, json=params)).json()
    if "data" in res:
        result_img = b64decode(''.join(res['data'][0].split(',')[1:])) # 截取列表中的第2项到结尾获取base64并解码为图片
        result_img = Image.open(BytesIO(result_img)).convert("RGB") # 载入图片并转换色彩空间为RGB
        return MessageSegment.image(pic2b64(result_img)) # 图片转base64并转cq码
    else:
        return None

async def get_Real_ESRGAN(img):
    '''
    Real-ESRGAN图片超分
    '''
    url_predict = get_config("image4x", "Real-ESRGAN-api") # 获取api地址
    b_io = BytesIO()
    img.save(b_io, format='JPEG', quality=90)
    i_b64 = "data:image/jpeg;base64," + str(b64encode(b_io.getvalue()))[2:-1]
    params = {
        "fn_index": 0,
        "data": [
            i_b64,
            "anime"
        ],
        "session_hash": generate_code(11)
    }
    res = await (await aiorequests.post(url_predict, json=params)).json()
    if 'data' in res:
        result_img = b64decode(''.join(res['data'][0].split(',')[1:])) # 截取列表中的第2项到结尾获取base64并解码为图片
        result_img = Image.open(BytesIO(result_img)).convert("RGB") # 载入图片并转换色彩空间为RGB
        return MessageSegment.image(pic2b64(result_img)) # 图片转base64并转cq码
    else:
        return None


async def quene_fetch_(url,_hash,max_try):
    #报错信息
    result_msg = ""
    error_msg = ""
    i = 0
    url_status = f'{url}/api/queue/status/'
    while i< max_try :
        i+=1
        resj =  await (await aiorequests.post(url_status, json={'hash': _hash})).json()
        await asyncio.sleep(1)#等待1秒
        if resj['status'] == 'PENDING' or resj['status'] == 'QUEUED':
            error_msg = f"状态码:{resj['status']} 原因:超时了捏~"
            continue
        elif resj['status'] == 'COMPLETE':
            error_msg = ""
            #print(resj['data']['data'])
            result_msg = resj['data']['data'] #获取结果 resj['data']['data']
            return result_msg,error_msg
        else:
            error_msg = f"状态码:{resj['status']} 失败原因:{resj['data']}"
            return result_msg,error_msg


async def cartoonization(image=Image, max_try=60):
    '''
    图片卡通化
    '''
    error_msg = ""
    result_msg = ""
    url = "https://hf.space/embed/hylee/White-box-Cartoonization"
    b_io = BytesIO()
    image.save(b_io, format='JPEG', quality=90)
    if error_msg != "":
        return result_msg,error_msg
    json_data = ["data:image/jpeg;base64," + base64.b64encode(b_io.getvalue()).decode()]
    url_push = f'{url}/api/queue/push/'
    json = {
        "fn_index": 0,
        "data": json_data,
        "session_hash": str(uuid.uuid1()),
        "action": "predict"
    }
    try:
        _hash = (await(await aiorequests.post(url_push, json=json)).json())['hash'] #获取当前任务的hash
    except Exception as e:
        error_msg = f"尝试排队 失败原因:{e}"
        return result_msg,error_msg
    result_msg,error_msg = await quene_fetch_(url,_hash,max_try) #获取结果 resj['data']['data'][0]
    if error_msg != "":
        return None,error_msg
    result_msg = result_msg[0]
    result_img = base64.b64decode(''.join(result_msg.split(',')[1:])) # 截取列表中的第2项到结尾获取base64并解码为图片
    result_img = Image.open(BytesIO(result_img)).convert("RGB") # 载入图片并转换色彩空间为RGB
    pic2b64(result_img)
    result_msg = MessageSegment.image(pic2b64(result_img)) # 图片转base64并转cq码
    return result_msg,error_msg
    

async def get_tags(image=Image,max_try=60):
    url = "https://hf.space/embed/NoCrypt/DeepDanbooru_string"
    result_msg = ""
    error_msg = ""
    url_push = f'{url}/api/queue/push/'
    b_io = BytesIO()
    image.save(b_io, format='JPEG', quality=90)
    json_data = ["data:image/jpeg;base64," + base64.b64encode(b_io.getvalue()).decode(),0.7] # 阈值0.7，即取置信度70%以上的tag
    json = {
        "fn_index": 0,
        "data": json_data,
        "session_hash": str(uuid.uuid1()),
        "action": "predict"
    }
    try:
        _hash = (await(await aiorequests.post(url_push, json=json)).json())['hash'] #获取当前任务的hash
    except Exception as e:
        error_msg = f"尝试排队 失败原因:{e}"
        return result_msg,error_msg
    result_msg,error_msg = await quene_fetch_(url,_hash,max_try) #获取结果 resj['data']['data']
    return result_msg[1], error_msg

async def img_make(msglist,page = 1):
    num = len(msglist)
    max_row = math.ceil(num/4)
    target = Image.new('RGB', (1920,512*max_row),(255,255,255))
    page = page - 1
    idlist,imglist,thumblist = [],[],[]
    for (a,b,c) in msglist:
        idlist.append(a)
        imglist.append(b)
        thumblist.append(c)
    for index in range(0+(page*per_page_num),per_page_num+(page*per_page_num)):
        try:
            id = f"ID: {idlist[index]}" #图片ID
            thumb = f"点赞: {thumblist[index]}" #点赞数
            image_path= str(imglist[index]) #图片路径
        except:
            break
        region = Image.open(image_path)
        region = region.convert("RGB")
        region = region.resize((int(region.width/2),int(region.height/2)))
        font = ImageFont.truetype(str(fontpath), 36)  # 设置字体和大小
        draw = ImageDraw.Draw(target)
        row = math.ceil((index+1)/4)
        column= (index+1)%4+1
        target.paste(region,(80*column+384*(column-1),50+100*(row-1)+384*(row-1)))
        draw.text((80*column+384*(column-1)+int(region.width/2)-90,80+100*(row-1)+384*(row-1)+region.height),id,font=font,fill = (0, 0, 0))
        draw.text((80*column+384*(column-1)+int(region.width/2)+20,80+100*(row-1)+384*(row-1)+region.height),thumb,font=font,fill = (0, 0, 0))
    imgmes = pic2b64(target) # 将图片转为base64
    resultmes = MessageSegment.image(imgmes) # 将图片转为CQ码
    return resultmes