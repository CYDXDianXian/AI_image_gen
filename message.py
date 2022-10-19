import asyncio
import traceback
import hoshino
from .config import get_config


def render_forward_msg(msg_list: list, uid=2854196306, name='小冰'):
	forward_msg = []
	for msg in msg_list:
		forward_msg.append({
			"type": "node",
			"data": {
				"name": str(name),
				"uin": str(uid),
				"content": msg
			}
		})
	return forward_msg

async def send_msg(msg_list, ev):
	result_list = []
	if not get_config('base', 'enable_forward_msg'):
		for msg in msg_list:
			try:
				result_list.append(await hoshino.get_bot().send(ev, msg))
			except:
				hoshino.logger.error('[ERROR]图片发送失败')
				await hoshino.get_bot().send(ev, f'涩图太涩,发不出去力...')
			await asyncio.sleep(1)
	else:
		forward_msg = render_forward_msg(msg_list)
		try:
			result_list.append(await hoshino.get_bot().send_group_forward_msg(group_id=ev.group_id, messages=forward_msg))
		except:
			traceback.print_exc()
			hoshino.logger.error('[ERROR]图片发送失败')
			await hoshino.get_bot().send(ev, f'涩图太涩,发不出去力...')
		await asyncio.sleep(1)
	return result_list