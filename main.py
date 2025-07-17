import time
import requests
import json
import schedule
import os
from bs4 import BeautifulSoup

# 从环境变量获取
appID = os.getenv("APP_ID")
appSecret = os.getenv("APP_SECRET")
city = os.getenv("CITY")  # 添加城市环境变量

# 从环境变量获取逗号分隔的OpenID列表
openIds_str = os.getenv("OPEN_IDS")
openIds = [oid.strip() for oid in openIds_str.split(",")]

# 天气预报模板ID
weather_template_id = "OqxHyfroYI9lryCQwR-MHukMcy9r7qhKScmw2NPfzyI"
# 时间表模板ID - 确保这是有效的模板ID
timetable_template_id = "YOUR_TIMETABLE_TEMPLATE_ID"

# 频率控制
MAX_USERS_PER_MINUTE = 20  # 微信API限制

def get_weather(my_city):
    try:
        urls = ["http://www.weather.com.cn/textFC/hb.shtml",
                "http://www.weather.com.cn/textFC/db.shtml",
                "http://www.weather.com.cn/textFC/hd.shtml",
                "http://www.weather.com.cn/textFC/hz.shtml",
                "http://www.weather.com.cn/textFC/hn.shtml",
                "http://www.weather.com.cn/textFC/xb.shtml",
                "http://www.weather.com.cn/textFC/xn.shtml"
                ]
        
        for url in urls:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()  # 检查HTTP错误
            text = resp.content.decode("utf-8")
            soup = BeautifulSoup(text, 'html5lib')
            div_conMidtab = soup.find("div", class_="conMidtab")
            
            if not div_conMidtab:
                continue
                
            tables = div_conMidtab.find_all("table")
            for table in tables:
                trs = table.find_all("tr")[2:]
                for index, tr in enumerate(trs):
                    tds = tr.find_all("td")
                    if len(tds) < 8:  # 确保有足够的列
                        continue
                        
                    city_td = tds[-8]
                    this_city = list(city_td.stripped_strings)[0]
                    
                    if this_city == my_city:
                        # ... 现有解析逻辑 ...
                        return this_city, temp, weather_typ, wind
                        
        print(f"未找到城市 {my_city} 的天气信息")
        return None
        
    except Exception as e:
        print(f"获取天气失败: {e}")
        return None


def get_access_token():
    try:
        url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appID.strip()}&secret={appSecret.strip()}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'access_token' in data:
            return data['access_token']
        else:
            print(f"获取access_token失败: {data}")
            return None
            
    except Exception as e:
        print(f"获取access_token出错: {e}")
        return None


def get_daily_love():
    try:
        url = "https://api.lovelive.tools/api/SweetNothings/Serialization/Json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get('returnObj', [""])[0]
    except Exception as e:
        print(f"获取每日情话失败: {e}")
        return "今天没有情话哦~"


def send_weather(access_token, weather):
    if not weather:
        print("天气信息无效，取消发送")
        return
        
    for i, openId in enumerate(openIds):
        try:
            import datetime
            today = datetime.date.today()
            today_str = today.strftime("%Y年%m月%d日")

            body = {
                "touser": openId.strip(),
                "template_id": weather_template_id.strip(),
                "url": "https://weixin.qq.com",
                "data": {
                    "date": {"value": today_str},
                    "region": {"value": weather[0]},
                    "weather": {"value": weather[2]},
                    "temp": {"value": weather[1]},
                    "wind_dir": {"value": weather[3]},
                    "today_note": {"value": get_daily_love()}
                }
            }
            
            url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
            response = requests.post(
                url, 
                json.dumps(body, ensure_ascii=False).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                timeout=10
            ).json()
            
            print(f"发送给 {openId} 的结果: {response}")
            
            # 频率控制
            if (i + 1) % MAX_USERS_PER_MINUTE == 0 and (i + 1) < len(openIds):
                print(f"已发送{MAX_USERS_PER_MINUTE}个用户，等待60秒避免频率限制")
                time.sleep(60)
            else:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"发送给 {openId} 失败: {e}")


def send_timetable(access_token, message):
    if not timetable_template_id or timetable_template_id.strip() == "":
        print("时间表模板ID未设置，取消发送")
        return
        
    for i, openId in enumerate(openIds):
        try:
            body = {
                "touser": openId.strip(),
                "template_id": timetable_template_id.strip(),
                "url": "https://weixin.qq.com",
                "data": {"message": {"value": message}}
            }
            
            url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
            response = requests.post(
                url, 
                json.dumps(body, ensure_ascii=False).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                timeout=10
            ).json()
            
            print(f"发送时间表给 {openId} 的结果: {response}")
            
            # 频率控制
            if (i + 1) % MAX_USERS_PER_MINUTE == 0 and (i + 1) < len(openIds):
                print(f"已发送{MAX_USERS_PER_MINUTE}个用户，等待60秒避免频率限制")
                time.sleep(60)
            else:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"发送时间表给 {openId} 失败: {e}")


def weather_report(city):
    access_token = get_access_token()
    if not access_token:
        print("获取access_token失败，无法发送天气报告")
        return
        
    weather = get_weather(city)
    if weather:
        print(f"天气信息： {weather}")
        send_weather(access_token, weather)
    else:
        print("无法获取天气信息，取消发送")


def timetable(message):
    access_token = get_access_token()
    if not access_token:
        print("获取access_token失败，无法发送时间表")
        return
        
    send_timetable(access_token, message)


if __name__ == '__main__':
    # 发送天气报告
    weather_report(city)
    
    # 发送时间表
    # timetable("第二教学楼十分钟后开始英语课")
    
    # 定时任务（本地运行时使用）
    # schedule.every().day.at("18:30").do(weather_report, city)
    # schedule.every().monday.at("13:50").do(timetable, "第二教学楼十分钟后开始英语课")
    
    # while True:
    #    schedule.run_pending()
    #    time.sleep(1)