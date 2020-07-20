import requests
import json
import random
import time
from datetime import datetime

from contents import *


def info(message):
    for url in WEBHOOKS:
        data = {
            'message_type': 'group',
            'group_id': 617888503,
            'message': message,
            'auto_escape': True
        }
        r = requests.post(url, data=data)
        if r.ok:
            print('message send success'.format(message))
        else:
            print('message send fail, code: {}, content: {}'.format(r.status_code, r.content.decode('utf-8')))


def send_message(url, text, single_md=False):
    header = {"Content-type": "application/json"}
    if single_md:
        data = {
            "blocks": [
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }
                },
                {
                    "type": "divider"
                }
            ]
        }
    else:
        data = {"text": text}
    response = requests.post(url, headers=header, data=json.dumps(data))
    if response.status_code != 200:
        print('Request to slack returned an error %s, the response is:\n%s' % (response.status_code, response.text))


def open_dota_matches_refresh(uid):
    header = {
        "authority": "api.opendota.com",
        "method": "POST",
        "path": "/api/players/{}/refresh".format(uid),
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,en-CA;q=0.7",
        "content-length": "0",
        "origin": "https://www.opendota.com",
        "referer": "https://www.opendota.com/players/{}/matches".format(uid),
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
    url = "https://api.opendota.com/api/players/{}/refresh".format(uid)
    r = requests.post(url, headers=header)


def get_matches(mid):
    """
        Get a specific match with mid
    """
    url = "https://api.opendota.com/api/matchES/{}".format(mid)
    r = requests.get(url)
    if r.ok:
        result = json.loads(r.content.decode('utf-8'))
        return result
    else:
        print('get mid: {} matches fail, status code: {}'.format(uid, r.status_code))


def get_recent_matches(uid):
    """
    get player recenet match in opendota
    """
    # url = "https://api.opendota.com/api/players/{}/matches?limit={}".format(uid)
    url = "https://api.opendota.com/api/players/{}/recentMatches".format(uid)
    r = requests.get(url)
    if r.ok:
        result = json.loads(r.content.decode('utf-8'))
        return result
    else:
        print('get uid: {} matches fail, status code: {}'.format(uid, r.status_code))


def filter_recent_matches(result):
    return_list = []
    for match in result:
        # only need AP, RD, RANKED AP MODE, and Public match, Ranked, team, solo match lobby
        if match['game_mode'] in (1, 3, 22, 4) and match['lobby_type'] in (0, 5, 6, 7):
            return_list.append(match)
    return return_list


def calculate_kda(k, d, a):
    if d == 0:
        d = 1
    return round((k + a) / d, 2)


def analyse_match_win_or_lose(match):
    if match['player_slot'] >= 128:
        is_radint = False
    else:
        is_radint = True
    if is_radint:
        if match['radiant_win']:
            win = True
        else:
            win = False
    else:
        if match['radiant_win']:
            win = False
        else:
            win = True
    return win


def kda_emoji(kda):
    if kda > 10:
        emoji = ':thumbsup:'
    elif kda < 2:
        emoji = ":scream:"
    else:
        emoji = ""
    return emoji


def analyse_one_match(match, name=None, postive=False):
    # 活动模式不解析
    if match['game_mode'] in (15, 19):
        print('Match ID:{} 为活动模式, 跳过'.format(match['match_id']))
        return
    # roll车不解析
    if match['duration'] <= 600:
        print('Match ID:{} 低于10分钟猜测roll车或者掉线, 跳过'.format(match['match_id']))
        return
    # 比赛是否胜利
    win = analyse_match_win_or_lose(match)
    kda = calculate_kda(match['kills'], match['deaths'], match['assists'])
    emoji = kda_emoji(kda)
    # 是否夸夸
    # 获胜 KDA大于10 或 失败 KDA大于6 夸
    if (win and kda > 10) or (not win and kda > 6):
        postive = True
    # 获胜 KDA小于4 或者失败KDA小于1 喷
    elif (win and kda < 4) or (not win and kda < 1):
        postive = False
    # 其余随机
    else:
        if random.randint(0, 1) == 0:
            postive = True
        else:
            postive = False
    print_str = ''
    # 生成标题语句
    if win and postive:
        print_str += random.choice(WIN_POSTIVE).format(name) + '📈 +25\n'
    elif win and not postive:
        print_str += random.choice(WIN_NEGATIVE).format(name) + '📈 +25\n'
    elif not win and postive:
        print_str += random.choice(LOSE_POSTIVE).format(name) + '📉 -25\n'
    else:
        print_str += random.choice(LOSE_NEGATIVE).format(name) + '📉 -25\n'

    # 生成比赛详情
    # 计算时间
    print_str += "比赛开始时间: {}\n".format(datetime.fromtimestamp(match['start_time']).strftime('%Y-%m-%d %H:%M:%S'))
    print_str += "比赛持续时间: {}分 {}秒\n".format(match['duration'] // 60, match['duration'] % 60)
    print_str += "使用英雄: {}\n".format(HEROES_LIST_CHINESE[match['hero_id']] if match['hero_id'] in HEROES_LIST_CHINESE else '不知道什么鬼')
    print_str += "战绩: [{}/{}/{}] \n".format(match['kills'], match['deaths'], match['assists'])
    print_str += "KDA: {} {}\n".format(kda, emoji)
    print_str += "每分钟金钱数: {}\n".format(match['gold_per_min'])
    print_str += "每分钟经验数: {}\n".format(match['xp_per_min'])
    print_str += "补刀数: {}\n".format(match['last_hits'])
    print_str += "游戏模式: [{}/{}]\n".format(
        GAME_MODE[match['game_mode']] if match['game_mode'] in GAME_MODE else '未知',
        LOBBY[match['lobby_type']] if match['lobby_type'] in LOBBY else '未知')
    print_str += "游戏服务器: [{}]\n".format(AREA_CODE[match['cluster']] if match['cluster'] in AREA_CODE else '未知')
    print_str += "战绩详情: https://www.dotabuff.com/matches/{}".format(match['match_id'])

    # 发送
    print(print_str)
    info(print_str)


def analyse_player_recent_matches(uid, name):
    open_dota_matches_refresh(uid)
    print("refresh {}'s({}) recent matches, wait 10s.".format(name, uid))
    time.sleep(10)
    result = get_recent_matches(uid)
    result = filter_recent_matches(result)
    for match in result:
        analyse_one_match(match, name=name)