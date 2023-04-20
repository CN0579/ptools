# Create your views here.
import datetime
import json
import logging
import os
import socket
import subprocess
import time
from concurrent.futures.thread import ThreadPoolExecutor

import requests
import toml
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_job
from lxml import etree

from pt_site.UtilityTool import PtSpider, MessageTemplate, FileSizeConvert
from pt_site.models import MySite, TorrentInfo
from ptools.base import StatusCodeEnum, CommonResponse

job_defaults = {
    'coalesce': True,
    'misfire_grace_time': None
}
executors = {
    'default': ThreadPoolExecutor(2)
}
scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
scheduler.add_jobstore(DjangoJobStore(), 'default')

pool = ThreadPoolExecutor(2)
pt_spider = PtSpider()
logger = logging.getLogger('ptools')


# Create your views here.


def auto_sign_in():
    """自动签到"""
    start = time.time()
    # 获取工具支持且本人开启签到的所有站点
    queryset = MySite.objects.filter(site__sign_in_support=True).filter(sign_in=True).all()
    message_list = pt_spider.do_sign_in(pool, queryset)
    end = time.time()
    consuming = '> <font  color="blue">{} 任务运行成功！耗时：{}完成时间：{}  </font>\n'.format(
        '自动签到', end - start,
        time.strftime("%Y-%m-%d %H:%M:%S")
    )

    if message_list == 0:
        logger.info('已经全部签到咯！！')
    else:
        logger.info(message_list + consuming)
        message = message_list + consuming
        pt_spider.send_text(title='通知：自动签到', message=message)
    logger.info('{} 任务运行成功！完成时间：{}'.format('自动签到', time.strftime("%Y-%m-%d %H:%M:%S")))


def auto_get_status():
    """
    更新个人数据
    """
    start = time.time()
    message_list = '# 更新个人数据  \n\n'
    queryset = MySite.objects.filter(site__get_userinfo_support=True).filter(get_info=True).all()
    # site_list = [my_site for my_site in queryset if my_site.site.get_userinfo_support and my_site.get_info]
    results = pool.map(pt_spider.send_status_request, queryset)
    message_template = MessageTemplate.status_message_template
    for my_site, result in zip(queryset, results):
        if result.code == StatusCodeEnum.OK.code:
            res = pt_spider.parse_status_html(my_site, result.data)
            logger.info('自动更新个人数据: {}, {}'.format(my_site.site, res))
            if res.code == StatusCodeEnum.OK.code:
                status = res.data[0]
                message = message_template.format(
                    my_site.site.name,
                    my_site.my_level,
                    status.my_sp,
                    status.sp_hour,
                    status.my_bonus,
                    status.ratio,
                    FileSizeConvert.parse_2_file_size(status.seed_vol),
                    FileSizeConvert.parse_2_file_size(status.uploaded),
                    FileSizeConvert.parse_2_file_size(status.downloaded),
                    status.seed,
                    status.leech,
                    status.invitation,
                    my_site.my_hr
                )
                logger.info('组装Message：{}'.format(message))
                message_list += (
                        '> <font color="orange">' + my_site.site.name + '</font> 信息更新成功！' + message + '  \n\n')
                # pt_spider.send_text(my_site.site.name + ' 信息更新成功！' + message)
                logger.info(my_site.site.name + '信息更新成功！' + message)
            else:
                print(res)
                message = '> <font color="red">' + my_site.site.name + ' 信息更新失败！原因：' + res.msg + '</font>  \n\n'
                message_list = message + message_list
                # pt_spider.send_text(my_site.site.name + ' 信息更新失败！原因：' + str(res[0]))
                logger.warning(my_site.site.name + '信息更新失败！原因：' + res.msg)
        else:
            # pt_spider.send_text(my_site.site.name + ' 信息更新失败！原因：' + str(result[1]))
            message = '> <font color="red">' + my_site.site.name + ' 信息更新失败！原因：' + result.msg + '</font>  \n\n'
            message_list = message + message_list
            logger.warning(my_site.site.name + '信息更新失败！原因：' + result.msg)
    # 发送今日数据
    pt_spider.today_data()
    end = time.time()
    consuming = '> <font color="blue">{} 任务运行成功！耗时：{} 完成时间：{}  </font>  \n'.format(
        '自动更新个人数据', end - start,
        time.strftime("%Y-%m-%d %H:%M:%S")
    )
    logger.info(message_list + consuming)
    message = message_list + consuming
    pt_spider.send_text(title='通知：更新个人数据', message=message)


