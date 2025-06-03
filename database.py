import redis
import mysql.connector
import time
import json
from datetime import datetime
from typing import List, Tuple

def connect_to_database():
    """
    尝试优先连接 Redis，若无响应则回退连接 MySQL。
    返回 (connection, db_type)，其中 db_type 是 'redis' 或 'mysql'。
    """
    i=0##云数据库服务已到期，用此参数改为只用本地数据库
    # 1. 先尝试连接 Redis（3秒超时）
    if i==1:
        try:
            start_time = time.time()
            r = redis.Redis(
                host='192.168.0.71',
                port=6379,
                db=0,
                socket_timeout=1  # 关键：设置超时时间
            )
            r.ping()  # 测试连接是否有效
            end_time = time.time()
            print(f"{datetime.now().strftime('%H:%M:%S')} - Redis 连接成功！耗时 {end_time - start_time:.2f} 秒")
            return r, 'redis'
        except Exception as e:
            print(f"{datetime.now().strftime('%H:%M:%S')} - Redis 连接失败: {e}")

    # 2. 如果 Redis 失败，尝试连接 MySQL
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456",
            database="test"
        )
        print(f"{datetime.now().strftime('%H:%M:%S')} -  连接成功！")
        return conn, 'mysql'
    except mysql.connector.Error as err:
        print(f"{datetime.now().strftime('%H:%M:%S')} -  连接失败: {err}")
        return None, None

def write_into_database(userid,userchat,aichat):
    db_conn, db_type = connect_to_database()
    if not db_conn:
        print("数据库连接失败！")
        return False

    try:
        if db_type == 'redis':
            # Redis存储结构
            chat_data = {
                'userid': str(userid),
                'userchat': userchat,
                'aichat': aichat,
                'timestamp': time.time()
            }
            # 使用哈希存储，键名为 chat:用户ID:时间戳
            db_conn.hset(
                f"chat:{userid}:{int(time.time())}",
                mapping=chat_data
            )
            
        elif db_type == 'mysql':
            cursor = db_conn.cursor()
            # 确保chat表存在（简化版）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `chat` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `userid` VARCHAR(255) NOT NULL,
                    `userchat` LONGTEXT NOT NULL,
                    `aichat` LONGTEXT NOT NULL
                )
            """)
            # 插入数据
            cursor.execute("""
                INSERT INTO chat (userid, userchat, aichat)
                VALUES (%s, %s, %s)
            """, (str(userid), userchat, aichat))
            db_conn.commit()
            
        print(f"成功写入{db_type}数据库，用户ID: {userid}")
        return True
        
    except Exception as e:
        print(f"数据库写入失败: {str(e)}")
        return False
        
    finally:
        if db_conn:
            db_conn.close()

def get_latest_message(n,userid):
    db_conn, db_type = connect_to_database()
    if not db_conn:
        print("数据库连接失败！")
        return False
    try:
        if db_type == 'mysql':
            cursor = db_conn.cursor()
            query = """
                SELECT userchat, aichat 
                FROM chat 
                WHERE userid = %s 
                ORDER BY id DESC
                LIMIT %s
            """
            cursor.execute(query, (userid, n))
            result = cursor.fetchall()
            return result[::-1]
            
        elif db_type == 'redis':
            # 获取该用户的所有聊天键（格式: chat:{userid}:{id}）
            pattern = f"chat:{userid}:*"
            keys = db_conn.keys(pattern)
            
            # 按id降序排序（键名中的最后一段是id）
            sorted_keys = sorted(
                keys,
                key=lambda k: int(k.decode().split(':')[-1]),
                reverse=True
            )[:n]
            
            # 提取消息内容
            messages = [
                (
                    db_conn.hget(key, "userchat").decode(),
                    db_conn.hget(key, "aichat").decode()
                )
                for key in sorted_keys
            ]
            return messages[::-1]
            
    except Exception as e:
        print(f"查询失败: {str(e)}")
        return []
        
    finally:
        if cursor:
            cursor.close()
        if db_conn:
            db_conn.close()

if __name__ == '__main__':
    a=get_latest_message(2,1)