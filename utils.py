import base64
import calendar
import json
import math
from pathlib import Path
from io import BytesIO
import re
import time
import traceback
from PIL import Image, ImageFont, ImageDraw
from hoshino import R, aiorequests
from . import db
from hoshino.typing import Message
from .config import get_config
from base64 import b64decode, b64encode
from . import easygradio

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

def pic2cq(pic: str):
    """
    图片转CQ码
    pic: base64编码的图片
    """
    return f"[CQ:image,file={pic}]"

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
    return pic2cq(pic2b64(i)) # 图片转base64并转cq码


def key_worlds_removal(msg):
    """
    replace() 方法用另一个指定的短语替换一个指定的短语。
    如果未指定其他内容，则将替换所有出现的指定短语。
    """
    return msg.replace('以图生图', '').replace('以图绘图', '')


def isContainChinese(string: str) -> bool:
    for char in string:
        if ('\u4e00' <= char <= '\u9fa5'):
            return True
    return False


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
            url = (f"{api_url}/got_image") + (f"?tags={tags}")+ (f"&token={token}")
            response = await aiorequests.get(url, timeout=180)
        else:
            url = (f"{api_url}/got_image2image") + (f"?tags={tags}") +(f"&shape={shape}")+(f"&strength={strength}")+(f"&token={token}")
            response = await aiorequests.post(url,data=b64encode(b_io.getvalue()), timeout=180) # 上传图片
        imgdata = await response.content # 获取图片的二进制数据
        if len(imgdata) < 5000:
            error_msg = "token冷却中~"
    except Exception as e:
        resultmes = f"请求超时：{type(e)}"
        return resultmes, error_msg
    try:
        msg=""
        msgdata = json.loads(re.findall(r'{"steps".+?}',str(imgdata))[0]) # 使用r''来声明原始字符串，避免转义
        msg = f'\nseed:{msgdata["seed"]}   scale:{msgdata["scale"]}'
    except Exception as e:
        traceback.print_exc()
        error_msg = f"获取图片信息失败，服务器未返回数据：{type(e)}"
        return resultmes, error_msg
    try:
        img = Image.open(BytesIO(imgdata)).convert("RGB") # 载入图片并转换色彩空间为RGB
        imgmes = pic2b64(img) # 将图片转为base64
    except Exception as e:
        error_msg += f"处理图像失败：{type(e)}"
        return resultmes,error_msg
    resultmes = f"{pic2cq(imgmes)}{msg}\ntags:{tags}" # pic2cq(imgmes)将图片转为CQ码
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
    error_msg = ""
    result_msg = ""
    url = get_config("image4x", "Real-CUGAN-api") # 获取api地址
    b_io = BytesIO()
    image.save(b_io, format='JPEG', quality=90)
    json_data = ["data:image/jpeg;base64," + base64.b64encode(b_io.getvalue()).decode(), modelname, 2]
    result_msg, error_msg = await easygradio.predict_push(url, json_data)
    if error_msg:
        return None,error_msg
    result_img = b64decode(result_msg.split("base64,")[1]) # 获取base64并解码为图片
    result_img = Image.open(BytesIO(result_img)).convert("RGB") # 载入图片并转换色彩空间为RGB
    result_img = pic2cq(pic2b64(result_img)) # 图片转base64并转cq码
    return result_img, error_msg

async def get_Real_ESRGAN(img):
    '''
    Real-ESRGAN图片超分
    '''
    error_msg = ""
    result_msg = ""
    url = get_config("image4x", "Real-ESRGAN-api") # 获取api地址
    b_io = BytesIO()
    img.save(b_io, format='JPEG', quality=90)
    json_data = ["data:image/jpeg;base64," + base64.b64encode(b_io.getvalue()).decode(), "anime"]
    result_msg, error_msg = await easygradio.predict_push(url, json_data)
    if error_msg:
        return None,error_msg
    result_img = b64decode(result_msg.split("base64,")[1]) # 获取base64并解码为图片
    result_img = Image.open(BytesIO(result_img)).convert("RGB") # 载入图片并转换色彩空间为RGB
    result_img = pic2cq(pic2b64(result_img)) # 图片转base64并转cq码
    return result_img, error_msg


async def cartoonization(image: Image, max_try=60):
    '''
    图片卡通化
    '''
    error_msg = ""
    result_msg = ""
    url = get_config('pic_tools', 'img2anime_api')
    b_io = BytesIO()
    image.save(b_io, format='JPEG', quality=90)
    json_data = ["data:image/jpeg;base64," + base64.b64encode(b_io.getvalue()).decode()]
    result_msg, error_msg = await easygradio.quene_push_(url, json_data) #获取结果 resj['data']['data']
    if error_msg:
        return None,error_msg
    result_img = b64decode(result_msg[0].split("base64,")[1]) # 截取列表中的第2项到结尾获取base64并解码为图片
    result_img = Image.open(BytesIO(result_img)).convert("RGB") # 载入图片并转换色彩空间为RGB
    result_img = pic2cq(pic2b64(result_img)) # 图片转base64并转cq码
    return result_img, error_msg
    

async def get_tags(image: Image, max_try=60):
    '''
    DeepDanbooru图片鉴赏
    分析图片并获取对应tags
    置信度取70%以上
    '''
    result_msg = ""
    error_msg = ""
    url = get_config('pic_tools', 'img2tag_api')
    b_io = BytesIO()
    image.save(b_io, format='JPEG', quality=90)
    json_data = ["data:image/jpeg;base64," + base64.b64encode(b_io.getvalue()).decode(),0.7] # 阈值0.7，即取置信度70%以上的tag
    result_msg, error_msg = await easygradio.quene_push_(url, json_data) #获取结果 resj['data']['data']
    if error_msg:
        return None,error_msg
    return result_msg[1], error_msg

async def get_imgdata_magic(tags):#way=1时为get，way=0时为post
    error_msg =""  #报错信息
    result_msg = ""

    # 设置API
    api_url = get_config('NovelAI', 'api')
    token = get_config('NovelAI', 'token')
    try:
        url = (f"{api_url}/got_image") + (f"?tags={tags}")+ (f"&token={token}")
        imgdata = await (await aiorequests.get(url, timeout=180)).content
        if len(imgdata) < 5000:
            error_msg = "token冷却中~"
    except Exception as e:
        error_msg = f"请求超时：{type(e)}"
    img = Image.open(BytesIO(imgdata)).convert("RGB")
    result_msg = pic2cq(pic2b64(img)) # 图片转base64并转cq码
    return result_msg,error_msg

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
    resultmes = pic2cq(imgmes) # 将图片转为CQ码
    return resultmes