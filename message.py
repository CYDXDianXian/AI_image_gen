import asyncio
import traceback
import hoshino
from .config import get_config, get_group_config


def render_forward_msg(msg_list: list, uid=2854196306, name='会画画的小冰'):
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

async def SendMessageProcess(bot, ev, msg_list: list, withdraw = True):
	'''
	发送消息过程，并判断是否撤回
	'''
	gid = ev['group_id']

	result_list = await send_msg(msg_list, ev) # 发送消息过程并返回消息列表
	second = get_group_config(gid, "withdraw") # 获取撤回时间
	if withdraw:
		if second and second > 0: # 判断是否撤回
			await asyncio.sleep(second)
			for result in result_list:
				try:
					await bot.delete_msg(self_id=ev['self_id'], message_id=result['message_id'])
				except:
					traceback.print_exc()
					hoshino.logger.error('[ERROR]撤回失败')
				await asyncio.sleep(1)