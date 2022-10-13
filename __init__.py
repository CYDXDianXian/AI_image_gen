import os
from pathlib import Path
import traceback
import hoshino
from . import db
from hoshino.typing import CQEvent
import base64
import re
import json
from hoshino import Service, aiorequests, priv
import io
from PIL import Image
from io import BytesIO
import time,calendar
from heapq import nsmallest

sv_help = '''
注：+ 号不用输入
[ai绘图/生成涩图+tag] 关键词仅支持英文，用逗号隔开
[以图绘图/以图生图+tag+图片] 注意图片尽量长宽都在765像素以下，不然会被狠狠地压缩
[本群/个人XP排行] 本群/个人的tag使用频率
[本群/个人XP缝合] 缝合tags进行绘图
[上传pic/上传图片] 务必携带seed/scale/tags等参数
[查看本群pic/查看本群图片] 查看已上传的图片
[点赞pic/点赞图片+数字ID] 对已上传图片进行点赞

加{}代表增加权重,可以加很多个,有消息称加入英语短句识别
可选参数：
&shape=Portrait/Landscape/Square 默认Portrait竖图。Landscape(横图)，Square(方图)
&scale=11 默认11，赋予AI自由度的参数，越高表示越遵守tags，一般保持11左右不变
&seed=1111111 随机种子。在其他条件不变的情况下，相同的种子代表生成相同的图

以下为维护组使用(空格不能漏)：
[绘图 状态 <群号>] 查看本群或指定群的模块开启状态
[绘图 设置 tags整理/数据录入/中英翻译/违禁词过滤 启用/关闭] 启用或关闭对应模块
[绘图 黑/白名单 新增/添加/移除/删除 群号] 修改黑白名单
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
        "ban_if_group_num_over": 1000,  # 屏蔽群人数超过1000人的群
    },
    "default": {
        "arrange_tags": True, # 是否开启tags整理（默认开启，暂时无法关闭）
        "add_db": True, # 是否开启数据录入（默认开启，暂时无法关闭）
        "trans": True, # 是否开启翻译
        "limit_word": True # 是否开启违禁词过滤
    },
    "NovelAI": {
        "api": "",  # 设置api，例如："http://11.222.333.444:5555/"
        "token": ""  # 设置你的token，例如："ADGdsvSFGsaA5S2D"，（若你的api无需使用token，留空即可）
    },
    "youdao": {
        "youdao_api": 'https://openapi.youdao.com/api',  # 有道api地址
        "app_id": "",  # 自己的有道智云应用id
        "app_key": ""  # 自己的有道智云应用秘钥
    },
    "default_tags":{
        "tags": "miku" # 如果没有指定tag的话，默认的tag
    },
    "ban_word": {
        "wordlist": [
			"r18",
			"naked",
			"vagina",
			"penis",
			"nsfw",
			"genital",
			"nude",
			"NSFW",
			"R18",
			"NAKED",
			"VAGINA",
			"PENIS",
			"GENITAL",
			"NUDE",
			"tentacle",
			"hairjob",
			"oral/fellatio",
			"deepthroat",
			"gokkun",
			"gag",
			"ballgag",
			"bitgag",
			"ring_gag",
			"cleave_gag",
			"panty_gag",
			"tapegag",
			"facial",
			"leash",
			"handjob",
			"groping",
			"areolae",
			"nipples",
			"puffy_nipples",
			"small_nipples",
			"nipple_pull",
			"nipple_torture",
			"nipple_tweak",
			"nipple_piercing",
			"breast_grab",
			"lactation",
			"breast_sucking/nipple_suck",
			"breast_feeding",
			"paizuri",
			"multiple_paizuri",
			"breast_smother",
			"piercing",
			"navel_piercing",
			"thigh_sex",
			"footjob",
			"mound_of_venus",
			"wide_hips",
			"masturbation",
			"clothed_masturbation",
			"penis",
			"testicles",
			"ejaculation",
			"cum",
			"cum_inside",
			"cum_on_breast",
			"cum_on_hair",
			"cum_on_food",
			"tamakeri",
			"pussy/vaginal",
			"pubic_hair",
			"shaved_pussy",
			"no_pussy",
			"clitoris",
			"fat_mons",
			"cameltoe",
			"pussy_juice",
			"female_ejaculation",
			"grinding",
			"crotch_rub",
			"facesitting",
			"cervix",
			"cunnilingus",
			"insertion",
			"anal_insertion",
			"fruit_insertion",
			"large_insertion",
			"penetration",
			"fisting",
			"fingering",
			"multiple_insertions",
			"double_penetration",
			"triple_penetration",
			"double_vaginal",
			"peeing",
			"have_to_pee",
			"ass",
			"huge_ass",
			"spread_ass",
			"buttjob",
			"spanked",
			"anus",
			"anal",
			"double_anal",
			"anal_fingering",
			"anal_fisting",
			"anilingus",
			"enema",
			"stomach_bulge",
			"x-ray",
			"cross-section/internal_cumshot",
			"wakamezake",
			"public",
			"humiliation",
			"bra_lift",
			"panties_around_one_leg",
			"caught",
			"walk-in",
			"body_writing",
			"tally",
			"futanari",
			"incest",
			"twincest",
			"pegging",
			"femdom",
			"ganguro",
			"bestiality",
			"gangbang",
			"hreesome",
			"group_sex",
			"orgy/teamwork",
			"tribadism",
			"molestation",
			"voyeurism",
			"exhibitionism",
			"rape",
			"about_to_be_raped",
			"sex",
			"clothed_sex",
			"happy_sex",
			"underwater_sex",
			"spitroast",
			"cock_in_thighhigh",
			"doggystyle",
			"leg_lock/upright_straddle",
			"missionary",
			"girl_on_top",
			"cowgirl_position",
			"reverse_cowgirl",
			"virgin",
			"slave",
			"shibari",
			"bondage",
			"bdsm",
			"pillory/stocks",
			"rope",
			"bound_arms",
			"bound_wrists",
			"crotch_rope",
			"hogtie",
			"frogtie",
			"suspension",
			"spreader_bar",
			"wooden_horse",
			"anal_beads",
			"dildo",
			"cock_ring",
			"egg_vibrator",
			"artificial_vagina",
			"hitachi_magic_wand",
			"dildo",
			"double_dildo",
			"vibrator",
			"vibrator_in_thighhighs",
			"nyotaimori",
			"vore",
			"amputee",
			"transformation",
			"mind_control",
			"censored",
			"uncensored",
			"asian",
			"faceless_male",
			"blood"
		]
    },  # 屏蔽词列表
}

group_list_default = {
    "white_list": [

    ],
    "black_list": [

    ]
}

groupconfig_default = {}

save_image_path = Path(__file__).parent / "SaveImage" # 保存图片路径
Path(save_image_path).mkdir(parents = True, exist_ok = True) # 创建路径

# Check config if exist
pathcfg = os.path.join(os.path.dirname(__file__), 'config.json')
if not os.path.exists(pathcfg):
	try:
		with open(pathcfg, 'w') as cfgf:
			json.dump(config_default, cfgf, ensure_ascii=False, indent=4)
			hoshino.logger.error('[WARNING]未找到配置文件，已根据默认配置模板创建，请打开插件目录内config.json查看和修改。')
	except:
		hoshino.logger.error('[ERROR]创建配置文件失败，请检查插件目录的读写权限及是否存在config.json。')
		traceback.print_exc()

# check group list if exist
glpath = os.path.join(os.path.dirname(__file__), 'grouplist.json')
if not os.path.exists(glpath):
	try:
		with open(glpath, 'w') as cfggl:
			json.dump(group_list_default, cfggl, ensure_ascii=False, indent=4)
			hoshino.logger.error('[WARNING]未找到黑白名单文件，已根据默认黑白名单模板创建。')
	except:
		hoshino.logger.error('[ERROR]创建黑白名单文件失败，请检查插件目录的读写权限。')
		traceback.print_exc()

# check group config if exist
gpcfgpath = os.path.join(os.path.dirname(__file__), 'groupconfig.json')
if not os.path.exists(gpcfgpath):
	try:
		with open(gpcfgpath, 'w') as gpcfg:
			json.dump(groupconfig_default, gpcfg, ensure_ascii=False, indent=4)
			hoshino.logger.error('[WARNING]未找到群个体设置文件，已创建。')
	except:
		hoshino.logger.error('[ERROR]创建群个体设置文件失败，请检查插件目录的读写权限。')
		traceback.print_exc()

from .config import get_config, get_group_config, get_group_info, set_group_config, group_list_check, set_group_list, get_grouplist
from .process import img_make, process_img, process_tags


# 设置limiter
tlmt = hoshino.util.DailyNumberLimiter(get_config('base', 'daily_max'))
flmt = hoshino.util.FreqLimiter(get_config('base', 'freq_limit'))


# 设置API
word2img_url = f"{get_config('NovelAI', 'api')}got_image?tags="
img2img_url = f"{get_config('NovelAI', 'api')}got_image2image"
token = f"&token={get_config('NovelAI', 'token')}"

wordlist = get_config('ban_word', 'wordlist')
default_tags = get_config('default_tags', 'tags')

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
    elif args[0] == '设置' and len(args) >= 3:  # setu set module on [group]
        if len(args) >= 4 and args[3].isdigit():
            gid = int(args[3])
        if args[1] == 'tags整理':
            key = 'arrange_tags'
        elif args[1] == '数据录入':
            key = 'add_db'
        elif args[1] == '中英翻译':
            key = 'trans'
        elif args[1] == '违禁词过滤':
            key = 'limit_word'
        else:
            key = None
        if args[2] == '开' or args[2] == '启用':
            value = True
        elif args[2] == '关' or args[2] == '禁用':
            value = False
        elif args[2].isdigit():
            value = int(args[2])
        else:
            value = None
        if key and (not value is None):
            set_group_config(gid, key, value)
            msg = '设置成功！当前设置值如下:\n'
            msg += f'群/{gid} : 设置项/{key} = 值/{value}'
        else:
            msg = '无效参数'
    elif args[0] == '状态':
        if len(args) >= 2 and args[1].isdigit():
            gid = int(args[1])
        arrange_tags_status = "启用" if get_group_config(gid, "arrange_tags") else "禁用"
        add_db_status = "启用" if get_group_config(gid, "add_db") else "禁用"
        trans_status = "启用" if get_group_config(gid, "trans") else "禁用"
        limit_word_status = "启用" if get_group_config(gid, "limit_word") else "禁用"
        msg = f'群 {gid} :'
        msg += f'\ntags整理: {arrange_tags_status}'
        msg += f'\n数据录入: {add_db_status}'
        msg += f'\n中英翻译: {trans_status}'
        msg += f'\n违禁词过滤: {limit_word_status}'
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


@sv.on_fullmatch(('ai绘图帮助', '生成涩图帮助', '生成色图帮助'))
async def gen_pic_help(bot, ev: CQEvent):
    await bot.send(ev, sv_help)


@sv.on_prefix(('ai绘图', '生成色图', '生成涩图'))
async def gen_pic(bot, ev: CQEvent):
    uid = ev['user_id']
    gid = ev['group_id']

    num = 1
    result, msg = check_lmt(uid, num, gid) # 检查群权限与个人次数
    if result != 0:
        await bot.send(ev, msg)
        return

    tags = ev.message.extract_plain_text()
    tags,error_msg,tags_guolu=await process_tags(gid,uid,tags) # tags处理过程
    if len(error_msg):
        await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
    if len(tags_guolu):
        await bot.send(ev, f"已过滤：{tags_guolu}", at_sender=True)
    if not len(tags):
        tags = default_tags
        await bot.send(ev, f"将使用默认tag：{default_tags}", at_sender=True)
    try:
        await bot.send(ev, f"在画了在画了，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)
        
        get_url = word2img_url + tags + token
        res = await aiorequests.get(get_url)
        image = await res.content
        load_data = json.loads(re.findall('{"steps".+?}', str(image))[0])
        image_b64 = 'base64://' + str(base64.b64encode(image).decode())
        mes = f"[CQ:image,file={image_b64}]\n"
        mes += f'seed:{load_data["seed"]}   '
        mes += f'scale:{load_data["scale"]}\n'
        if len(tags) < 2000:
            mes += f'tags:{tags}'
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
    result, msg = check_lmt(uid, num, gid) # 检查群权限与个人次数
    if result != 0:
        await bot.send(ev, msg)
        return

    tags = ev.message.extract_plain_text()
    tags,error_msg,tags_guolu=await process_tags(gid,uid,tags) #tags处理过程
    if len(error_msg):
        await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
    if len(tags_guolu):
        await bot.send(ev, f"已过滤：{tags_guolu}", at_sender=True)
    if not len(tags):
        tags = default_tags
        await bot.send(ev, f"将使用默认tag：{default_tags}", at_sender=True)
    try:
        if tags == "":
            await bot.send(ev, '以图绘图必须添加tag')
            return
        else:
            url = ev.message[1]["data"]["url"]
        await bot.send(ev, f"正在生成，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)
        post_url = img2img_url + (f"?tags={tags}" if tags != "" else "") + token
        image = Image.open(io.BytesIO(await (await aiorequests.get(url, timeout=20)).content))
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
        mes += f'seed:{load_data["seed"]}   '
        mes += f'scale:{load_data["scale"]}\n'
        if len(tags) < 2000:
            mes += f'tags:{tags}'
        await bot.send(ev, mes, at_sender=True)
    except Exception as e:
        await bot.send(ev, f"生成失败…{e}")
        return

    
@sv.on_fullmatch(('本群XP排行', '本群xp排行'))
async def get_group_xp(bot, ev):
    gid = ev.group_id
    xp_list = db.get_xp_list_group(gid)
    msg = '本群的XP排行榜为：\n'
    if len(xp_list)>0:
        for xpinfo in xp_list:
            keyword, num = xpinfo
            msg += f'关键词：{keyword}；次数：{num}\n'
    else:
        msg += '暂无本群的XP信息'
    await bot.send(ev, msg)

@sv.on_fullmatch(('个人XP排行', '个人xp排行'))
async def get_personal_xp(bot, ev):
    gid = ev.group_id
    uid = ev.user_id
    xp_list = db.get_xp_list_personal(gid,uid)
    msg = '你的XP排行榜为：\n'
    if len(xp_list)>0:
        for xpinfo in xp_list:
            keyword, num = xpinfo
            msg += f'关键词：{keyword}；次数：{num}\n'
    else:
        msg += '暂无你在本群的XP信息'
    await bot.send(ev, msg)

@sv.on_fullmatch(('本群XP缝合', '本群xp缝合'))
async def get_group_xp_pic(bot, ev):
    gid = ev.group_id
    uid = ev.user_id
    
    num = 1
    result, msg = check_lmt(uid, num, gid) # 检查群权限与个人次数
    if result != 0:
        await bot.send(ev, msg)
        return

    xp_list = db.get_xp_list_kwd_group(gid)
    msg = []
    if len(xp_list)>0:
        await bot.send(ev, f"正在缝合，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)
        for xpinfo in xp_list:
            keyword = xpinfo
            msg.append(keyword)
        xp_tags = (',').join(str(x) for x in msg)
        tags = (',').join(str(x) for x in (re.findall(r"'(.+?)'",xp_tags)))
        tags,error_msg,tags_guolu=await process_tags(gid,uid,tags,add_db=True,arrange_tags=True) #tags处理过程
        if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
        if len(tags_guolu):
            await bot.send(ev, f"已过滤：{tags_guolu}", at_sender=True)
        if not len(tags):
            tags = default_tags
            await bot.send(ev, f"将使用默认tag：{default_tags}", at_sender=True)
        try:
            url = word2img_url + tags + token
            response = await aiorequests.get(url, timeout = 30)
            data = await response.content
        except Exception as e:
            await bot.finish(ev, f"请求超时~", at_sender=True)
        msg,imgmes,error_msg = process_img(data)
        if len(error_msg):
            await bot.finish(ev, f"已报错：{error_msg}", at_sender=True)
        resultmes = f"[CQ:image,file={imgmes}]"
        resultmes += msg
        resultmes += f"\n tags:{tags}"
        await bot.send(ev, resultmes, at_sender=True)
    else:
        msg += '暂无本群的XP信息'

@sv.on_fullmatch(('个人XP缝合', '个人xp缝合'))
async def get_personal_xp_pic(bot, ev):
    gid = ev.group_id
    uid = ev.user_id
    
    num = 1
    result, msg = check_lmt(uid, num, gid) # 检查群权限与个人次数
    if result != 0:
        await bot.send(ev, msg)
        return
    
    xp_list = db.get_xp_list_kwd_personal(gid,uid)
    msg = []
    if len(xp_list)>0:
        await bot.send(ev, f"正在缝合，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)
        for xpinfo in xp_list:
            keyword = xpinfo
            msg.append(keyword)
        xp_tags = (',').join(str(x) for x in msg)
        tags = (',').join(str(x) for x in (re.findall(r"'(.+?)'",xp_tags)))
        tags,error_msg,tags_guolu=await process_tags(gid,uid,tags,add_db=True,arrange_tags=True) #tags处理过程
        if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
        if len(tags_guolu):
            await bot.send(ev, f"已过滤：{tags_guolu}", at_sender=True)
        if not len(tags):
            tags = default_tags
            await bot.send(ev, f"将使用默认tag：{default_tags}", at_sender=True)
        try:
            url = word2img_url + tags + token
            response = await aiorequests.get(url, timeout = 30)
            data = await response.content
        except Exception as e:
            await bot.finish(ev, f"请求超时~", at_sender=True)
        msg,imgmes,error_msg = process_img(data)
        if len(error_msg):
            await bot.finish(ev, f"已报错：{error_msg}", at_sender=True)
        resultmes = f"[CQ:image,file={imgmes}]"
        resultmes += msg
        resultmes += f"\n tags:{tags}"
        await bot.send(ev, resultmes, at_sender=True)
    else:
        msg += '暂无你在本群的XP信息'

@sv.on_prefix(('上传pic', '上传图片'))
async def upload_header(bot, ev):
    try:
        for i in ev.message:
            if i.type == "image":
                image=str(i)
                break
        image_url = re.match(r"\[CQ:image,file=(.*),url=(.*)\]", str(image))
        pic_url = image_url.group(2)
        response = await aiorequests.get(pic_url)
        img = Image.open(BytesIO(await response.content)).convert("RGB")
        ls_f=base64.b64encode(BytesIO(await response.content).read())
        imgdata=base64.b64decode(ls_f)
        pic_hash = hash(imgdata)
        datetime = calendar.timegm(time.gmtime())
        img_name= str(datetime)+'.png'
        pic_dir = save_image_path / img_name # 拼接图片路径
        a,b = img.size
        c = a/b
        s = [0.6667,1.5,1]
        s1 =["Portrait","Landscape","Square"]
        shape=s1[s.index(nsmallest(1, s, key=lambda x: abs(x-c))[0])]#shape
        Path(save_image_path, img_name).write_bytes(imgdata) # 保存图片到本地
    except:
        traceback.print_exc()
        await bot.finish(ev, '保存图片出错', at_sender=True)
    try:
        seed=(str(ev.message.extract_plain_text()).split(f"scale:")[0]).split('seed:')[1].strip()
        scale=(str(ev.message.extract_plain_text()).split(f"tags:")[0]).split('scale:')[1].strip()
        tags=(str(ev.message.extract_plain_text()).split(f"tags:")[1])
        pic_msg = tags + f"&seed={seed}" + f"&scale={scale}"
    except:
        await bot.finish(ev, '格式出错', at_sender=True)
    try:
        db.add_pic(ev.group_id, ev.user_id, pic_hash, str(pic_dir), pic_msg)
        await bot.send(ev, f'上传成功！已成功保存图片和配方', at_sender=True)
    except Exception as e:
        traceback.print_exc()
        await bot.send(ev, f"报错:{e}",at_sender=True)

@sv.on_prefix(("查看个人pic", "查看个人图片"))
async def check_personal_pic(bot, ev):
    gid = ev.group_id
    uid = ev.user_id
    page = ev.message.extract_plain_text().strip()
    if not page.isdigit() and '*' not in page:
        page = 1
    page = int(page)
    num = page*8
    msglist = db.get_pic_list_group(num)
    msglist = db.get_pic_list_personal(uid,num)
    if not len(msglist):
        await bot.finish(ev, '无法找到个人图片信息', at_sender=True)
    resultmes = img_make(msglist,page)
    await bot.send(ev, resultmes, at_sender=True)

@sv.on_fullmatch(('查看本群pic', '查看本群图片'))
async def check_group_pic(bot, ev):
    gid = ev.group_id
    uid = ev.user_id
    page = ev.message.extract_plain_text().strip()
    if not page.isdigit() and '*' not in page:
        page = 1
    page = int(page)
    num = page*8
    msglist = db.get_pic_list_group(gid,num)
    if not len(msglist):
        await bot.finish(ev, '无法找到本群图片信息', at_sender=True)
    resultmes = img_make(msglist,page)
    await bot.send(ev, resultmes, at_sender=True)
    
@sv.on_prefix(("查看全部pic", "查看全部图片"))
async def check_all_pic(bot, ev):
    page = ev.message.extract_plain_text().strip()
    if not page.isdigit() and '*' not in page:
        page = 1
    page = int(page)
    num = page*8
    msglist = db.get_pic_list_all(num)
    #msg = f"页数{page} 数据{len(msglist)}"
    if not len(msglist):
        await bot.finish(ev, '无法找到图片信息', at_sender=True)
    resultmes = img_make(msglist,page)
    await bot.send(ev, resultmes, at_sender=True)
    #await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(("点赞pic", "点赞图片"))
async def img_thumb(bot, ev):
    id = ev.message.extract_plain_text().strip()
    if not id.isdigit() and '*' not in id:
        await bot.finish(ev, '图片ID???')
    msg = db.add_pic_thumb(id)
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(("删除pic", "删除图片"))
async def del_img(bot, ev):
    gid = ev.group_id
    uid = ev.user_id
    if not priv.check_priv(ev,priv.SUPERUSER):
        msg = "只有超管才能删除"
        await bot.finish(ev, msg, at_sender=True)
    id = ev.message.extract_plain_text().strip()
    if not id.isdigit() and '*' not in id:
        await bot.finish(ev, '图片ID???')
    msg = db.del_pic(id)
    await bot.send(ev, msg, at_sender=True)

@sv.on_rex((r'^快捷绘图 ([0-9]\d*)(.*)'))
async def quick_img(bot, ev):
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    id = match.group(1)
    tags = match.group(2)

    num = 1
    result, msg = check_lmt(uid, num, gid) # 检查群权限与个人次数
    if result != 0:
        await bot.send(ev, msg)
        return
    try:
        msg = db.get_pic_data_id(id)
        (a,b) = msg
        msg = re.sub("&seed=[0-9]\d*", "", b, count=0, flags=0)
        tags +=f",{msg}"
        tags,error_msg,tags_guolu=process_tags(gid,uid,tags) #tags处理过程
        if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
        if len(tags_guolu):
            await bot.send(ev, f"已过滤：{tags_guolu}", at_sender=True)
        if not len(tags):
            tags = default_tags
            await bot.send(ev, f"将使用默认tag：{default_tags}", at_sender=True)
        try:
            url = word2img_url + tags + token
            response = await aiorequests.get(url, timeout = 30)
            data = await response.content
        except Exception as e:
            await bot.finish(ev, f"请求超时~", at_sender=True)
        msg,imgmes,error_msg = process_img(data)
        if len(error_msg):
            await bot.finish(ev, f"已报错：{error_msg}", at_sender=True)
        resultmes = f"[CQ:image,file={imgmes}]"
        resultmes += msg
        resultmes += f"\n tags:{tags}"
        await bot.send(ev, resultmes, at_sender=True)
    except Exception as e:
        await bot.send(ev, f"报错:{e}",at_sender=True)

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
