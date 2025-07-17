import time
import requests
import json
import schedule
import os
import random
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 从环境变量获取
appID = os.getenv("APP_ID")
appSecret = os.getenv("APP_SECRET")
city = os.getenv("CITY")  # 添加城市环境变量

# 从环境变量获取逗号分隔的OpenID列表
openIds_str = os.getenv("OPEN_IDS")
openIds = [oid.strip() for oid in openIds_str.split(",")] if openIds_str else []

# 天气预报模板ID
weather_template_id = "OqxHyfroYI9lryCQwR-MHukMcy9r7qhKScmw2NPfzyI"
# 时间表模板ID - 确保这是有效的模板ID
timetable_template_id = "YOUR_TIMETABLE_TEMPLATE_ID"

# 频率控制
MAX_USERS_PER_MINUTE = 20  # 微信API限制

# 创建具有重试机制的会话
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # 最大重试次数
        backoff_factor=1,  # 指数退避因子
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
        allowed_methods=["GET", "POST"]  # 允许重试的HTTP方法
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 设置用户代理头
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    ]
    
    session.headers.update({
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    
    return session

def get_weather(my_city):
    try:
        urls = [
            "http://www.weather.com.cn/textFC/hb.shtml",
            "http://www.weather.com.cn/textFC/db.shtml",
            "http://www.weather.com.cn/textFC/hd.shtml",
            "http://www.weather.com.cn/textFC/hz.shtml",
            "http://www.weather.com.cn/textFC/hn.shtml",
            "http://www.weather.com.cn/textFC/xb.shtml",
            "http://www.weather.com.cn/textFC/xn.shtml"
        ]
        
        session = create_session()
        
        for url in urls:
            try:
                print(f"尝试从 {url} 获取天气...")
                resp = session.get(url, timeout=15)
                resp.raise_for_status()  # 检查HTTP错误
                
                # 检查响应内容类型
                content_type = resp.headers.get('Content-Type', '').lower()
                if 'charset=' not in content_type:
                    resp.encoding = 'utf-8'  # 默认使用utf-8编码
                    
                text = resp.text
                soup = BeautifulSoup(text, 'html.parser')  # 使用更快的解析器
                
                # 添加调试输出
                # print(f"响应内容: {text[:500]}...")  # 打印前500个字符
                
                div_conMidtab = soup.find("div", class_="conMidtab")
                
                if not div_conMidtab:
                    print(f"在 {url} 中未找到 conMidtab 元素")
                    continue
                    
                tables = div_conMidtab.find_all("table")
                if not tables:
                    print(f"在 {url} 中未找到表格")
                    continue
                    
                for table in tables:
                    trs = table.find_all("tr")[2:]
                    for index, tr in enumerate(trs):
                        tds = tr.find_all("td")
                        if len(tds) < 8:  # 确保有足够的列
                            continue
                            
                        city_td = tds[-8]
                        this_city = list(city_td.stripped_strings)[0] if city_td.stripped_strings else ""
                        
                        if this_city == my_city:
                            # 解析天气数据
                            high_temp_td = tds[-5]
                            low_temp_td = tds[-2]
                            weather_type_day_td = tds[-7]
                            weather_type_night_td = tds[-4]
                            wind_td_day = tds[-6]
                            wind_td_day_night = tds[-3]

                            high_temp = list(high_temp_td.stripped_strings)[0] if high_temp_td.stripped_strings else "-"
                            low_temp = list(low_temp_td.stripped_strings)[0] if low_temp_td.stripped_strings else "-"
                            weather_typ_day = list(weather_type_day_td.stripped_strings)[0] if weather_type_day_td.stripped_strings else "-"
                            weather_type_night = list(weather_type_night_td.stripped_strings)[0] if weather_type_night_td.stripped_strings else "-"

                            wind_day = "".join(list(wind_td_day.stripped_strings)[:2]) if wind_td_day.stripped_strings else "--"
                            wind_night = "".join(list(wind_td_day_night.stripped_strings)[:2]) if wind_td_day_night.stripped_strings else "--"

                            # 如果没有白天的数据就使用夜间的
                            # temp = f"{low_temp}——{high_temp}℃" if high_temp != "-" else f"{low_temp}℃"
                            if high_temp != "-":
                                temp = f"{low_temp}——{high_temp}摄氏度"
                            else:
                                temp = f"{low_temp}摄氏度"
                            weather_typ = weather_typ_day if weather_typ_day != "-" else weather_type_night
                            wind = wind_day if wind_day != "--" else wind_night
                            
                            return this_city, temp, weather_typ, wind
                
                # 请求之间添加随机延迟，避免被识别为爬虫
                time.sleep(random.uniform(1, 3))
                        
            except Exception as e:
                print(f"处理 {url} 时出错: {e}")
                continue
        
        print(f"未找到城市 {my_city} 的天气信息")
        return None
        
    except Exception as e:
        print(f"获取天气失败: {e}")
        return None


def get_access_token():
    try:
        url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appID.strip()}&secret={appSecret.strip()}'
        session = create_session()
        response = session.get(url, timeout=15)
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
        session = create_session()
        r = session.get(url, timeout=15)
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
    
    if not openIds:
        print("没有设置接收用户，取消发送")
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
            session = create_session()
            response = session.post(
                url, 
                json.dumps(body, ensure_ascii=False).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                timeout=15
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
    
    if not openIds:
        print("没有设置接收用户，取消发送")
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
            session = create_session()
            response = session.post(
                url, 
                json.dumps(body, ensure_ascii=False).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                timeout=15
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
    if not city:
        print("未设置城市，取消天气报告")
        return
    
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