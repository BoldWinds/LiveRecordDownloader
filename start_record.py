import random
import os
import subprocess
import threading
import datetime

from spider import *
from web_rid import *
from config import *
from get_url import *


def start_record(config, url_tuple, name_list, not_record_list, warning_count, logger, count_variable=-1):
    live_list = []
    recording = set()
    unrecording = set()
    recording_time_list = {}
    video_save_path = config.video_save_path
    semaphore = threading.Semaphore(4)
    rstr = r"[\/\\\:\*\?\"\<\>\|&u]"
    default_path = os.getcwd()

    print("start_record!")
    while True:
        try:
            record_finished = False
            record_finished_2 = False
            runonce = False
            is_long_url = False
            count_time = time.time()
            record_url = url_tuple[0]
            anchor_name = url_tuple[1]
            print("\r运行新线程,传入地址 " + record_url)

            while True:
                try:
                    port_info = []
                    if record_url.find("https://live.douyin.com/") > -1:
                        # 判断如果是浏览器长链接
                        with semaphore:
                            # 使用semaphore来控制同时访问资源的线程数量
                            json_data = get_douyin_stream_data(record_url, config.dy_cookie)  # 注意这里需要配置文件中的cookie
                            port_info = get_douyin_stream_url(json_data, config.video_quality)
                    elif record_url.find("https://v.douyin.com/") > -1:
                        # 判断如果是app分享链接
                        is_long_url = True
                        room_id, sec_user_id = get_sec_user_id(record_url)
                        web_rid = get_live_room_id(room_id, sec_user_id)
                        if len(web_rid) == 0:
                            print('web_rid 获取失败，若多次失败请联系作者修复或者使用浏览器打开后的长链接')
                        new_record_url = "https://live.douyin.com/" + str(web_rid)
                        not_record_list.append(new_record_url)
                        with semaphore:
                            json_data = get_douyin_stream_data(new_record_url, config.dy_cookie)
                            port_info = get_douyin_stream_url(json_data, config.video_quality)

                    anchor_name = port_info.get("anchor_name", '')

                    if not anchor_name:
                        print(f'序号{count_variable} 网址内容获取失败,进行重试中...获取失败的地址是:{url_tuple}')
                        warning_count += 1
                    else:
                        anchor_name = re.sub(rstr, "_", anchor_name)  # 过滤不能作为文件名的字符，替换为下划线
                        record_name = f'序号{count_variable} {anchor_name}'

                        if anchor_name in recording:
                            print(f"新增的地址: {anchor_name} 已经存在,本条线程将会退出")
                            name_list.append(f'{record_url}|#{record_url}')
                            return

                        if url_tuple[1] == "" and runonce is False:
                            if is_long_url:
                                name_list.append(f'{record_url}|{new_record_url},主播: {anchor_name.strip()}')
                            else:
                                name_list.append(f'{record_url}|{record_url},主播: {anchor_name.strip()}')
                            runonce = True

                        if port_info['is_live'] is False:
                            print(f"{record_name} 等待直播... ")
                            config.update_live_room(record_url, {'description': anchor_name, 'isLiving': "等待开播",
                                                                 'isRecording': False})
                        else:
                            content = f"{record_name} 正在直播中..."
                            config.update_live_room(record_url, {'description': anchor_name, 'isLiving': "正在直播",
                                                                 'isRecording': True})
                            print(content)

                            real_url = port_info['record_url']
                            print("real url is: " + real_url)
                            full_path = f'{default_path}/{anchor_name}'
                            if real_url != "":
                                live_list.append(anchor_name)
                                now = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
                                try:
                                    if len(video_save_path) > 0:
                                        if video_save_path[-1] != "/":
                                            video_save_path = video_save_path + "/"
                                        full_path = f'{video_save_path}/{anchor_name}'
                                        if not os.path.exists(full_path):
                                            os.makedirs(full_path)
                                    else:
                                        if not os.path.exists(anchor_name):
                                            os.makedirs('./' + anchor_name)

                                except Exception as e:
                                    print(f"路径错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
                                    logger.warning(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")

                                if not os.path.exists(full_path):
                                    print(
                                        "保存路径不存在,不能生成录制.请避免把本程序放在c盘,桌面,下载文件夹,qq默认传输目录.请重新检查设置")
                                    logger.warning(
                                        "错误信息: 保存路径不存在,不能生成录制.请避免把本程序放在c盘,桌面,下载文件夹,qq默认传输目录.请重新检查设置")

                                ffmpeg_command = [
                                    "ffmpeg", "-y",
                                    "-v", "verbose",
                                    "-rw_timeout", "10000000",  # 10s
                                    "-loglevel", "error",
                                    "-hide_banner",
                                    "-user_agent",
                                    "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36",
                                    "-protocol_whitelist", "rtmp,crypto,file,http,https,tcp,tls,udp,rtp",
                                    "-thread_queue_size", "1024",
                                    "-analyzeduration", "2147483647",
                                    "-probesize", "2147483647",
                                    "-fflags", "+discardcorrupt",
                                    "-i", real_url,
                                    "-bufsize", "5000k",
                                    "-sn", "-dn",
                                    "-reconnect_delay_max", "30",
                                    "-reconnect_streamed", "-reconnect_at_eof",
                                    "-c:a", "copy",
                                    "-max_muxing_queue_size", "64",
                                    "-correct_ts_overflow", "1",
                                ]

                                recording.add(record_name)
                                start_record_time = datetime.datetime.now()
                                recording_time_list[record_name] = start_record_time
                                rec_info = f"\r{anchor_name} 录制视频中: {full_path}"
                                filename_short = full_path + '/' + anchor_name + '_' + now

                                # mp4处理
                                filename = anchor_name + '_' + now + ".mp4"
                                config.update_live_room(record_url, {'description': anchor_name, 'startTime': now})
                                print(f'{rec_info}/{filename}')
                                file = full_path + '/' + filename

                                try:
                                    command = [
                                        "-map", "0",
                                        "-c:v", "copy",  # 直接用copy的话体积特别大.
                                        "-f", "mp4",
                                        "{path}".format(path=file),
                                    ]
                                    ffmpeg_command.extend(command)
                                    _output = subprocess.check_output(ffmpeg_command, stderr=subprocess.STDOUT)

                                    # 取消http_proxy环境变量设置
                                    # if proxy_addr:
                                    #     del os.environ["http_proxy"]

                                    record_finished = True
                                    record_finished_2 = True
                                    count_time = time.time()

                                except subprocess.CalledProcessError as e:
                                    # logging.warning(str(e.output))
                                    print(f"{e.output} 发生错误的行数: {e.__traceback__.tb_lineno}")
                                    logger.warning(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")

                            if record_finished_2 == True:
                                if record_name in recording:
                                    recording.remove(record_name)
                                if anchor_name in unrecording:
                                    unrecording.add(anchor_name)
                                print(f"\n{anchor_name} {time.strftime('%Y-%m-%d %H:%M:%S')} 直播录制完成\n")
                                record_finished_2 = False

                except Exception as e:
                    print(f"错误信息:{e}\r\n读取的地址为: {record_url} 发生错误的行数: {e.__traceback__.tb_lineno}")
                    logger.warning("错误信息: " + str(e) + " 发生错误的行数: " + str(e.__traceback__.tb_lineno))
                    warning_count += 1

                num = random.randint(-5, 5)   # 生成-5到5的随机数，加上delay_default
                if num < 0:  # 如果得到的结果小于0，则将其设置为0
                    num = 0
                x = num

                # 如果出错太多,就加秒数
                if warning_count > 100:
                    x = x + 60
                    print("瞬时错误太多,延迟加60秒")

                # 这里是.如果录制结束后,循环时间会暂时变成30s后检测一遍. 这样一定程度上防止主播卡顿造成少录
                # 当30秒过后检测一遍后. 会回归正常设置的循环秒数
                if record_finished == True:
                    count_time_end = time.time() - count_time
                    if count_time_end < 60:
                        x = 30
                    record_finished = False

                else:
                    x = num

                # 这里是正常循环
                while x:
                    x = x - 1
                    time.sleep(1)
        except Exception as e:
            print(f"错误信息:{e}\r\n发生错误的行数: {e.__traceback__.tb_lineno}")
            logger.warning(f"错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            print(f"线程崩溃2秒后重试.错误信息: {e} 发生错误的行数: {e.__traceback__.tb_lineno}")
            warning_count += 1
            time.sleep(2)
