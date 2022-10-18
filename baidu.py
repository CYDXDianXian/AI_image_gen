from hoshino import aiorequests
import string
import time
import hashlib
import json
from .config import get_config
 
#init
baidu_api = get_config('baidu', 'baidu_api')
baidu_appid = get_config('baidu', 'baidu_appid')
baidu_key = get_config('baidu', 'baidu_key')
lower_case = list(string.ascii_lowercase)

def isContainChinese(s):
    for c in s:
        if ('\u4e00' <= c <= '\u9fa5'):
            return True
    return False

async def baiduTranslate(word):
    #init salt and final_sign
    salt = str(time.time())[:10]
    final_sign = str(baidu_appid)+word+salt+baidu_key
    final_sign = hashlib.md5(final_sign.encode("utf-8")).hexdigest()
    #区别en,zh构造请求参数
    if list(word)[0] in lower_case:
        paramas = {
            'q':word,
            'from':'en',
            'to':'zh',
            'appid':'%s'%baidu_appid,
            'salt':'%s'%salt,
            'sign':'%s'%final_sign
            }
        my_url = baidu_api+'?appid='+str(baidu_appid)+'&q='+word+'&from='+'en'+'&to='+'zh'+'&salt='+salt+'&sign='+final_sign
    else:
        paramas = {
            'q':word,
            'from':'zh',
            'to':'en',
            'appid':'%s'%baidu_appid,
            'salt':'%s'%salt,
            'sign':'%s'%final_sign
            }
        my_url = baidu_api+'?appid='+str(baidu_appid)+'&q='+word+'&from='+'zh'+'&to='+'en'+'&salt='+salt+'&sign='+final_sign
    response = await (await aiorequests.get(baidu_api,params = paramas)).content
    content = str(response,encoding = "utf-8")
    json_reads = json.loads(content)
    return json_reads['trans_result'][0]['dst']

async def tag_baiduTrans(tags):
    if(isContainChinese(tags)):
        tags = await baiduTranslate(tags)
    return tags