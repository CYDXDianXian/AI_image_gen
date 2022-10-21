import os
import sqlite3

XP_DB_PATH = os.path.expanduser('~/.hoshino/AI_image_xp2.db')
class XpCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(XP_DB_PATH), exist_ok=True)
        self._create_table()

    def _connect(self):
        return sqlite3.connect(XP_DB_PATH)

    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS XP_NUM
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           KEYWORD         TEXT   NOT NULL,
                           NUM             INT    NOT NULL,
                           PRIMARY KEY(GID,UID,KEYWORD));''')
        except:
            raise Exception('创建表发生错误')

    def _add_xp_num(self, gid, uid, keyword):
        try:
            num = self._get_xp_num(gid, uid, keyword)
            if num == None:
                num = 0
            num += 1
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO XP_NUM (GID,UID,KEYWORD,NUM) \
                                VALUES (?,?,?,?)", (gid, uid, keyword, num)
                )
        except:
            raise Exception('更新表发生错误')

    def _get_xp_num(self, gid, uid, keyword):
        try:
            r = self._connect().execute("SELECT NUM FROM XP_NUM WHERE GID=? AND UID=? AND KEYWORD=?", (gid, uid, keyword)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找表发生错误')


    def _get_xp_list_group(self, gid, num):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT KEYWORD,NUM FROM XP_NUM WHERE GID={gid} ORDER BY NUM desc LIMIT {num}").fetchall()
        return r if r else {}

    def _get_xp_list_personal(self, gid, uid, num):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT KEYWORD,NUM FROM XP_NUM WHERE GID={gid} AND UID={uid} ORDER BY NUM desc LIMIT {num}").fetchall()
        return r if r else {}

    def _get_xp_list_kwd_group(self, gid, num):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT KEYWORD FROM XP_NUM WHERE GID={gid} ORDER BY NUM desc LIMIT {num}").fetchall()
        return r if r else {}

    def _get_xp_list_kwd_personal(self, gid, uid, num):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT KEYWORD FROM XP_NUM WHERE GID={gid} AND UID={uid} ORDER BY NUM desc LIMIT {num}").fetchall()
        return r if r else {}

def get_xp_list_group(gid,num=20):
    XP = XpCounter()
    xp_list = XP._get_xp_list_group(gid, num)
    if len(xp_list)>0:
        data = sorted(xp_list,key=lambda cus:cus[1],reverse=True)
        new_data = []
        for xp_data in data:
            keyword, num = xp_data
            new_data.append((keyword,num))
        rankData = sorted(new_data,key=lambda cus:cus[1],reverse=True)
        return rankData
    else:
        return []

def get_xp_list_personal(gid,uid,num=20):
    XP = XpCounter()
    xp_list = XP._get_xp_list_personal(gid,uid,num)
    if len(xp_list)>0:
        data = sorted(xp_list,key=lambda cus:cus[1],reverse=True)
        new_data = []
        for xp_data in data:
            keyword, num = xp_data
            new_data.append((keyword,num))
        rankData = sorted(new_data,key=lambda cus:cus[1],reverse=True)
        return rankData
    else:
        return []

def get_xp_list_kwd_group(gid,num=10):
    XP = XpCounter()
    xp_list_kwd = XP._get_xp_list_kwd_group(gid, num)
    if len(xp_list_kwd)>0:
        return xp_list_kwd
    else:
        return []

def get_xp_list_kwd_personal(gid,uid,num=10):
    XP = XpCounter()
    xp_list_kwd = XP._get_xp_list_kwd_personal(gid,uid,num)
    if len(xp_list_kwd)>0:
        return xp_list_kwd
    else:
        return []


def add_xp_num(gid,uid,keyword):
    XP = XpCounter()
    XP._add_xp_num(gid,uid,keyword)

##########################以下是setu_pic的内容###################################
PIC_DB_PATH = os.path.expanduser('~/.hoshino/AI_image_pic.db')
class PicCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(PIC_DB_PATH), exist_ok=True)
        self._create_table()
        self._create_index()

    def _connect(self):
        return sqlite3.connect(PIC_DB_PATH)

    def _create_table(self):
        try:
            self._connect().execute('''
            CREATE TABLE IF NOT EXISTS PIC_DATA(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                GID             INT   NOT NULL,
                UID             INT   NOT NULL,
                PIC_HASH        TEXT   NOT NULL,
                PIC_DIR         TEXT   NOT NULL,
                PIC_MSG         TEXT   NOT NULL,
                THUMB           INT    NOT NULL
                );''')
        except Exception as e:
            raise e

    def _create_index(self):
        try:
            self._connect().execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS hash ON
                PIC_DATA (
                PIC_HASH
                );''')
        except Exception as e:
            raise e

    def _add_pic(self, gid, uid, pic_hash, pic_dir, pic_msg, thumb): #增加数据
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO PIC_DATA (GID,UID,PIC_HASH,PIC_DIR,PIC_MSG,THUMB) \
                                VALUES (?,?,?,?,?,?)", [gid, uid, pic_hash, pic_dir, pic_msg, thumb]
                )
        except Exception as e:
            raise e

    def _del_pic(self, id): #删除数据
        try:
            with self._connect() as conn:
                conn.execute(
                    f"DELETE FROM PIC_DATA WHERE ID =?",[id]
                )
        except Exception as e:
            raise e

    def _get_pic_exist_hash(self, pic_hash): #通过hash值来判断图片是否存在，存在1，不存在0
        try:
            r = self._connect().execute(f"SELECT PIC_HASH FROM PIC_DATA WHERE PIC_HASH=?",[pic_hash]).fetchone()
            return 0 if r is None else 1
        except Exception as e:
            raise e

    def _get_pic_exist_id(self, id): #通过id来判断图片是否存在，存在1，不存在0
        try:
            r = self._connect().execute(f"SELECT PIC_HASH FROM PIC_DATA WHERE ID=?",[id]).fetchone()
            return 0 if r is None else 1
        except Exception as e:
            raise e

    def _get_pic_data_id(self, id): #通过自增的ID获取图片信息 路径和msg
        try:
            r = self._connect().execute("SELECT PIC_DIR,PIC_MSG FROM PIC_DATA WHERE ID=?", [id]).fetchone()
            return r if r else {}
        except Exception as e:
            raise e

    def _get_pic_id_hash(self, pic_hash): #通过图片hash获取ID
        try:
            r = self._connect().execute(f"SELECT ID FROM PIC_DATA WHERE PIC_HASH=?",[pic_hash]).fetchone()
            return r if r else {}
        except Exception as e:
            raise e

    def _get_pic_thumb(self, id): #通过自增的ID获取图片信息 thumb
        try:
            r = self._connect().execute("SELECT THUMB FROM PIC_DATA WHERE ID=?", [id]).fetchone()
            return 0 if r is None else r[0]
        except Exception as e:
            raise e

    def _add_pic_thumb(self, id):
        try:
            num = self._get_pic_thumb(id)
            num += 1
            with self._connect() as conn:
                conn.execute(
                    f"UPDATE PIC_DATA SET THUMB =? WHERE ID =?",[num,id]
                )
        except Exception as e:
            raise e

    def _get_pic_list_all(self, num):
        try:
            with self._connect() as conn:
                r = conn.execute(
                    f"SELECT ID,PIC_DIR,THUMB FROM PIC_DATA ORDER BY THUMB desc LIMIT {num}").fetchall()
            return r if r else {}
        except Exception as e:
            raise e

    def _get_pic_list_group(self, gid, num):
        try:
            with self._connect() as conn:
                r = conn.execute(
                    f"SELECT ID,PIC_DIR,THUMB FROM PIC_DATA WHERE GID=? ORDER BY THUMB desc LIMIT {num}",[gid]).fetchall()
            return r if r else {}
        except Exception as e:
            raise e

    def _get_pic_list_personal(self, uid, num):
        try:
            with self._connect() as conn:
                r = conn.execute(
                    f"SELECT ID,PIC_DIR,THUMB FROM PIC_DATA WHERE UID=? ORDER BY THUMB desc LIMIT {num}",[uid]).fetchall()
            return r if r else {}
        except Exception as e:
            raise e