def auto_update_torrents():
    """
    拉取最新种子
    """
    start = time.time()
    message_list = '# 拉取免费种子  \n\n'
    queryset = MySite.objects.all()
    site_list = [my_site for my_site in queryset if my_site.site.get_torrent_support]
    results = pool.map(pt_spider.send_torrent_info_request, site_list)
    for my_site, result in zip(site_list, results):
        logger.info('获取种子：{}{}'.format(my_site.site.name, result))
        # print(result is tuple[int])
        if result.code == StatusCodeEnum.OK.code:
            res = pt_spider.get_torrent_info_list(my_site, result.data)
            # 通知推送
            if res.code == StatusCodeEnum.OK.code:
                message = '> <font color="orange">{}</font> 种子抓取成功！新增种子{}条，更新种子{}条!  \n\n'.format(
                    my_site.site.name,
                    res.data[0],
                    res.data[1])
                message_list += message
            else:
                message = '> <font color="red">' + my_site.site.name + '抓取种子信息失败！原因：' + res.msg + '</font>  \n'
                message_list = message + message_list
            # 日志
            logger.info(
                '{} 种子抓取成功！新增种子{}条，更新种子{}条! '.format(my_site.site.name, res.data[0], res.data[
                    1]) if res.code == StatusCodeEnum.OK.code else my_site.site.name + '抓取种子信息失败！原因：' + res.msg)
        else:
            # pt_spider.send_text(my_site.site.name + ' 抓取种子信息失败！原因：' + result[0])
            message = '> <font color="red">' + my_site.site.name + ' 抓取种子信息失败！原因：' + result.msg + '</font>  \n'
            message_list = message + message_list
            logger.info(my_site.site.name + '抓取种子信息失败！原因：' + result.msg)
    end = time.time()
    consuming = '> {} 任务运行成功！耗时：{} 当前时间：{}  \n'.format(
        '拉取最新种子',
        end - start,
        time.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info(message_list + consuming)
    message = message_list + consuming
    pt_spider.send_text(title='通知：拉取最新种子', message=message)


def auto_remove_expire_torrents():
    """
    删除过期种子
    """
    start = time.time()
    torrent_info_list = TorrentInfo.objects.all()
    count = 0
    for torrent_info in torrent_info_list:
        logger.info('种子名称：{}'.format(torrent_info.name))
        expire_time = torrent_info.sale_expire
        if '无限期' in expire_time:
            # ToDo 先更新种子信息，然后再判断
            continue
        if expire_time.endswith(':'):
            expire_time += '00'
            torrent_info.sale_expire = expire_time
            torrent_info.save()
        time_now = datetime.datetime.now()
        try:
            expire_time_parse = datetime.datetime.strptime(expire_time, '%Y-%m-%d %H:%M:%S')
            logger.info('优惠到期时间：{}'.format(expire_time))
        except Exception as e:
            logger.info('优惠到期时间解析错误：{}'.format(e))
            torrent_info.delete()
            count += 1
            continue
        if (expire_time_parse - time_now).days <= 0:
            logger.info('优惠已到期时间：{}'.format(expire_time))
            if torrent_info.downloader:
                # 未推送到下载器，跳过或删除？
                pass
            if pt_spider.get_torrent_info_from_downloader(torrent_info).code == StatusCodeEnum.OK.code:
                # todo 设定任务规则：
                #  免费到期后，下载完毕的种子是删除还是保留？
                #  未下载完成的，是暂停还是删除？
                pass
            count += 1
            torrent_info.delete()
    end = time.time()
    message = f'> 清除种子 任务运行成功！共清除过期种子{count}个，耗时：{end - start}  \n{time.strftime("%Y-%m-%d %H:%M:%S")}'
    pt_spider.send_text(title='通知：清除种子任务', message=message)


def auto_push_to_downloader():
    """推送到下载器"""
    start = time.time()
    print('推送到下载器')
    end = time.time()
    message = f'> 签到 任务运行成功！耗时：{end - start}  \n{time.strftime("%Y-%m-%d %H:%M:%S")}'
    pt_spider.send_text(title='通知：推送种子任务', message=message)


def auto_get_torrent_hash():
    """自动获取种子HASH"""
    start = time.time()
    print('自动获取种子HASH')
    time.sleep(5)
    end = time.time()
    message = f'> 获取种子HASH 任务运行成功！耗时：{end - start}  \n{time.strftime("%Y-%m-%d %H:%M:%S")}'
    pt_spider.send_text(title='通知：自动获取种子HASH', message=message)


def exec_command(commands):
    """执行命令行命令"""
    result = []
    for key, command in commands.items():
        p = subprocess.run(command, shell=True)
        logger.info('{} 命令执行结果：\n{}'.format(key, p))
        result.append({
            'command': key,
            'res': p.returncode
        })
    return result


@register_job(scheduler, 'cron', id='auto_get_upgrade', hour=2, minute=25, replace_existing=True)
def auto_get_upgrade():
    """程序更新"""
    try:
        logger.info('开始自动更新')
        update_commands = {
            # 'cp db/db.sqlite3 db/db.sqlite3-$(date "+%Y%m%d%H%M%S")',
            # '更新依赖环境': 'wget -O requirements.txt https://gitee.com/ngfchl/ptools/raw/master/requirements.txt && pip install -r requirements.txt -U',
            # '强制覆盖本地': 'git clean -df && git reset --hard',
            # '获取更新信息': 'git fetch --all',
            '拉取代码更新': f'git pull origin {os.getenv("DEV")}',
        }
        sync_commands = {
            '同步数据库': 'python manage.py migrate',
        }
        logger.info('拉取最新代码')
        result = exec_command(update_commands)
        logger.info('更新完毕')
        result.extend(exec_command(update_commands))
        message = f'> 更新完成！！{datetime.datetime.now()}'
        pt_spider.send_text(title='通知：程序更新', message=message)
        return CommonResponse.success(
            msg='更新成功！稍后请在接到通知后同步数据库！！',
            data={
                'result': result
            }
        )
    except Exception as e:
        # raise
        msg = '更新失败!{}，请尝试同步数据库！'.format(str(e))
        logger.error(msg)
        message = f'> <font color="red">{msg}</font>'
        pt_spider.send_text(title=msg, message=message)
        return CommonResponse.error(msg=msg)


@register_job(scheduler, 'cron', id='auto_do_xpath', hour=2, minute=30, replace_existing=True)
def auto_do_xpath():
    try:
        logger.info('开始自动更新')
        update_commands = {
            '同步数据库': 'python manage.py migrate',
        }
        logger.info('同步数据库')
        result = exec_command(update_commands)
        message = f'> 更新完成！！数据库同步完毕！{datetime.datetime.now()}'
        logger.info(message)
        pt_spider.send_text(title='通知：程序更新', message=message)
        return CommonResponse.success(
            msg=message,
            data={'result': result}
        )
    except Exception as e:
        # raise
        msg = '更新失败!{}，请尝试手动同步数据库！'.format(str(e))
        logger.error(msg)
        message = f'> <font color="red">{msg}</font>'
        pt_spider.send_text(title=msg, message=message)
        return CommonResponse.error(msg=msg)


def auto_update_license():
    """auto_update_license"""
    res = pt_spider.generate_config_file()
    if res.code != 0:
        return CommonResponse.error(
            msg=res.msg
        )
    with open('db/ptools.toml', 'r') as f:
        data = toml.load(f)
        print(data)
    pt_helper = data.get('pt_helper')
    if len(pt_helper) <= 0:
        return CommonResponse.error(
            msg='请先配置小助手相关信息再进行操作！'
        )
    host = pt_helper.get('host')
    username = pt_helper.get('username')
    password = pt_helper.get('password')
    url = 'http://get_pt_helper_license.guyubao.com/getTrial'
    license_xpath = '//h2/text()'
    session = requests.Session()
    res = session.get(url=url)
    token = ''.join(etree.HTML(res.content).xpath(license_xpath))
    login_url = host + '/login/submit'
    login_res = session.post(
        url=login_url,
        data={
            'username': username,
            'password': password,
        }
    )
    token_url = host + '/sys/config/update'
    logger.info(login_res.cookies.get_dict())
    cookies = session.cookies.get_dict()
    logger.info(cookies)
    res = session.post(
        url=token_url,
        cookies=cookies,
        data={
            'Id': 4,
            'ParamKey': 'license',
            'ParamValue': token.split('：')[-1],
            'Status': 1,
        }
    )
    logger.info(f'结果：{res.text}')
    result = res.json()
    if result.get('code') == 0:
        result['data'] = token
        pt_spider.send_text(title='小助手License更新成功！', message=f'> {token}')
        return CommonResponse.success(
            data=result
        )
    return CommonResponse.error(
        msg=f'License更新失败！'
    )


try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 44444))
    logger.info('启动Django主线程')
except socket.error:
    logger.info('启动后台任务')
    scheduler.start()
except Exception as e:
    logger.info('启动后台任务启动任务失败！{}'.format(e))
    # 有错误就停止定时器
    pt_spider.send_text(title='启动后台任务启动任务失败！', message='启动后台任务启动任务失败！')
    scheduler.shutdown()
