import os
import sqlite3
import traceback
import requests
import hoshino
from hoshino.typing import CQEvent
import base64
import re
import json
from hoshino import Service, aiorequests, priv
import io
from PIL import Image

sv_help = '''
注：+ 号不用输入
[ai绘图/生成涩图+tag] 关键词仅支持英文，用逗号隔开
[以图绘图/以图生图+tag+图片] 注意图片尽量长宽都在765像素以下，不然会被狠狠地压缩
[我的xp/我的XP] 查询你使用的tag频率
加{}代表增加权重,可以加很多个,有消息称加入英语短句识别
可选参数
&shape=Portrait/Landscape/Square 默认Portrait竖图
&scale=11 默认11,只建议11-24,细节会提高,太高了会过曝
&seed=1111111 如果想在返回的原图上修改,加入seed使图片生成结构类似

以下为维护组使用：
[绘图 黑/白名单 新增/添加/移除/删除 群号] 修改黑白名单(空格不能漏)
[黑名单列表/白名单列表] 查询黑白名单列表
'''.strip()

sv = Service(
    name="ai绘图",  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    bundle="娱乐",  # 分组归类
    help_=sv_help  # 帮助说明
)

# 以下参数仅用作配置说明，请不要在这里修改，请在config.json文件中修改配置才能生效！！！
config_default = {
    "base": {
        "daily_max": 20,  # 每日上限次数
        "freq_limit": 60,  # 频率限制
        "whitelistmode": False,  # 白名单模式开关
        "blacklistmode": True,  # 黑名单模式开关
        "ban_if_group_num_over": 1000  # 屏蔽群人数超过1000人的群
    },
    "NovelAI": {
        "api": "",  # 设置api，例如："http://11.222.333.444:5555/"
        "token": ""  # 设置你的token，例如："ADGdsvSFGsaA5S2D"，（若你的api无需使用token，留空即可）
    },
    "ban_word": {
        "wordlist": ["r18", "naked", "vagina", "penis", "nsfw", "genital", "nude", "NSFW", "R18", "NAKED", "VAGINA", "PENIS", "GENITAL", "NUDE"]
    }  # 屏蔽词列表
}
group_list_default = {
    "white_list": [

    ],
    "black_list": [

    ]
}

# Check config if exist
pathcfg = os.path.join(os.path.dirname(__file__), 'config.json')
if not os.path.exists(pathcfg):
    try:
        with open(pathcfg, 'w') as cfgf:
            json.dump(config_default, cfgf, ensure_ascii=False, indent=2)
            hoshino.logger.error(
                '[WARNING]未找到配置文件，已根据默认配置模板创建，请打开插件目录内config.json查看和修改。')
    except:
        hoshino.logger.error('[ERROR]创建配置文件失败，请检查插件目录的读写权限及是否存在config.json。')
        traceback.print_exc()

# check group list if exist
glpath = os.path.join(os.path.dirname(__file__), 'grouplist.json')
if not os.path.exists(glpath):
    try:
        with open(glpath, 'w') as cfggl:
            json.dump(group_list_default, cfggl, ensure_ascii=False, indent=2)
            hoshino.logger.error('[WARNING]未找到黑白名单文件，已根据默认黑白名单模板创建。')
    except:
        hoshino.logger.error('[ERROR]创建黑白名单文件失败，请检查插件目录的读写权限。')
        traceback.print_exc()

from .config import get_config, group_list_check, set_group_list, get_group_info, get_grouplist


# 设置limiter
tlmt = hoshino.util.DailyNumberLimiter(get_config('base', 'daily_max'))
flmt = hoshino.util.FreqLimiter(get_config('base', 'freq_limit'))


def check_lmt(uid, num, gid):
    if uid in hoshino.config.SUPERUSERS:
        return 0, ''
    if group_list_check(gid) != 0:
        if group_list_check(gid) == 1:
            return 1, f'此功能启用了白名单模式,本群未在白名单中,请联系维护组解决'
        else:
            return 1, f'此功能已在本群禁用,可能因为人数超限或之前有滥用行为,请联系维护组解决'
    if not tlmt.check(uid):
        return 1, f"您今天已经冲过{get_config('base', 'daily_max')}次了,请明天再来~"
    if num > 1 and (get_config('base', 'daily_max') - tlmt.get_num(uid)) < num:
        return 1, f"您今天的剩余次数为{get_config('base', 'daily_max') - tlmt.get_num(uid)}次,已不足{num}次,请少冲点(恼)!"
    if not flmt.check(uid):
        return 1, f'您冲的太快了,{round(flmt.left_time(uid))}秒后再来吧~'
    tlmt.increase(uid, num)
    flmt.start_cd(uid)
    return 0, ''


