import asyncio
from PIL import Image
from io import BytesIO
from base64 import b64encode, b64decode
from .utils import generate_code
from hoshino import aiorequests


async def fetch_data(_hash, max_retry_num=15):
    url_status = 'https://hf.space/embed/hylee/White-box-Cartoonization/api/queue/status/'
    resj = await (await aiorequests.post(url_status, json={'hash': _hash})).json()
    retrying = 0
    while True:
        if retrying >= max_retry_num:
            return None
        if resj['status'] == 'PENDING':
            retrying += 1
            await asyncio.sleep(1)
            continue
        elif resj['status'] == 'COMPLETE':
            result_img = b64decode(''.join(resj['data']['data'][0].split(',')[1:]))
            result_img = Image.open(BytesIO(result_img)).convert("RGB")
            buffer = BytesIO()  # 创建缓存
            result_img.save(buffer, format="png")
            img_msg = 'base64://' + b64encode(buffer.getvalue()).decode()
            return img_msg


async def cartoonization(image):
    url_push = 'https://hf.space/embed/hylee/White-box-Cartoonization/api/queue/push/'

    params = {
        "data": [],
        "cleared": False,
        "session_hash": generate_code(11),
        "action": "predict",
        "example_id": None,
    }

    imageData = BytesIO()
    image.save(imageData, format='PNG')
    params['data'] = ['data:image/png;base64,' + str(b64encode(imageData.getvalue()))[2:-1]]  # 0.5的阈值
    _hash = (await (await aiorequests.post(url_push, json=params)).json())['hash']
    resj = await fetch_data(_hash)
    return resj
