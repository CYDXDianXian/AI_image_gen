from base64 import b64encode
from io import BytesIO
import json
import re
import traceback
from PIL import Image
from .import limit, db
from .youdao import tag_trans
from .baidu import tag_baiduTrans
from .config import get_config, get_group_config
from .translator_lite.apis import baidu, youdao
from .utils import isContainChinese

async def process_tags(gid,uid,tags):
    '''
    录入数据库，翻译，过滤屏蔽词
    '''
    error_msg ="" #报错信息
    tags_guolv="" #过滤词信息
    
    add_db = get_group_config(gid, 'add_db')
    trans = get_group_config(gid, 'trans')
    limit_word = get_group_config(gid, 'limit_word')
    arrange_tags = get_group_config(gid, 'arrange_tags')
    youdao_trans = get_config('youdao', 'youdao_trans')
    baidu_trans = get_config('baidu', 'baidu_trans')
    
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
            traceback.print_exc()
    if trans == True:
        if baidu_trans == True:
            try:
                msg = re.split("([&])", tags ,1)
                if get_config('baidu', 'baidu_appid'):
                    msg[0] = await tag_baiduTrans(msg[0]) # 百度翻译
                elif isContainChinese(msg[0]):
                    msg[0] = await baidu(msg[0])
                tags = "".join(msg)
            except Exception as e:
                error_msg = "翻译失败"
                traceback.print_exc()
        elif youdao_trans == True:
            try:
                msg = re.split("([&])", tags ,1)
                if get_config('youdao', 'app_id'):
                    msg[0] = await tag_trans(msg[0]) # 有道翻译
                elif isContainChinese(msg[0]):
                    msg[0] = await youdao(msg[0])
                tags = "".join(msg)
            except Exception as e:
                error_msg = "翻译失败"
                traceback.print_exc()
        else:
            error_msg = "翻译失败，百度翻译和有道翻译服务均未开启，请开启服务后重试"
    if limit_word == True:
        try:
            tags,tags_guolv = limit.guolv(tags)#过滤屏蔽词
        except Exception as e:
            error_msg = "过滤屏蔽词失败"
            traceback.print_exc()
    if arrange_tags == True:
        try:
            taglist = re.split(',|，',tags)
            while "" in taglist:
                taglist.remove("")#去除空元素
            tags = ",".join(taglist)
        except Exception as e:
            error_msg = "整理tags失败"
            traceback.print_exc()
    return tags,error_msg,tags_guolv

def process_img(data):
    error_msg ="" #报错信息
    msg = ""
    imgmes = ""
    try:
        msgdata = json.loads(re.findall('{"steps".+?}',str(data))[0])
        msg = f'\nseed:{msgdata["seed"]}   scale:{msgdata["scale"]}'
    except Exception as e:
        error_msg = "无法获取seed,请检测token是否失效"
        traceback.print_exc()
    try:
        img = Image.open(BytesIO(data)).convert("RGB")
        buffer = BytesIO()  # 创建缓存
        img.save(buffer, format="png")
        imgmes = 'base64://' + b64encode(buffer.getvalue()).decode()
    except Exception as e:
        error_msg = "处理图像失败"
        traceback.print_exc()
    return msg,imgmes,error_msg