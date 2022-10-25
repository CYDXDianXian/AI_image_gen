# AI_image_gen
 AI绘图HoshinoBot插件版

仓库地址：https://github.com/CYDXDianXian/AI_image_gen

感谢 [sans](https://github.com/sanshanya) 老师、[Cath]() 老师、 [兰鹿](https://github.com/BlueDeer233) 以及各群友上传的代码，这里主要对群友上传的各个版本代码进行了缝合


## 注意事项

- **2022-10-22版本更新后，旧配置文件`config.json`与新版无法兼容，请备份好个人api和token数据后删除`config.json`文件，再使用`git pull`命令从仓库拉取更新，获取配置文件模板`config_example.json`后按文档后面提到的配置方法进行操作。若您在使用过程中发生报错，请检查配置文件是否已更新**

- **若出现 `ImportError: No module named xxx` 报错，请重装依赖：在插件目录下运行powershell输入`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`**

- **若仓库更新遇到问题，请删除AI_image_gen目录后重新克隆仓库（注意删除前先将`SaveImage`文件夹和`config.json`文件备份好，若不慎删除出现找不到图片路径的报错，请一并删除 `~\.hoshino\AI_image_pic.db` 文件来解决报错问题）：**

  ```
  # 在...HoshinoBot\hoshino\modules目录下删除旧AI_image_gen目录重新克隆该仓库：
  git clone https://github.com/CYDXDianXian/AI_image_gen.git
  ```
  
- **2022-10-20版本开始，新上传图片的保存路径移至Hoshinobot资源目录下：`...HoshinoBot\res\img\AI_setu`**

## 特点

- [x] 根据tag绘制图片，根据tag+图片绘制图片
- [x] 接入有道翻译和百度翻译，可自动将中文tag翻译为英文
- [x] 图片超分（清晰术！默认使用Real-CUGAN模型四倍超分图片）
- [x] 图片二次元化
- [x] 元素法典咏唱
- [x] 上传AI生成的图片及其配方
- [x] 查看个人/本群/全部群图片
- [x] 查看已上传图片的配方
- [x] 使用已上传图片的配方进行快捷绘图
- [x] 删除已上传图片（仅限维护组使用）
- [x] 本群或个人XP查询
- [x] 本群或个人XP缝合
- [x] 每日上限和频率限制（维护组不会被限制）
- [x] 撤回时间/tags整理/数据录入/中英翻译/违禁词过滤 开关控制
- [x] 可设置群黑/白名单
- [x] 可屏蔽群人数超过一定数量的大群
- [x] 可自行设置屏蔽词，屏蔽某些tag后会使bot出图更加安全健康，tag会自动转为小写
- [x] 图片鉴赏功能
- [x] 转发消息模式
- [x] 自动撤回消息
- [x] 回复消息进行以图绘图/上传图片/图片鉴赏/清晰术/二次元化
- [x] 更改配置文件无需重启bot

## 配置方法

1. 在`...HoshinoBot\hoshino\modules`目录下克隆该仓库：

   ```
   git clone https://github.com/CYDXDianXian/AI_image_gen.git
   ```

2. 将本插件目录下的配置文件模板 `config.template.json` 复制并重命名为 `config.json` ,并进行如下设置：

   > **Warning** \
   > 只有**在`config.json`中更改配置**才会生效，**请不要修改`default_config.py`中**的默认配置信息！
   
   - 在`api`中填写IP地址
   - 在`token`中填写你的token
   - 【可选】在`baidu_appid`中填写自己的[百度翻译](https://api.fanyi.baidu.com/)APP ID，不填使用内置百度翻译
   - 【可选】在`baidu_key`填写自己的[百度翻译](https://api.fanyi.baidu.com/)密钥，不填使用内置百度翻译
   - 【可选】在`app_id`中填写自己的[有道智云](https://ai.youdao.com/)应用id，不填使用内置有道翻译
   - 【可选】在`app_key`中填写自己的[有道智云](https://ai.youdao.com/)应用秘钥，不填使用内置有道翻译
   
   百度翻译与有道翻译二选一即可，不用的翻译可以关掉。（建议使用百度翻译，对二次元词汇翻译效果较好，如何获取API请翻阅文档后半部分的**API说明**）

   配置文件`config.json`中的选项都可以依据个人喜好进行更改，但请不要更改配置文件以外的任何文件，否则容易造成程序运行出错！

   ```python
   {
       "base": {
           "daily_max": 20,  # 每日上限次数
           "freq_limit": 60,  # 频率限制
           "whitelistmode": False,  # 白名单模式开关
           "blacklistmode": True,  # 黑名单模式开关
           "ban_if_group_num_over": 1000,  # 屏蔽群人数超过1000人的群
           "enable_forward_msg": True,  # 是否开启转发消息模式
           "per_page_num": 28 # 用于查看图片时，每页最多有多少张图
       },
       "default": {
           "withdraw": 0,  # 撤回时间，单位秒。设置为0即为不撤回
           "arrange_tags": True,  # 是否开启tags整理
           "add_db": True,  # 是否开启XP数据录入
           "trans": True,  # 是否开启翻译
           "limit_word": True  # 是否开启违禁词过滤
       },
       "NovelAI": {
           "api": "",  # 设置api，例如："http://11.222.333.444:5555/"，结尾的/不能漏
           "token": "",  # 设置你的token，例如："ADGdsvSFGsaA5S2D"，（若你的api无需使用token，留空即可）
           "strength": "0.60" # Denoising strength 与原图的关联程度，越小关联越大
       },
       "baidu": {
           "baidu_trans": True,  # 百度翻译开关
           "baidu_api": "https://fanyi-api.baidu.com/api/trans/vip/translate",  # 百度api地址
           "baidu_appid": "",  # 【可选】自己的百度翻译APP ID，不填使用内置百度翻译
           "baidu_key": ""  # 【可选】自己的百度翻译密钥，不填使用内置百度翻译
       },
       "youdao": {
           "youdao_trans": False,  # 有道翻译开关
           "youdao_api": "https://openapi.youdao.com/api",  # 有道api地址
           "app_id": "",  # 【可选】自己的有道智云应用id，不填使用内置有道翻译
           "app_key": ""  # 【可选】自己的有道智云应用秘钥，不填使用内置有道翻译
       },
       "image4x": {
           "Real-CUGAN": True, # Real-CUGAN超分模型开关，可支持2、3、4倍超分，更锐利的线条，更好的纹理保留，虚化区域保留
           "Real-CUGAN-api": "http://134.175.32.157:9999/api/predict", # Real-CUGAN的api地址。目前接入的是奥帝努斯大佬的GPU服务器，速度更快！
           "Real-ESRGAN": False, # 目前存在bug（图片尺寸过大生成的图会很小），故暂时不建议开启
           "Real-ESRGAN-api": "https://hf.space/embed/akhaliq/Real-ESRGAN/+/api/predict/" # Real-ESRGAN的api地址
       },
       "default_tags": {
           "tags": "miku"  # 如果没有指定tag的话，默认的tag
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
               "R18"
           ]
       },  # 屏蔽词列表
   }
   ```
   
3. 安装依赖：

   ```
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

4. 在`hoshino/config/__bot__.py`文件中，`MODULES_ON`里添加 "AI_image_gen"

5. 运行Hoshinobot

6. 更新插件：

   请在你的 `hoshino/modules/AI_image_gen` 文件夹里，打开powershell输入 `git pull` ，运行完重启hoshinobot即可

## 使用方法

注：+ 号不用输入

| 指令                                                         | 说明                                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| ai绘图帮助                                                   | 获取本插件全部功能的使用说明                                 |
| ai绘图/生成涩图+tag                                          | 关键词仅支持英文，用逗号隔开                                 |
| 以图绘图/以图生图+tag+图片                                   | 注意图片尽量长宽都在765像素以下，不然会被狠狠地压缩          |
| 清晰术/上采样+图片                                           | 图片超分(默认四倍放大三倍降噪)                               |
| 清晰术+2倍/3倍/4倍放大+不/保守/强力降噪                      | 图片放大倍率与降噪倍率选项                                   |
| 二次元化/动漫化+图片                                         | 照片二次元化                                                 |
| 元素法典 xxx                                                 | xxx可以是多种魔咒，空格分离                                  |
| 元素法典咏唱/吟唱 xxx                                        | 发动黑暗法典，多种魔咒用空格分离                             |
| 上传pic/上传图片                                             | 务必携带seed/scale/tags等参数                                |
| 查看配方/查看tag+图片ID                                      | 查看已上传图片的配方                                         |
| 快捷绘图+图片ID                                              | 使用已上传图片的配方进行快捷绘图                             |
| 查看个人pic/查看个人图片+页码                                | 查看个人已上传的图片                                         |
| 查看本群pic/查看本群图片+页码                                | 查看本群已上传的图片                                         |
| 查看全部pic/查看全部图片+页码                                | 查看全部群已上传的图片                                       |
| 点赞pic/点赞图片+图片ID                                      | 对已上传图片进行点赞                                         |
| 删除pic/删除图片+图片ID                                      | 删除对应图片和配方(仅限维护组使用)                           |
| 本群/个人XP排行                                              | 本群/个人的tag使用频率                                       |
| 本群/个人XP缝合                                              | 缝合tags进行绘图                                             |
| 图片鉴赏/生成tag+图片                                        | 根据上传的图片生成tags                                       |
| 回复消息+以图绘图/上传图片/图片鉴赏/清晰术/二次元化          | 回复消息使用上述功能                                         |
| **以下为维护组使用**（空格不能漏）                           |                                                              |
| 绘图 状态 [群号]                                             | 查看本群或指定群的模块开启状态                               |
| 绘图 设置 撤回时间 0~999 [群号]                              | 设置本群或指定群撤回时间(单位秒)，0为不撤回                  |
| 绘图 设置 tags整理/数据录入/中英翻译/违禁词过滤 启用/关闭 [群号] | 启用/关闭本群或指定群的对应模块                              |
| 绘图 黑/白名单 新增/添加/移除/删除 群号                      | 修改黑白名单                                                 |
| 黑名单列表/白名单列表                                        | 查询黑白名单列表                                             |
| **参数使用说明**                                             |                                                              |
| {}                                                           | 关键词上加{}代表增加权重,可以加很多个                        |
| []                                                           | 关键词上加[]代表减少权重,可以加很多个                        |
| &shape=Portrait/Landscape/Square                             | 默认Portrait竖图。Landscape(横图)，Square(方图)              |
| &scale=11                                                    | 默认11，赋予AI自由度的参数，越高表示越遵守tags，一般保持11左右不变 |
| &seed=1111111                                                | 随机种子。在其他条件不变的情况下，相同的种子代表生成相同的图 |

参数用法示例：

![image](https://user-images.githubusercontent.com/71607036/195133884-d4c2a8cf-3853-4bce-b1e4-d2229f51f193.png)

![image](https://user-images.githubusercontent.com/71607036/195134222-6e7c68d4-62c0-4870-89ed-38ae5d733aa1.png)

## API说明

> 目前可用的NovelAI-API：[路路佬的API](https://lulu.uedbq.xyz/token)

> 如何使用翻译？（注：百度翻译二次元词汇比有道效果好一点）

- 方案一：内置翻译器[可选 百度/有道]
  1. 在配置文件启用你需要的翻译
  2. 无需填写API ID和密钥即可开始使
  3. 注意单次翻译字符上限为5000，次数无限，若魔法咏唱的tag超过字符数请选择方案二：API调用

- 方案二：API调用[可选 百度/有道]
  1. 若使用百度翻译API：使用您的百度账号登录[百度翻译开放平台](http://api.fanyi.baidu.com/)
  2. 注册成为开发者，获得 APPID
  3. 进行开发者认证（如仅需标准版可跳过）【仅需实名注册一下就可以使用高级版，建议认证。高级版免费调用量为100万字符/月】
  4. 开通通用翻译API服务：[开通链接](https://fanyi-api.baidu.com/choose)
  5. 在管理控制台中查看APP ID与密钥，将其填入配置文件对应的位置
  6. 若使用有道翻译API：请访问[有道智云](https://ai.youdao.com/)注册账号，在控制台中以API接入方式创建一个文本翻译应用，查看应用即可获取有道应用ID和应用秘钥，然后将其填写至配置文件即可使用有道翻译服务

## 使用效果预览

![image](https://user-images.githubusercontent.com/71607036/194919204-d3a3e4aa-05b4-4d5c-a0de-76a9d7b62b6e.png)

![image](https://user-images.githubusercontent.com/71607036/197311100-ea6ff357-4b57-4901-ba71-0c00ffc12ea6.png)

![image](https://user-images.githubusercontent.com/71607036/195683770-64954eac-bc68-4138-bf40-e99dee93e73c.png)

![image](https://user-images.githubusercontent.com/71607036/195686419-21bb5cc6-1928-454b-9c38-21f0011d1173.png)

![image](https://user-images.githubusercontent.com/71607036/195681878-e31d1162-9d0d-4899-80c9-e9f49d52b85f.png)

![image](https://user-images.githubusercontent.com/71607036/195682116-2b75e1af-68ff-42e2-a519-2398922a531b.png)

![image](https://user-images.githubusercontent.com/71607036/195219903-e22d4c3b-1357-4da1-bb7e-8441fb575db4.png)

![image](https://user-images.githubusercontent.com/71607036/195219944-59930139-46d6-474e-8262-de4711fffcee.png)

![image](https://user-images.githubusercontent.com/71607036/195219976-a4a9d82b-a1d5-4ff9-912a-9ea808d90a75.png)

![image](https://user-images.githubusercontent.com/71607036/196759011-cf5e6782-1a65-4e8c-9801-2bb2465bd9a1.png)
![image](https://user-images.githubusercontent.com/71607036/196759036-59b3151a-af47-4209-b7c3-c661fc05d661.png)

## 鸣谢

[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)

[HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot)

[setu_renew](https://github.com/pcrbot/setu_renew)

[Hugging Face](https://huggingface.co/)

[DeepDanbooru](https://github.com/KichangKim/DeepDanbooru)

[Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)

[White-box-Cartoonization](https://github.com/SystemErrorWang/White-box-Cartoonization)

## 友情链接

[ai_setu - sans](https://github.com/pcrbot/ai_setu)

[ai绘图安全版 - 姬野梦美](https://github.com/jiyemengmei/AI_Draw_safemode)

## 更新日志

2022-10-25：新增元素法典功能，优化图片超分、图片鉴赏、二次元化相关代码，解决功能使用不稳定问题

2022-10-23：优化图片处理逻辑，提高bot收发图片的速度

2022-10-22：清晰术功能更新，接入Real_CUGAN图片超分api，更新分群管理配置功能

2022-10-21：初步优化代码结构，重构消息发送模块，解决：以图绘图bug、图片上传重复问题、查看已上传图片时图片发送失败问题

2022-10-20：新增不用申请APIKEY的内置[翻译](https://github.com/azmiao/translator_lite)，新增清晰术（图片超分）和图片二次元化

2022-10-20：新增转发消息模式；新增自动撤回消息功能；图片鉴赏直接生成文字版tags，方便复制；修复回复上传、回复以图绘图、回复图片鉴赏的bug

2022-10-16：新增回复消息以图绘图、上传图片、生成tags功能

2022-10-15：新增图片鉴赏功能，将帮助说明转为图片发送

2022-10-14：新增快捷绘图，查看已上传的图片配方，查看个人/本群/全部图片，删除上传的图片，接入百度翻译API

2022-10-12：新增自动将中文tag翻译为英文功能，新增XP缝合，新增上传、查看和点赞本群图片，新增tags整理/数据录入/中英翻译/违禁词过滤 开关控制，屏蔽词列表更新

2022-10-11：新增XP查询，修改API接口格式

2022-10-10：初次提交
