import os
import traceback
import hoshino
from . import db
from .packedfiles import default_config
from hoshino.typing import CQEvent, MessageSegment
import re
import json
from hoshino import Service, priv
from io import BytesIO
from PIL import Image

sv_help = '''
注：+ 号不用输入
[ai绘图/生成涩图+tag] 关键词仅支持英文，用逗号隔开
[以图绘图/以图生图+tag+图片] 注意图片尽量长宽都在765像素以下，不然会被狠狠地压缩
[清晰术/上采样+图片] 图片超分(默认四倍放大三倍降噪)
[清晰术+双重/三重/四重吟唱+强力术式/中等术式/弱术式/不变式/原式] 图片放大倍率与降噪倍率选项
[二次元化/动漫化+图片] 照片二次元化
[上传pic/上传图片] 务必携带seed/scale/tags等参数
[查看配方/查看tag+图片ID] 查看已上传图片的配方
[快捷绘图+图片ID] 使用已上传图片的配方进行快捷绘图
[查看个人pic/查看个人图片+页码] 查看个人已上传的图片
[查看本群pic/查看本群图片+页码] 查看本群已上传的图片
[查看全部pic/查看全部图片+页码] 查看全部群已上传的图片
[点赞pic/点赞图片+图片ID] 对已上传图片进行点赞
[删除pic/删除图片+图片ID] 删除对应图片和配方(仅限维护组使用)
[本群/个人XP排行] 本群/个人的tag使用频率
[本群/个人XP缝合] 缝合tags进行绘图
[图片鉴赏/生成tag+图片] 根据上传的图片生成tags
[回复消息+以图绘图/上传图片/图片鉴赏/清晰术/二次元化] 回复消息使用上述功能

以下为维护组使用(空格不能漏)：
[绘图 状态 <群号>] 查看本群或指定群的模块开启状态
[绘图 设置 撤回时间 0~999 <群号>] 设置本群或指定群撤回时间(单位秒)，0为不撤回
[绘图 设置 tags整理/数据录入/中英翻译/违禁词过滤 启用/关闭 <群号>] 启用或关闭对应模块
[绘图 黑/白名单 新增/添加/移除/删除 群号] 修改黑白名单
[黑名单列表/白名单列表] 查询黑白名单列表

参数使用说明：
加{}代表增加权重,可以加很多个,有消息称加入英语短句识别
可选参数：
&shape=Portrait/Landscape/Square 默认Portrait竖图。Landscape(横图)，Square(方图)
&scale=11 默认11，赋予AI自由度的参数，越高表示越遵守tags，一般保持11左右不变
&seed=1111111 随机种子。在其他条件不变的情况下，相同的种子代表生成相同的图
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

config_default = default_config.config_default
group_list_default = default_config.group_list_default
groupconfig_default = default_config.groupconfig_default

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


# 生成配置文件后再进行读取配置文件的操作，否则会报错
from .config import get_config, get_group_config, get_group_info, set_group_config, group_list_check, set_group_list, get_grouplist
from .process import process_tags
from .message import SendMessageProcess
from . import utils


# 设置limiter
tlmt = hoshino.util.DailyNumberLimiter(get_config('base', 'daily_max'))
flmt = hoshino.util.FreqLimiter(get_config('base', 'freq_limit'))

# 获取默认tag
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
        if args[1] == '撤回时间':
            key = 'withdraw'
        elif args[1] == 'tags整理':
            key = 'arrange_tags'
        elif args[1] == '数据录入':
            key = 'add_db'
        elif args[1] == '中英翻译':
            key = 'trans'
        elif args[1] == '违禁词过滤':
            key = 'limit_word'
        else:
            key = None
        if args[2] == '开启' or args[2] == '启用':
            value = True
        elif args[2] == '关闭' or args[2] == '禁用':
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
        withdraw_status = "不撤回" if get_group_config(gid, "withdraw") == 0 else f'{get_group_config(gid, "withdraw")}秒'
        arrange_tags_status = "启用" if get_group_config(gid, "arrange_tags") else "禁用"
        add_db_status = "启用" if get_group_config(gid, "add_db") else "禁用"
        trans_status = "启用" if get_group_config(gid, "trans") else "禁用"
        limit_word_status = "启用" if get_group_config(gid, "limit_word") else "禁用"
        msg = f'群 {gid} :'
        msg += f'\n撤回时间: {withdraw_status}'
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
            await bot.send(ev, "操作错误，应为新增/删除其一")
            return
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
            await bot.send(ev, "操作错误，应为新增/删除其一")
            return
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
    await bot.send(ev, MessageSegment.image(utils.pic2b64(utils.text_to_image(sv_help))), at_sender=True)


@sv.on_prefix(('ai绘图', '生成色图', '生成涩图'))
async def gen_pic(bot, ev: CQEvent):
    msg_list = []
    uid = ev['user_id']
    gid = ev['group_id']

    tags = ev.message.extract_plain_text().strip()
    tags,error_msg,tags_guolv=await process_tags(gid,uid,tags) # tags处理过程

    if len(error_msg):
        msg_list.append(f"已报错：{error_msg}")
    if len(tags_guolv):
        msg_list.append(f"已过滤：{tags_guolv}")
    if not len(tags):
        tags = default_tags
        await bot.send(ev, f"将使用默认tag：{default_tags}", at_sender=True)
    try:
        num = 1
        result, msg = check_lmt(uid, num, gid) # 检查群权限与个人次数
        if result != 0:
            await bot.send(ev, msg)
            return
        await bot.send(ev, f"在画了在画了，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)
        
        resultmes,error_msg = await utils.get_imgdata(tags) # 绘图过程
        if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
            return
        
        msg_list.append(resultmes)
        await SendMessageProcess(bot, ev, msg_list) # 发送消息过程
    except Exception as e:
        await bot.send(ev, f"生成失败…{e}")
        return


thumbSize = (768, 768)

@sv.on_keyword(('以图生图', '以图绘图'))
async def gen_pic_from_pic(bot, ev: CQEvent):
    msg_list = []
    uid = ev['user_id']
    gid = ev['group_id']

    tags = utils.key_worlds_removal(ev.message.extract_plain_text()).strip()
    tags,error_msg,tags_guolv=await process_tags(gid,uid,tags) #tags处理过程
    if len(error_msg):
        msg_list.append(f"已报错：{error_msg}")
    if len(tags_guolv):
        msg_list.append(f"已过滤：{tags_guolv}")
    if not len(tags):
        tags = default_tags
        await bot.send(ev, f"将使用默认tag：{default_tags}", at_sender=True)
    
    try:
        image, _, _ = await utils.get_image_and_msg(bot, ev) # 获取图片过程
        if tags == "":
            await bot.send(ev, '以图绘图必须添加tag')
            return
        elif image is None:
            await bot.send(ev, '请输入需要绘图的图片')
            return
        
        num = 1
        result, msg = check_lmt(uid, num, gid) # 检查群权限与个人次数
        if result != 0:
            await bot.send(ev, msg)
            return
        await bot.send(ev, f"正在生成，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)
        
        if (image.size[0] > image.size[1]): # 判断图片形状
            image_shape = "Landscape"
        elif (image.size[0] == image.size[1]):
            image_shape = "Square"
        else:
            image_shape = "Portrait"
        image.thumbnail(thumbSize, resample=Image.ANTIALIAS) # 图片缩放
        imageData = BytesIO() # 创建二进制缓存
        image.save(imageData, format='png') # 保存图片至缓存中
        
        resultmes,error_msg = await utils.get_imgdata(tags,way=0,shape=image_shape,b_io=imageData) # 绘图过程
        if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
            return
        
        msg_list.append(resultmes)
        await SendMessageProcess(bot, ev, msg_list) # 发送消息过程
    except Exception as e:
        await bot.send(ev, f"生成失败…{e}")
        traceback.print_exc()
        return


@sv.on_keyword(('图片鉴赏', '鉴赏图片', '生成tag', '生成tags'))
async def generate_tags(bot, ev):
    # uid = ev['user_id']
    # gid = ev['group_id']
    #
    # num = 1
    # result, msg = check_lmt(uid, num, gid)  # 检查群权限与个人次数
    # if result != 0:
    #     await bot.send(ev, msg)
    #     return

    msg_list = []
    image, _, _ = await utils.get_image_and_msg(bot, ev)
    if not image:
        await bot.send(ev, '请输入需要分析的图片', at_sender=True)
        return
    await bot.send(ev, f"正在生成tags，请稍后...")
    json_tags = await utils.get_tags(image)

    if json_tags:
        msg = "图片鉴赏结果为如下"
        msg_list.append(msg)
        msg = ','.join([f'{t["label"]}' for t in json_tags])
        msg_list.append(msg)
        await SendMessageProcess(bot, ev, msg_list, withdraw=False) # 发送消息过程
    else:
        await bot.send(ev, '生成失败，肯定不是bot的错！', at_sender=True)
        traceback.print_exc()

@sv.on_keyword(('二次元化', '动漫化'))
async def animize(bot, ev):
    msg_list = []
    image, _, _ = await utils.get_image_and_msg(bot, ev)
    if not image:
        await bot.send(ev, '请输入需要分析的图片', at_sender=True)
        return
    await bot.send(ev, f"正在进入二次元，请稍后...")

    img_msg = await utils.cartoonization(image)
    if img_msg:
        msg_list.append(MessageSegment.image(img_msg))
        await SendMessageProcess(bot, ev, msg_list) # 发送消息过程
    else:
        await bot.send(ev, '生成失败，图片被创死了！', at_sender=True)
        traceback.print_exc()

@sv.on_suffix(('XP排行', 'xp排行'))
async def get_xp_list(bot, ev):
    msg_list = []
    msg = ev.message.extract_plain_text()
    gid = ev.group_id
    uid = ev.user_id
    resultmes,error_msg = await utils.get_xp_list_(msg,gid,uid)
    if len(error_msg):
        await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
        return
    
    msg_list.append(resultmes)
    await SendMessageProcess(bot, ev, msg_list, withdraw=False) # 发送消息过程

@sv.on_suffix(('XP缝合', 'xp缝合'))
async def get_xp_pic(bot, ev):
    msg_list = []
    gid = ev.group_id
    uid = ev.user_id
    msg = ev.message.extract_plain_text()
    tags,error_msg = await utils.get_xp_pic_(msg,gid,uid)
    if len(error_msg):
        await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
        return
    
    num = 1
    result, msg = check_lmt(uid, num, gid) # 检查群权限与个人次数
    if result != 0:
        await bot.send(ev, msg)
        return
    await bot.send(ev, f"正在生成，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)

    tags,error_msg,tags_guolv=await process_tags(gid,uid,tags) #tags处理过程
    if len(error_msg):
        msg_list.append(f"已报错：{error_msg}")
    if len(tags_guolv):
        msg_list.append(f"已过滤：{tags_guolv}")
    resultmes,error_msg = await utils.get_imgdata(tags) # 绘图过程
    if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
            return
    
    msg_list.append(resultmes)
    await SendMessageProcess(bot, ev, msg_list) # 发送消息过程

@sv.on_keyword(('上传pic', '上传图片'))
async def upload_header(bot, ev):
    image, pic_hash, msg = await utils.get_image_and_msg(bot, ev) # 获取图片过程
    if not image:
        await bot.send(ev, "图片获取失败！", at_sender=True)
        return
    pic_dir,error_msg = await utils.save_pic(image, pic_hash)
    if len(error_msg):
        await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
        return
    try:
        seed=(str(msg).split(f"scale:")[0]).split('seed:')[1].strip()
        scale=(str(msg).split(f"tags:")[0]).split('scale:')[1].strip()
        tags=(str(msg).split(f"tags:")[1])
        pic_msg = tags + f"&seed={seed}" + f"&scale={scale}"
    except:
        await bot.send(ev, '格式出错', at_sender=True)
        return
    try:
        resultmes = db.add_pic(ev.group_id, ev.user_id, pic_hash, str(pic_dir), pic_msg) # pic_dir是Path路径对象，必须转为str后数据库才能正常录入
        await bot.send(ev, resultmes, at_sender=True)
    except Exception as e:
        traceback.print_exc()
        await bot.send(ev, f"报错:{e}",at_sender=True)

@sv.on_rex((r'^查看(.*)图片+(\s?([0-9]\d*))?'))
async def check_pic(bot, ev):
    msg_list = []
    gid = ev.group_id
    uid = ev.user_id
    match = ev['match']
    msg = match.group(1)
    try:
        page = int(match.group(2).lstrip())
    except:
        page = 1
    resultmes,error_msg = await utils.check_pic_(gid,uid,msg,page)
    if len(error_msg):
        await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
        return
        
    msg_list.append(resultmes)
    await SendMessageProcess(bot, ev, msg_list, withdraw=False) # 发送消息过程

@sv.on_prefix(("点赞pic", "点赞图片"))
async def img_thumb(bot, ev):
    id = ev.message.extract_plain_text().strip()
    if not id.isdigit() and '*' not in id:
        await bot.send(ev, '图片ID呢???')
        return
    msg = db.add_pic_thumb(id)
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix(("删除pic", "删除图片"))
async def del_img(bot, ev):
    try:
        gid = ev.group_id
        uid = ev.user_id
        if not priv.check_priv(ev,priv.SUPERUSER):
            msg = "只有超管才能删除"
            await bot.send(ev, msg, at_sender=True)
            return
        id = ev.message.extract_plain_text().strip()
        if not id.isdigit() and '*' not in id:
            await bot.send(ev, '图片ID呢???')
            return
        db.del_pic(id)
        msg = f"已成功删除【{id}】号图片"
        await bot.send(ev, msg, at_sender=True)
    except ValueError as e:
        await bot.send(ev, f"已报错：【{id}】号图片不存在！",at_sender=True)
        traceback.print_exc()
    except Exception as e:
        await bot.send(ev, f"报错:{e}",at_sender=True)
        traceback.print_exc()

@sv.on_rex((r'^快捷绘图\s?([0-9]\d*)\s?(.*)'))
async def quick_img(bot, ev):
    try:
        msg_list = []

        gid = ev.group_id
        uid = ev.user_id
        match = ev['match']
        id = match.group(1)
        tags = match.group(2)
        msg = db.get_pic_data_id(id)
        (a,b) = msg
        msg = re.sub("&seed=[0-9]\d*", "", b, count=0, flags=0)
        tags +=f",{msg}"
        
        num = 1
        result, msg_ = check_lmt(uid, num, gid) # 检查群权限与个人次数
        if result != 0:
            await bot.send(ev, msg_)
            return
        await bot.send(ev, f"正在使用【{id}】号图片的配方进行绘图，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)

        tags,error_msg,tags_guolv = await process_tags(gid,uid,tags) #tags处理过程
        if len(error_msg):
            msg_list.append(f"已报错：{error_msg}")
        if len(tags_guolv):
            msg_list.append(f"已过滤：{tags_guolv}")
        
        resultmes,error_msg = await utils.get_imgdata(tags)
        if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
            return

        msg_list.append(resultmes)
        await SendMessageProcess(bot, ev, msg_list)
    except ValueError as e:
        await bot.send(ev, f"已报错：【{id}】号图片不存在！",at_sender=True)
        traceback.print_exc()
        return
    except Exception as e:
        await bot.send(ev, f"报错:{e}",at_sender=True)
        traceback.print_exc()
        return

@sv.on_prefix(('查看配方', '查看tag', '查看tags'))
async def get_img_peifang(bot, ev: CQEvent):
    try:
        msg_list = []
        id = ev.message.extract_plain_text().strip()
        if not id.isdigit() and '*' not in id:
            await bot.send(ev, '图片ID呢???没ID怎么查???')
            return
        msg = db.get_pic_data_id(id)
        (a,b) = msg
        msg = re.sub("&seed=[0-9]\d*", "", b, count=0, flags=0)
        tags = ""
        tags +=f"{msg}"
        msg_list.append(f"【{id}】号图片的配方如下")
        msg_list.append(tags)
        await SendMessageProcess(bot, ev, msg_list, withdraw=False)
    except ValueError as e:
        await bot.send(ev, f"已报错：【{id}】号图片不存在！",at_sender=True)
        traceback.print_exc()
    except Exception as e:
        await bot.send(ev, f"报错:{e}",at_sender=True)
        traceback.print_exc()

@sv.on_keyword(('清晰术', '清晰化', '上采样'))
async def image4x(bot, ev):
    if get_config("image4x", "Real-CUGAN"):
        await img_Real_CUGAN(bot, ev)
    elif get_config("image4x", "Real-ESRGAN"):
        await img_Real_ESRGAN(bot, ev)
    else:
        await bot.send(ev, "已报错：Real-CUGAN与Real-ESRGAN超分模型均未开启！", at_sender=True)

async def img_Real_CUGAN(bot, ev):
    try:
        msg_list = []
        image, _, _ = await utils.get_image_and_msg(bot, ev)
        if not image:
            await bot.send(ev, '请输入需要超分的图片', at_sender=True)
            return
        ix=image.size[0] # 获取图片宽度
        iy=image.size[1] # 获取图片高度
        thumbSize = (1024, 1024)
        if ix * iy > 1000000: # 图片像素大于100w将对其进行缩放
            image.thumbnail(thumbSize, resample=Image.ANTIALIAS) # 图片等比例缩放
            await bot.send(ev, "图片尺寸超过100万像素，将对其进行缩放", at_sender=True)
        fashu = ev.message.extract_plain_text()
        scale = 2
        con = "conservative"
        if "双重吟唱" in fashu:
            scale = 2
        elif "三重吟唱" in fashu:
            scale = 3
        elif "四重吟唱" in fashu:
            scale = 4
        else:
            scale = 4 # 如不指定放大倍数，则默认放大4倍

        if "强力术式" in fashu:
            con = "denoise3x"
        elif "中等术式" in fashu:
            con = "no-denoise"
            if scale == 2:
                con = "denoise2x"
        elif "弱术式" in fashu:
            con = "no-denoise"
            if scale == 2:
                con = "denoise1x"
        elif "不变式" in fashu:
            con = "no-denoise"
        elif "原式" in fashu:
            con = "conservative"
        else:
            con = "denoise3x" # 如不指定降噪等级，默认3倍降噪

        modelname = f"up{scale}x-latest-{con}.pth"
        await bot.send(ev, f"鸣大钟一次，推动杠杆，启动活塞和泵；鸣大钟两次，按下按钮，发动机点火，点燃涡轮，注入生命；鸣大钟三次，齐声歌唱，赞美万机之神！大清晰术【{con}】【{scale}】重唱！")
        img_msg = await utils.get_Real_CUGAN(image, modelname)

        if img_msg:
            msg_list.append(f"【{scale}】重唱【{con}】分支大清晰术！")
            msg_list.append(MessageSegment.image(img_msg))
            await SendMessageProcess(bot, ev, msg_list) # 发送消息过程
        else:
            await bot.send(ev, "清晰术失败，服务器未返回图片数据", at_sender=True)
            traceback.print_exc()
    except Exception as e:
        await bot.send(ev, f"清晰术失败,{e}", at_sender=True)
        traceback.print_exc()

async def img_Real_ESRGAN(bot, ev):
    msg_list = []
    image, _, _ = await utils.get_image_and_msg(bot, ev)
    ix=image.size[0] # 获取图片宽度
    iy=image.size[1] # 获取图片高度
    thumbSize = (1024, 1024)
    if not image:
        await bot.send(ev, '请输入需要超分的图片', at_sender=True)
        return
    if ix * iy > 1000000: # 图片像素大于100w将对其进行缩放
        image.thumbnail(thumbSize, resample=Image.ANTIALIAS) # 图片等比例缩放
        await bot.send(ev, "图片尺寸超过100万像素，将对其进行缩放", at_sender=True)
    await bot.send(ev, f"正在使用Real-ESRGAN模型4倍超分图片，请稍后...")

    img_msg = await utils.get_Real_ESRGAN(image)
    if img_msg:
        msg_list.append("使用Real-ESRGAN模型4倍超分图片结果")
        msg_list.append(MessageSegment.image(img_msg))
        await SendMessageProcess(bot, ev, msg_list) # 发送消息过程
    else:
        await bot.send(ev, '生成失败，肯定不是bot的错！', at_sender=True)
        traceback.print_exc()

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
