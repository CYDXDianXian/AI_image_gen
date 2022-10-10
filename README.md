# AI_image_gen
 AI绘图hoshinobot插件版

仓库地址：https://github.com/CYDXDianXian/AI_image_gen

感谢群友上传的各种版本的AI绘图，这里缝合了一些实用功能进去，以后会看情况缝合更多的功能~

## 特点

- 根据tag绘制图片，根据tag+图片绘制图片
- XP查询
- 每日上限和频率限制（维护组不会被限制）
- 可设置群黑/白名单
- 可屏蔽群人数超过一定数量的大群
- 可自行设置屏蔽词，屏蔽某些tag后会使bot出图更加安全健康（维护组不会被限制）

## 配置方法

1. 在`...HoshinoBot\hoshino\modules`目录下克隆该仓库：

   ```
   git https://github.com/CYDXDianXian/AI_image_gen.git
   ```

2. 更改配置文件`config.json`：

   在`api`中填写IP地址

   在`token`中填写你的token

   ```python
   {
       "base": {
           "daily_max": 20,  # 每日上限次数
           "freq_limit": 60,  # 频率限制
           "whitelistmode": False,  # 白名单模式开关
           "blacklistmode": True,  # 黑名单模式开关
           "ban_if_group_num_over": 1000  # 屏蔽群人数过1000人的群
       },
       "NovelAI": {
           "api": "",  # 设置api，例如："11.222.333.444:5555"
           "token": ""  # 设置你的token，例如："ADGdsvSFGsaA5S2D"
       },
       "ban_word": {
           "wordlist": ["r18", "naked", "vagina", "penis", "nsfw", "genital", "nude", "NSFW", "R18", "NAKED", "VAGINA", "PENIS", "GENITAL", "NUDE"]
       }  # 屏蔽词列表
   }
   ```

   注意，只有在`config.json`中更改配置才会生效，请不要修改`__init__.py`中的默认配置信息

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

| 指令                                    | 说明                                                         |
| --------------------------------------- | ------------------------------------------------------------ |
| ai绘图/生成涩图+tag                     | 关键词仅支持英文，用逗号隔开                                 |
| 以图绘图/以图生图+tag+图片              | 注意图片尽量长宽都在765像素以下，不然会被狠狠地压缩          |
| 我的XP/我的xp                           | 查询你使用的tag频率                                          |
| {}                                      | 关键词上加{}代表增加权重,可以加很多个,有消息称加入英语短句识别 |
| **可选参数**                            |                                                              |
| &shape=Portrait/Landscape/Square        | 默认Portrait竖图                                             |
| &scale=11                               | 默认11,只建议11-24,细节会提高,太高了会过曝                   |
| &seed=1111111                           | 如果想在返回的原图上修改,加入seed使图片生成结构类似          |
| **以下为维护组使用**                    |                                                              |
| 绘图 黑/白名单 新增/添加/移除/删除 群号 | 修改黑白名单(空格不能漏)                                     |
| 黑名单列表/白名单列表                   | 查询黑白名单列表                                             |

## 其他说明

- 目前API都为私人搭建，你需要一个拥有有效付费计划的 [NovelAI](https://novelai.net/) 账号，本插件只使用 [NovelAI](https://novelai.net/) 搭建的API所提供的接口。付费计划请自行前往 [NovelAI](https://novelai.net/) 了解。(别问怎么搭建API，我很菜，我也不会QAQ，其他地方应该有教程的吧！）

## 使用效果预览

![image](https://user-images.githubusercontent.com/71607036/194919204-d3a3e4aa-05b4-4d5c-a0de-76a9d7b62b6e.png)

![image](https://user-images.githubusercontent.com/71607036/194919518-f6dbd175-45f7-404a-b9ea-59ff70bb4d6a.png)

![image](https://user-images.githubusercontent.com/71607036/194919615-8ac42e62-77dc-463c-b373-9b2819f56d2a.png)

