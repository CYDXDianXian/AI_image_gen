from base64 import b64encode
import base64
from io import BytesIO
import json
import re
from PIL import Image, ImageDraw,ImageFont
from .import limit, db
from .youdao import tag_trans
from .config import get_config, get_group_config


def process_tags(gid,uid,tags,add_db=True,arrange_tags=True):
    '''
    录入数据库，翻译，过滤屏蔽词
    '''
    error_msg ="" #报错信息
    tags_guolu="" #过滤词信息
    
    # add_db = get_group_config(gid, 'add_db') # 有bug，先保持开启不变
    trans = get_group_config(gid, 'trans')
    limit_word = get_group_config(gid, 'limit_word')
    # arrange_tags = get_group_config(gid, 'arrange_tags')  # 有bug，先保持开启不变

    if add_db == True:
        try:
            msg = re.split('&',tags)[0]
            taglist = re.split(',|，',msg)
            while "" in taglist:
                taglist.remove("")#去除空元素
            for tag in taglist:
                db.add_xp_num(gid,uid,tag)
        except Exception as e:
            error_msg = "录入数据库失败"
    if trans == True:
        try:
            msg = re.split("([&])", tags ,1)
            msg[0] = tag_trans(msg[0])#有道翻译
            tags = "".join(msg)
        except Exception as e:
            error_msg = "翻译失败"
    if limit_word == True:
        try:
            tags,tags_guolu = limit.guolv(tags)#过滤屏蔽词
        except Exception as e:
            error_msg = "过滤屏蔽词失败"
    if arrange_tags == True:
        try:
            taglist = re.split(',|，',tags)
            while "" in taglist:
                taglist.remove("")#去除空元素
            tags = ",".join(taglist)
        except Exception as e:
            error_msg = "整理tags失败"
    return tags,error_msg,tags_guolu

def process_img(data):
    error_msg ="" #报错信息
    msg = ""
    imgmes = ""
    try:
        msgdata = json.loads(re.findall('{"steps".+?}',str(data))[0])
        msg = f'\nseed:{msgdata["seed"]}   scale:{msgdata["scale"]}'
    except Exception as e:
        error_msg = "无法获取seed,请检测token是否失效"
    try:
        img = Image.open(BytesIO(data)).convert("RGB")
        buffer = BytesIO()  # 创建缓存
        img.save(buffer, format="png")
        imgmes = 'base64://' + b64encode(buffer.getvalue()).decode()
    except Exception as e:
        error_msg = "处理图像失败"
    return msg,imgmes,error_msg

def img_make(msglist):
    msglist = msglist
    target = Image.new('RGB', (1920,1080),(255,255,255))
    i=0
    idlist,imglist,thumblist = [],[],[]
    for (a,b,c) in msglist:
        idlist.append(a)
        imglist.append(b)
        thumblist.append(c)
    for i in range(0,8):
        try:
            id = f"ID: {idlist[i]}" #图片ID
            thumb = f"点赞: {thumblist[i]}" #点赞数
            image_path= str(imglist[i]) #图片路径
        except:
            break
        region = Image.open(image_path)
        region = region.convert("RGB")
        region = region.resize((int(region.width/2),int(region.height/2)))
        font = ImageFont.truetype('C:\\WINDOWS\\Fonts\\simsun.ttc', 36)  # 设置字体和大小
        draw = ImageDraw.Draw(target)
        if i<4:
            target.paste(region,(80*(i+1)+384*i,50))
            draw.text((80*(i+1)+384*i+int(region.width/2)-130,80+region.height),id,font=font,fill = (0, 0, 0))
            draw.text((80*(i+1)+384*i+int(region.width/2)+10,80+region.height),thumb,font=font,fill = (0, 0, 0))
        if i>=4:
            target.paste(region,(80*(i-3)+384*(i-4),150+384))
            draw.text((80*(i-3)+384*(i-4)+int(region.width/2)-130,180+384+region.height),id,font=font,fill = (0, 0, 0))
            draw.text((80*(i-3)+384*(i-4)+int(region.width/2)+10,180+384+region.height),thumb,font=font,fill = (0, 0, 0))
        i+=1
    result_buffer = BytesIO()
    target.save(result_buffer, format='JPEG', quality=100) #质量影响图片大小
    imgmes = 'base64://' + base64.b64encode(result_buffer.getvalue()).decode()
    resultmes = f"[CQ:image,file={imgmes}]"
    return resultmes