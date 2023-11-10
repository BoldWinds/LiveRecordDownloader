import logging
import os
import sys
import time
import subprocess
import threading

from config import *
from start_record import start_record


def change_max_connect(warning_count=0):
    max_request = 4
    # 动态控制连接次数
    preset = max_request
    # 记录当前时间
    start_time = time.time()

    while True:
        time.sleep(5)
        if 10 <= warning_count <= 20:
            if preset > 5:
                max_request = 5
            else:
                max_request //= 2  # 将max_request除以2（向下取整）
                if max_request > 0:  # 如果得到的结果大于0，则直接取该结果
                    max_request = preset
                else:  # 否则将其设置为1
                    preset = 1

            print("同一时间访问网络的线程数动态改为", max_request)
            warning_count = 0
            time.sleep(5)

        elif 20 < warning_count:
            max_request = 1
            print("同一时间访问网络的线程数动态改为", max_request)
            warning_count = 0
            time.sleep(10)

        elif warning_count < 10 and time.time() - start_time > 60:
            max_request = preset
            warning_count = 0
            start_time = time.time()
            print("同一时间访问网络的线程数动态改为", max_request)


def main():
    # --------------------------检测是否存在ffmpeg-------------------------------------
    ffmpeg_file_check = subprocess.getoutput(["ffmpeg"])
    if ffmpeg_file_check.find("run") > -1:
        # print("ffmpeg存在")
        pass
    else:
        print("重要提示:")
        input("检测到ffmpeg不存在,请将ffmpeg.exe放到同目录,或者设置为环境变量,没有ffmpeg将无法录制")
        sys.exit(0)

    # --------------------------初始化程序-------------------------------------
    print("-----------------------------------------------------")
    print("|               LiveRecordDownloader                |")
    print("-----------------------------------------------------")

    # --------------------------初始化变量-------------------------------------
    firstRunOtherLine = True
    first_start = True
    url_tuples_list = []
    create_var = locals()
    running_list = []
    name_list = []
    not_record_list = []
    monitoring = 0
    warning_count = 0

    # --------------------------log日志-------------------------------------
    logger = logging.getLogger('直播录制下载')
    logger.setLevel(logging.INFO)
    if not os.path.exists("./log"):
        os.makedirs("./log")
    fh = logging.FileHandler("./log/error.log", encoding="utf-8-sig", mode="a")
    fh.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if not os.path.exists('./config'):
        os.makedirs('./config')

    config_path = './config/config.json'

    while True:
        # 循环读取配置
        config = Config(config_path)

        # 读取直播间url信息
        try:
            rooms = config.live_rooms
            for item in rooms:
                url = item.url
                description = item.description

                if ('http://' not in url) and ('https://' not in url):
                    url = 'https://' + url

                url_host = url.split('/')[2]
                host_list = [
                    'live.douyin.com',
                    'v.douyin.com',
                    'live.kuaishou.com',
                    'www.huya.com',
                    'www.douyu.com',
                    'www.yy.com',
                    'live.bilibili.com'
                ]
                if url_host in host_list:
                    new_line = (url, description)
                    url_tuples_list.append(new_line)
                else:
                    print(f"{url} 未知链接.此条跳过")
            while len(name_list):
                a = name_list.pop()
                replace_words = a.split('|')
                if replace_words[0] != replace_words[1]:
                    config.update_live_room(url_to_find=replace_words[0],
                                            updates={'url': replace_words[1].split(',')[0],
                                                     'description': replace_words[1].split(',')[1]})

            if len(url_tuples_list) > 0:
                textNoRepeatUrl = list(set(url_tuples_list))
            if len(textNoRepeatUrl) > 0:
                for url_tuple in textNoRepeatUrl:
                    if url_tuple[0] in not_record_list:
                        continue

                    if url_tuple[0] not in running_list:
                        if first_start == False:
                            print("新增链接: " + url_tuple[0])
                        monitoring = monitoring + 1
                        args = [config, url_tuple, name_list, not_record_list, warning_count, logger, monitoring]
                        # TODO: 执行开始录制的操作
                        create_var['thread' + str(monitoring)] = threading.Thread(target=start_record, args=args)
                        create_var['thread' + str(monitoring)].daemon = True
                        create_var['thread' + str(monitoring)].start()
                        running_list.append(url_tuple[0])
            url_tuples_list = []
            first_start = False

        except Exception as e:
            print(f"错误信息:{e}\r\n发生错误的行数: {e.__traceback__.tb_lineno}")
            logger.warning(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")

        # 每次循环更新config
        config.save_config()
        time.sleep(3)


main()