# 设置API
word2img_url = f"{get_config('NovelAI', 'api')}got_image?tags="
img2img_url = f"{get_config('NovelAI', 'api')}got_image2image"
token = f"&token={get_config('NovelAI', 'token')}"

# 加载屏蔽词
wordlist = get_config('ban_word', 'wordlist')


@sv.on_prefix('绘图')
async def send_config(bot, ev):
    uid = ev['user_id']
    gid = ev['group_id']
    is_su = hoshino.priv.check_priv(ev, hoshino.priv.SUPERUSER)
    args = ev.message.extract_plain_text().split()

    msg = ''
    if not is_su:
        msg = '需要超级用户权限\n发送"ai绘图帮助"获取操作指令'
    elif len(args) == 0:
        msg = '无效参数\n发送"ai绘图帮助"获取操作指令'
    elif args[0] == "黑名单" and len(args) == 3:  # 黑名单 新增/删除 gid(一次只能提供一个)
        if args[1] in ["新增", "添加"]:
            mode = 0
        elif args[1] in ["删除", "移除"]:
            mode = 1
        else:
            await bot.finish(ev, "操作错误，应为新增/删除其一")
        group_id = args[2]
        statuscode, failedgid = set_group_list(group_id, 1, mode)
        if statuscode == 403:
            msg = '无法访问黑白名单'
        elif statuscode == 404:
            msg = f'群{failedgid[0]}不在黑名单中'
        elif statuscode == 401:
            msg = f'警告！黑名单模式未开启！\n成功{args[1]}群{group_id}'
        else:
            msg = f'成功{args[1]}群{group_id}'
    elif args[0] == '白名单' and len(args) == 3:  # 白名单 新增/删除 gid(一次只能提供一个)
        if args[1] in ["新增", "添加"]:
            mode = 0
        elif args[1] in ["删除", "移除"]:
            mode = 1
        else:
            await bot.finish(ev, "操作错误，应为新增/删除其一")
        group_id = args[2]
        statuscode, failedgid = set_group_list(group_id, 0, mode)
        if statuscode == 403:
            msg = '无法访问黑白名单'
        elif statuscode == 404:
            msg = f'群{failedgid[0]}不在白名单中'
        elif statuscode == 402:
            msg = f'警告！白名单模式未开启！\n成功{args[1]}群{group_id}'
        else:
            msg = f'成功{args[1]}群{group_id}'
    else:
        msg = '无效参数'
    await bot.send(ev, msg)


@sv.on_fullmatch(('ai绘图帮助', '生成涩图帮助'))
async def gen_pic_help(bot, ev: CQEvent):
    await bot.send(ev, sv_help)