def add_pic(gid, uid, pic_hash, pic_dir, pic_msg):
    PC = PicCounter()
    if not PC._get_pic_exist_hash(pic_hash):
        PC._add_pic(gid, uid, pic_hash, pic_dir, pic_msg,0)
        return "上传图片成功"
    return "上传图片失败，图片已存在"

def get_pic_exist_hash(pic_hash):
    PC = PicCounter()
    return PC._get_pic_exist_hash(pic_hash)

def add_pic_thumb(id):
    PC = PicCounter()
    if PC._get_pic_exist_id(id):
        PC._add_pic_thumb(id)
        return f"点赞【{id}】号图片成功"
    return f"点赞【{id}】号图片失败，该图片不存在！"


def get_pic_id_hash(pic_hash):
    PC = PicCounter()
    id = PC._get_pic_id_hash(pic_hash)
    return id

def get_pic_data_id(id):
    PC = PicCounter()
    r = PC._get_pic_data_id(id)
    return r

def get_pic_list_all(num=8):
    PC = PicCounter()
    r = PC._get_pic_list_all(num)
    return r

def get_pic_list_group(gid,num=8):
    PC = PicCounter()
    r = PC._get_pic_list_group(gid, num)
    return r

def get_pic_list_personal(uid,num=8):
    PC = PicCounter()
    r = PC._get_pic_list_personal(uid, num)
    return r

def del_pic(id):
    PC = PicCounter()
    r = PC._del_pic(id)
    return "remove pic success"