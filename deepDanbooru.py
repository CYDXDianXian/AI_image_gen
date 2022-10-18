import io
import base64
import random
from hoshino import aiorequests


def generate_code(code_len=6):
    all_char = '0123456789qazwsxedcrfvtgbyhnujmikolp'
    index = len(all_char) - 1
    code = ''
    for _ in range(code_len):
        num = random.randint(0, index)
        code += all_char[num]
    return code


async def fetch_data(_hash, max_retry_num=5):
    url_status = 'https://hf.space/embed/hysts/DeepDanbooru/api/queue/status/'
    resj = await (await aiorequests.post(url_status, json={'hash': _hash})).json()
    retrying = 0
    while True:
        if retrying >= max_retry_num:
            return None
        if resj['status'] == 'PENDING':
            retrying += 1
            continue
        elif resj['status'] == 'COMPLETE':
            return resj['data']['data'][0]['confidences']
        else:
            return None


async def get_tags(image):
    url_push = 'https://hf.space/embed/hysts/DeepDanbooru/api/queue/push/'

    params = {
        "fn_index": 0,
        "data": [],
        "session_hash": generate_code(11),
        "action": "predict"
    }

    imageData = io.BytesIO()
    image.save(imageData, format='PNG')
    params['data'] = ['data:image/png;base64,' + str(base64.b64encode(imageData.getvalue()))[2:-1], 0.5]  # 0.5的阈值
    _hash = (await (await aiorequests.post(url_push, json=params)).json())['hash']
    resj = await fetch_data(_hash)
    return resj
