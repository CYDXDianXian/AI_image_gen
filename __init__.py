import os
import traceback
import hoshino
from . import db
from .packedfiles import default_config
from hoshino.typing import CQEvent
import re
import json
from hoshino import Service, priv
from io import BytesIO
from . import magic

sv_help = '''
注：+ 号不用输入
【主要功能】
[ai绘图/生成涩图+tag] 关键词仅支持英文，用逗号隔开
[清晰术/图片超分+图片] 图片超分(默认2倍放大3级降噪)
[清晰术+2倍/3倍/4倍放大+不/保守/强力降噪] 图片放大倍率与降噪倍率选项
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
[元素法典 xxx] xxx可以是多种魔咒，空格分离
[元素法典咏唱/吟唱 xxx] 发动黑暗法典，多种魔咒用空格分离

【元素法典目录】
['水魔法', '空间法', '冰魔法', '核爆法', '风魔法', '流沙法', '白骨法', '星空法', '机凯种', 
'森林冰', '幻之时', '雷男法', '圣光法', '苇名法', '自然法', '冰系改', '融合法', '虹彩法', 
'暗锁法', '星冰乐', '火烧云', '城堡法', '雪月法', '结晶法', '黄昏法', '森林法', '泡泡法', 
'蔷薇法', '月亮法', '森火法', '废土法', '机娘水', '黄金法', '死灵法', '水晶法', '水森法', 
'冰火法', '龙骑士', '坠落法', '水下法', '秘境法', '摄影法', '望穿水', '天选术', '摩登法', 
'血魔法', '绚丽术', '唤龙术', '龙机法', '战姬法', '炼银术', '星源法', '学院法', '浮世绘', 
'星霞海', '冬雪法', '刻刻帝', '万物熔炉', '暗鸦法', '花 火法基础', '星之彩', '沉入星海', 
'百溺法', '百溺法plus', '辉煌阳光法', '星鬓法', '森罗法', '星天使', '黄金律', '机凯姬 改', 
'人鱼法', '末日', '碎梦', '幻碎梦', '血法改', '留影术', '西幻术', '星语术', '金石法', 
'飘花法', '冰霜龙息plus', '冰霜龙息']

【以下为维护组使用(空格不能漏)】
[绘图 状态 <群号>] 查看本群或指定群的模块开启状态
[绘图 设置 撤回时间 0~999 <群号>] 设置本群或指定群撤回时间(单位秒)，0为不撤回
[绘图 设置 tags整理/数据录入/中英翻译/违禁词过滤 开启/关闭 <群号>] 启用或禁用对应模块
[绘图 黑/白名单 新增/添加/移除/删除 群号] 修改黑白名单
[黑名单列表/白名单列表] 查询黑白名单列表

【参数使用说明】
加{}代表增加权重,可以加很多个
可选参数：
&ntags=xxx 负面tags输入
&shape=Portrait/Landscape/Square 默认Portrait竖图。Landscape(横图)，Square(方图)
&scale=11 默认11，赋予AI自由度的参数，越高表示越遵守tags，一般保持11左右不变
&seed=1111111 随机种子。在其他条件不变的情况下，相同的种子代表生成相同的图
输入例：
ai绘图 {{miku}},long hair&ntags=lowres,bad hands&shape=Portrait&scale=24&seed=150502
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
    await bot.send(ev, utils.text_to_image(sv_help), at_sender=True)


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
        await bot.send(ev, f"生成失败…{type(e)}")
        return


# @sv.on_keyword(('以图生图', '以图绘图')) # 官网api关闭了该入口，故暂时停用该功能
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
        image.thumbnail(size=(768, 768)) # 图片缩放
        imageData = BytesIO() # 创建二进制缓存
        image.save(imageData, format='png') # 保存图片至缓存中，png格式为无损格式
        
        resultmes,error_msg = await utils.get_imgdata(tags,way=0,shape=image_shape,b_io=imageData) # 绘图过程
        if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
            return
        
        msg_list.append(resultmes)
        await SendMessageProcess(bot, ev, msg_list) # 发送消息过程
    except Exception as e:
        await bot.send(ev, f"生成失败：{type(e)}")
        traceback.print_exc()
        return

@sv.on_suffix(('XP排行', 'xp排行'))
async def get_xp_list(bot, ev):
    try:
        msg_list = []
        msg = ev.message.extract_plain_text()
        gid = ev.group_id
        uid = ev.user_id
        resultmes,error_msg = await utils.get_xp_list_(msg,gid,uid)
        if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
            return
    except Exception as e:
        await bot.send(ev, f"已报错：{type(e)}", at_sender=True)
        traceback.print_exc()
    
    msg_list.append(resultmes)
    await SendMessageProcess(bot, ev, msg_list, withdraw=False) # 发送消息过程

@sv.on_suffix(('XP缝合', 'xp缝合'))
async def get_xp_pic(bot, ev):
    try:
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
    except Exception as e:
        await bot.send(ev, f"已报错：{type(e)}", at_sender=True)
        traceback.print_exc()

@sv.on_keyword(('上传pic', '上传图片'))
async def upload_header(bot, ev):
    try:
        image, pic_hash, msg = await utils.get_image_and_msg(bot, ev) # 获取图片过程
        if not image:
            await bot.send(ev, "请输入要上传的图片", at_sender=True)
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
            await bot.send(ev, f"报错:{type(e)}",at_sender=True)
    except Exception as e:
        await bot.send(ev, f"已报错：{type(e)}", at_sender=True)
        traceback.print_exc()

@sv.on_rex((r'^查看(.*)图片+(\s?([0-9]\d*))?'))
async def check_pic(bot, ev):
    try:
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
    except Exception as e:
        await bot.send(ev, f"已报错：{type(e)}", at_sender=True)
        traceback.print_exc()

@sv.on_prefix(("点赞pic", "点赞图片"))
async def img_thumb(bot, ev):
    try:
        id = ev.message.extract_plain_text().strip()
        if not id.isdigit() and '*' not in id:
            await bot.send(ev, '图片ID呢???')
            return
        msg = db.add_pic_thumb(id)
        await bot.send(ev, msg, at_sender=True)
    except Exception as e:
        await bot.send(ev, f"已报错：{type(e)}", at_sender=True)
        traceback.print_exc()

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
        return
    except Exception as e:
        await bot.send(ev, f"报错:{type(e)}",at_sender=True)
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
        await bot.send(ev, f"报错:{type(e)}",at_sender=True)
        traceback.print_exc()

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
        await bot.send(ev, f"报错:{type(e)}",at_sender=True)
        traceback.print_exc()

@sv.on_keyword(('图片鉴赏', '鉴赏图片', '生成tag', '生成tags'))
async def generate_tags(bot, ev):
    try:
        msg_list = []
        image, _, _ = await utils.get_image_and_msg(bot, ev)
        if not image:
            await bot.send(ev, '请输入需要分析的图片', at_sender=True)
            return
        await bot.send(ev, f"正在生成tags，请稍后...")
        ix=image.size[0] # 获取图片宽度
        iy=image.size[1] # 获取图片高度
        if ix * iy > 1000000: # 图片像素大于100万像素的，会对其进行缩放
            image.thumbnail(size=(1000, 1000)) # 图片等比例缩放
        result_msg,error_msg = await utils.get_tags(image)
        if error_msg:
            await bot.send(ev, f"鉴赏失败：{error_msg}", at_sender=True)
            traceback.print_exc()
            return
        msg_list.append("图片鉴赏结果为如下")
        msg_list.append(result_msg)
        await SendMessageProcess(bot, ev, msg_list, withdraw=False) # 发送消息过程
    except Exception as e:
        await bot.send(ev, f"鉴赏失败：{type(e)}", at_sender=True)
        traceback.print_exc()

@sv.on_keyword(('二次元化', '动漫化'))
async def animize(bot, ev):
    try:
        msg_list = []
        image, _, _ = await utils.get_image_and_msg(bot, ev)
        if not image:
            await bot.send(ev, '请输入需要分析的图片', at_sender=True)
            return
        await bot.send(ev, f"正在进入二次元，请稍后...")
        ix=image.size[0] # 获取图片宽度
        iy=image.size[1] # 获取图片高度
        if ix * iy > 490000: # 图片像素大于49万像素的，会对其进行缩放
            image.thumbnail(size=(700, 700)) # 图片等比例缩放
        img_msg, error_msg= await utils.cartoonization(image)
        if error_msg:
            await bot.send(ev, f"二次元化失败：{error_msg}", at_sender=True)
            traceback.print_exc()
            return
        msg_list.append("图片已进入二次元")
        msg_list.append(img_msg)
        await SendMessageProcess(bot, ev, msg_list) # 发送消息过程
    except Exception as e:
        await bot.send(ev, f"已报错：{type(e)}", at_sender=True)
        traceback.print_exc()

@sv.on_keyword(('清晰术', '图片超分', '图片放大'))
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
        if ix * iy > 1000000: # 图片像素大于100万像素的，会对其进行缩放
            image.thumbnail(size=(1000, 1000)) # 图片等比例缩放
            await bot.send(ev, f"图片尺寸超过100万像素，将对其进行缩放", at_sender=True)
        msg = ev.message.extract_plain_text().strip()
        try:
            if "二倍放大" in msg or "2倍放大" in msg:
                scale = 2
            elif "三倍放大" in msg or "3倍放大" in msg:
                scale = 3
            elif "四倍放大" in msg or "4倍放大" in msg:
                scale = 4
            else:
                scale = 2 # 如不指定放大倍数，则默认放大2倍

            if "保守降噪" in msg:
                con = "conservative"
                con_cn = "保守"
            elif "强力降噪" in msg or "三级降噪" in msg or "3级降噪" in msg:
                con = "denoise3x"
                con_cn = "3级"
            elif "不降噪" in msg:
                con = "no-denoise"
                con_cn = "不降噪"
            else:
                con = "denoise3x" # 如不指定降噪等级，默认3倍降噪
                con_cn = "3级"
            modelname = f"up{scale}x-latest-{con}.pth"
            await bot.send(ev, f"放大倍率：{scale}倍    降噪等级：{con_cn}\n正在进行图片超分，请稍后...")
        except Exception as e:
            await bot.send(bot, ev, f"超分参数输入错误：{type(e)}")
            return
        img_msg, error_msg = await utils.get_Real_CUGAN(image, modelname)
        if error_msg:
            await bot.send(ev, f"图片超分失败：{error_msg}", at_sender=True)
            traceback.print_exc()
            return
        msg_list.append(f"放大倍率：{scale}倍\n降噪等级：{con_cn}\n使用模型：Real_CUGAN")
        msg_list.append(img_msg)
        await SendMessageProcess(bot, ev, msg_list) # 发送消息过程
    except Exception as e:
        await bot.send(ev, f"清晰术失败：{type(e)}", at_sender=True)
        traceback.print_exc()

async def img_Real_ESRGAN(bot, ev):
    try:
        msg_list = []
        image, _, _ = await utils.get_image_and_msg(bot, ev)
        if not image:
            await bot.send(ev, '请输入需要超分的图片', at_sender=True)
            return
        ix=image.size[0] # 获取图片宽度
        iy=image.size[1] # 获取图片高度
        if ix * iy > 1000000: # 图片像素大于100万像素的，会对其进行缩放
            image.thumbnail(size=(1000, 1000)) # 图片等比例缩放
            await bot.send(ev, f"图片尺寸超过100万像素，将对其进行缩放", at_sender=True)
        await bot.send(ev, f"正在使用Real-ESRGAN模型4倍超分图片，请稍后...")

        img_msg, error_msg = await utils.get_Real_ESRGAN(image)
        if error_msg:
            await bot.send(ev, f"图片超分失败：{error_msg}", at_sender=True)
            traceback.print_exc()
            return
        msg_list.append("放大倍率：4倍\n使用模型：Real-ESRGAN")
        msg_list.append(img_msg)
        await SendMessageProcess(bot, ev, msg_list) # 发送消息过程
    except Exception as e:
        await bot.send(ev, f"清晰术失败：{type(e)}", at_sender=True)
        traceback.print_exc()

@sv.on_prefix("元素法典")
async def magic_book(bot, ev):
    try:
        uid = ev['user_id']
        gid = ev['group_id']
        msg_list = []
        msg = ev.message.extract_plain_text().strip()
        tags, error_msg, node_msg, dark_msg = await magic.get_magic_book_(msg)
        if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
            return

        num = 1
        result, msg = check_lmt(uid, num, gid) # 检查群权限与个人次数
        if result != 0:
            await bot.send(ev, msg)
            return
        if dark_msg:
            await bot.send(ev, f"{dark_msg}正在进行魔法绘图，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)
        else:
            await bot.send(ev, f"元素法典已注入，正在进行魔法绘图，请稍后...\n(今日剩余{get_config('base', 'daily_max') - tlmt.get_num(uid)}次)", at_sender=True)

        result_msg,error_msg = await utils.get_imgdata_magic(tags)
        if len(error_msg):
            await bot.send(ev, f"已报错：{error_msg}", at_sender=True)
            return
        msg_list.append(result_msg)
        msg_list.append(node_msg)
        await SendMessageProcess(bot, ev, msg_list) # 发送消息过程
    except Exception as e:
        await bot.send(ev, f"已报错：{type(e)}", at_sender=True)
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