@sv.on_prefix(('ai绘图', '生成色图', '生成涩图'))
async def gen_pic(bot, ev: CQEvent):
    uid = ev['user_id']
    gid = ev['group_id']
    num = 1
    result, msg = check_lmt(uid, num, gid)
    if result != 0:
        await bot.send(ev, msg)
        return
    try:
        text = ev.message.extract_plain_text()
        if not priv.check_priv(ev, priv.SUPERUSER):
            for i in wordlist:
                if i in text:
                    await bot.send(ev, '不准涩涩')
                    return
        await bot.send(ev, f"在画了在画了，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)
        
        taglist = text.split(',')
        for tag in taglist:
            add_xp_num(uid, tag)
        
        get_url = word2img_url + text + token
        res = await aiorequests.get(get_url)
        image = await res.content
        load_data = json.loads(re.findall('{"steps".+?}', str(image))[0])
        image_b64 = 'base64://' + str(base64.b64encode(image).decode())
        mes = f"[CQ:image,file={image_b64}]\n"
        mes += f'seed:{load_data["seed"]}   '
        mes += f'scale:{load_data["scale"]}\n'
        mes += f'tags:{text}'
        await bot.send(ev, mes, at_sender=True)
    except Exception as e:
        await bot.send(ev, f"生成失败…{e}")
        return


thumbSize = (768, 768)


@sv.on_prefix(('以图生图', '以图绘图'))
async def gen_pic_from_pic(bot, ev: CQEvent):
    uid = ev['user_id']
    gid = ev['group_id']
    num = 1
    result, msg = check_lmt(uid, num, gid)
    if result != 0:
        await bot.send(ev, msg)
        return
    try:
        tag = ev.message.extract_plain_text()
        if not priv.check_priv(ev, priv.SUPERUSER):
            for i in wordlist:
                if i in tag:
                    await bot.send(ev, '不准涩涩')
                    return
        if tag == "":
            await bot.send(ev, '以图绘图必须添加tag')
            return
        else:
            url = ev.message[1]["data"]["url"]
        await bot.send(ev, f"正在生成，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)
        post_url = img2img_url + (f"?tags={tag}" if tag != "" else "") + token
        image = Image.open(io.BytesIO(requests.get(url, timeout=20).content))
        image = image.convert('RGB')
        if (image.size[0] > image.size[1]):
            image_shape = "Landscape"
        elif (image.size[0] == image.size[1]):
            image_shape = "Square"
        else:
            image_shape = "Portrait"
        image.thumbnail(thumbSize, resample=Image.ANTIALIAS)
        imageData = io.BytesIO()
        image.save(imageData, format='JPEG')
        res = await aiorequests.post(post_url + "&shape=" + image_shape, data=base64.b64encode(imageData.getvalue()))
        img = await res.content
        image_b64 = f"base64://{str(base64.b64encode(img).decode())}"
        load_data = json.loads(re.findall('{"steps".+?}', str(img))[0])
        mes = f"[CQ:image,file={image_b64}]\n"
        mes += f'seed:{load_data["seed"]}'
        await bot.send(ev, mes, at_sender=True)
    except Exception as e:
        await bot.send(ev, f"生成失败…{e}")
        return


XP_DB_PATH = os.path.expanduser('~/.hoshino/AI_image_xp.db')

class XpCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(XP_DB_PATH), exist_ok=True)
        self._create_table()
    def _connect(self):
        return sqlite3.connect(XP_DB_PATH)
        
    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS XP_NUM
                          (UID             INT    NOT NULL,
                           KEYWORD         TEXT   NOT NULL,
                           NUM             INT    NOT NULL,
                           PRIMARY KEY(UID,KEYWORD));''')
        except:
            raise Exception('创建表发生错误')
            
    def _add_xp_num(self, uid, keyword):
        try:
        
            num = self._get_xp_num(uid, keyword)
            if num == None:
                num = 0
            num += 1
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO XP_NUM (UID,KEYWORD,NUM) \
                                VALUES (?,?,?)", (uid, keyword, num)
                )
                  
        except:
            raise Exception('更新表发生错误')
            
    def _get_xp_num(self, uid, keyword):
        try:
            r = self._connect().execute("SELECT NUM FROM XP_NUM WHERE UID=? AND KEYWORD=?", (uid, keyword)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找表发生错误')
    
    def _get_xp_list(self, uid, num):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT KEYWORD,NUM FROM XP_NUM WHERE UID={uid} ORDER BY NUM desc LIMIT {num}").fetchall()
        return r if r else {}

def get_xp_list(uid):
    XP = XpCounter()
    xp_list = XP._get_xp_list(uid, 15)
    if len(xp_list)>0:
        data = sorted(xp_list,key=lambda cus:cus[1],reverse=True)
        new_data = []
        for xp_data in data:
            keyword, num = xp_data
            new_data.append((keyword,num))
        rankData = sorted(new_data,key=lambda cus:cus[1],reverse=True)
        return rankData
    else:
        return []

def add_xp_num(uid, keyword):
    XP = XpCounter()
    XP._add_xp_num(uid, keyword)
    
@sv.on_fullmatch(('我的XP', '我的xp'))
async def get_my_xp(bot, ev: CQEvent):
    xp_list = get_xp_list(ev.user_id)
    uid = ev.user_id
    msg = '您的XP信息为：\n'
    if len(xp_list)>0:
        for xpinfo in xp_list:
            keyword, num = xpinfo
            msg += f'关键词：{keyword}；查询次数：{num}\n'
    else:
        msg += '暂无您的XP信息'
    await bot.send(ev, msg)  

@sv.scheduled_job('cron', hour='2', minute='36')
async def set_ban_list():
    ban_list = []
    group_info = await get_group_info(info_type='member_count')
    for group in group_info:
        group_info[group] = int(group_info[group])
        if group_info[group] >= int(get_config('base', 'ban_if_group_num_over')):
            ban_list.append(group)
        else:
            pass
    set_group_list(ban_list, 1, 0)


@sv.on_fullmatch('黑名单列表')
async def get_black_list(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, '抱歉，您的权限不足，只有维护组才能进行该操作！')
        return
    gl = '以下群组已被列入ai绘图黑名单：'
    for g in get_grouplist('black_list'):
        gl += f"\n{g}"
    await bot.send(ev, gl)


@sv.on_fullmatch('白名单列表')
async def get_black_list(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, '抱歉，您的权限不足，只有维护组才能进行该操作！')
        return
    gl = '以下群组已被列入ai绘图白名单：'
    for g in get_grouplist('white_list'):
        gl += f"\n{g}"
    await bot.send(ev, gl)
