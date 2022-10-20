from PIL import Image
from io import BytesIO
from base64 import b64encode, b64decode
from .utils import generate_code
from hoshino import aiorequests


async def up_sampling(img):
    url_push = 'https://hf.space/embed/akhaliq/Real-ESRGAN/api/predict/'

    params = {
        "fn_index": 0,
        "data": [],
        "session_hash": generate_code(11),
    }

    imageData = BytesIO()
    img.save(imageData, format='PNG')
    params['data'] = ['data:image/png;base64,' + str(b64encode(imageData.getvalue()))[2:-1], "anime"]
    res = await (await aiorequests.post(url_push, json=params)).json()
    if 'data' in res:
        result_img = b64decode(''.join(res['data'][0].split(',')[1:]))
        result_img = Image.open(BytesIO(result_img)).convert("RGB")
        buffer = BytesIO()  # 创建缓存
        result_img.save(buffer, format="png")
        img_msg = 'base64://' + b64encode(buffer.getvalue()).decode()
        return img_msg
    else:
        return None
