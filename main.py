# 安装依赖 pip3 install requests html5lib bs4 schedule

import time
import requests
import json
import schedule
import os
from bs4 import BeautifulSoup


# 从测试号信息获取
# 从环境变量获取
appID = os.getenv("APP_ID", "wx1b3c649164eebf82")
appSecret = os.getenv("APP_SECRET", "d9e140e1a67b3e147462cf29438af1b4")

# 从环境变量获取逗号分隔的OpenID列表
openIds_str = os.getenv("OPEN_IDS", "ofOugvo0l0L1wUwdNpKwNmxrB5NQ,ofOugvptBC1pSiOLgp8f5GjpfQJs")
openIds = [oid.strip() for oid in openIds_str.split(",")]

# appID = "wx1b3c649164eebf82"
# appSecret = "d9e140e1a67b3e147462cf29438af1b4"
#收信人ID即 用户列表中的微信号，见上文
# openId = "ofOugvo0l0L1wUwdNpKwNmxrB5NQ"
# 收信人ID列表（多个用户）
# openIds = [
#    "ofOugvo0l0L1wUwdNpKwNmxrB5NQ",  # 用户1
#    "ofOugvptBC1pSiOLgp8f5GjpfQJs",                # 用户2
#    "USER_OPEN_ID_3",                # 用户3
    # 添加更多用户...
#]

# 天气预报模板ID
weather_template_id = "OqxHyfroYI9lryCQwR-MHukMcy9r7qhKScmw2NPfzyI"
# 时间表模板ID
timetable_template_id = ""


def get_weather(my_city):
    urls = ["http://www.weather.com.cn/textFC/hb.shtml",
            "http://www.weather.com.cn/textFC/db.shtml",
            "http://www.weather.com.cn/textFC/hd.shtml",
            "http://www.weather.com.cn/textFC/hz.shtml",
            "http://www.weather.com.cn/textFC/hn.shtml",
            "http://www.weather.com.cn/textFC/xb.shtml",
            "http://www.weather.com.cn/textFC/xn.shtml"
            ]
    for url in urls:
        resp = requests.get(url)
        text = resp.content.decode("utf-8")
        soup = BeautifulSoup(text, 'html5lib')
        div_conMidtab = soup.find("div", class_="conMidtab")
        tables = div_conMidtab.find_all("table")
        for table in tables:
            trs = table.find_all("tr")[2:]
            for index, tr in enumerate(trs):
                tds = tr.find_all("td")
                # 这里倒着数，因为每个省会的td结构跟其他不一样
                city_td = tds[-8]
                this_city = list(city_td.stripped_strings)[0]
                if this_city == my_city:

                    high_temp_td = tds[-5]
                    low_temp_td = tds[-2]
                    weather_type_day_td = tds[-7]
                    weather_type_night_td = tds[-4]
                    wind_td_day = tds[-6]
                    wind_td_day_night = tds[-3]

                    high_temp = list(high_temp_td.stripped_strings)[0]
                    low_temp = list(low_temp_td.stripped_strings)[0]
                    weather_typ_day = list(weather_type_day_td.stripped_strings)[0]
                    weather_type_night = list(weather_type_night_td.stripped_strings)[0]

                    wind_day = list(wind_td_day.stripped_strings)[0] + list(wind_td_day.stripped_strings)[1]
                    wind_night = list(wind_td_day_night.stripped_strings)[0] + list(wind_td_day_night.stripped_strings)[1]

                    # 如果没有白天的数据就使用夜间的
                    temp = f"{low_temp}——{high_temp}摄氏度" if high_temp != "-" else f"{low_temp}摄氏度"
                    weather_typ = weather_typ_day if weather_typ_day != "-" else weather_type_night
                    wind = f"{wind_day}" if wind_day != "--" else f"{wind_night}"
                    return this_city, temp, weather_typ, wind


def get_access_token():
    # 获取access token的url
    # url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}' \
    #     .format(appID.strip(), appSecret.strip())
    # 获取access token的url
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appID.strip()}&secret={appSecret.strip()}'

    response = requests.get(url).json()
    print(response)
    access_token = response.get('access_token')
    return access_token


def get_daily_love():
    # 每日一句情话
    url = "https://api.lovelive.tools/api/SweetNothings/Serialization/Json"
    r = requests.get(url)
    all_dict = json.loads(r.text)
    sentence = all_dict['returnObj'][0]
    daily_love = sentence
    return daily_love


def send_weather(access_token, weather):
    # touser 就是 openID
    # template_id 就是模板ID
    # url 就是点击模板跳转的url
    # data就按这种格式写，time和text就是之前{{time.DATA}}中的那个time，value就是你要替换DATA的值
    # 循环发送给所有用户
    for openId in openIds:

        import datetime
        today = datetime.date.today()
        today_str = today.strftime("%Y年%m月%d日")

        body = {
            "touser": openId.strip(),
            "template_id": weather_template_id.strip(),
            "url": "https://weixin.qq.com",
            "data": {
                "date": {
                    "value": today_str
                },
                "region": {
                    "value": weather[0]
                },
                "weather": {
                    "value": weather[2]
                },
                "temp": {
                    "value": weather[1]
                },
                "wind_dir": {
                    "value": weather[3]
                },
                "today_note": {
                    "value": get_daily_love()
                }
            }
        }
        # url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}'.format(access_token)
        # print(requests.post(url, json.dumps(body)).text)
        url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
        response = requests.post(url, json.dumps(body)).json()
        print(f"发送给 {openId} 的结果: {response}")
        
        # 添加延迟避免频率限制
        time.sleep(0.5)    

def send_timetable(access_token, message):
    # 循环发送给所有用户
    for openId in openIds:
    
        body = {
            # "touser": openId,
            "touser": openId.strip(),
            # "template_id": timetable_template_id.strip(),
            "url": "https://weixin.qq.com",
            "data": {
                "message": {
                    "value": message
                },
            }
        }
        # url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}'.format(access_token)
        # print(requests.post(url, json.dumps(body)).text)
        url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
        response = requests.post(url, json.dumps(body)).json()
        print(f"发送给 {openId} 的结果: {response}")
        
        # 添加延迟避免频率限制
        time.sleep(0.5)

def weather_report(city):
    # 1.获取access_token
    access_token = get_access_token()
    # 2. 获取天气
    weather = get_weather(city)
    print(f"天气信息： {weather}")
    # 3. 发送消息给所有用户
    send_weather(access_token, weather)


def timetable(message):
    # 1.获取access_token
    access_token = get_access_token()
    # 3. 发送消息给所有用户
    send_timetable(access_token, message)


if __name__ == '__main__':
    # 发送给所有用户
    weather_report("沈阳")
    # timetable("第二教学楼十分钟后开始英语课")
    
    # 定时任务示例（需要时取消注释）
    # schedule.every().day.at("18:30").do(weather_report, "南京")
    # schedule.every().monday.at("13:50").do(timetable, "第二教学楼十分钟后开始英语课")
    #while True:
    #    schedule.run_pending()
    #    time.sleep(1)
