# 以下是默认配置，仅用作注释参考和生成默认配置文件，请不要在这里修改，请在config.json文件中修改配置才能生效！！！
config_default = {
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
