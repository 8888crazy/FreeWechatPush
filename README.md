# 免费微信推送
原理：申请免费的测试版公众号，可获得免费的模板推送功能。



### 申请公众号测试账户

使用微信扫码即可
https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login

进入页面以后我们来获取到这四个值 
#### appID  appSecret openId template_id
![image](https://github.com/tech-shrimp/FreeWechatPush/assets/154193368/bdb27abd-39cb-4e77-9b89-299afabc7330)

想让谁收消息，谁就用微信扫二维码，然后出现在用户列表，获取微信号（openId）
 ![image](https://github.com/tech-shrimp/FreeWechatPush/assets/154193368/1327c6f5-5c92-4310-a10b-6f2956c1dd75)

新增测试模板获得  template_id（模板ID）
 ![image](https://github.com/tech-shrimp/FreeWechatPush/assets/154193368/ec689f4d-6c0b-44c4-915a-6fd7ada17028)

模板标题随便填，模板内容如下，可以根据需求自己定制

模板一 天气预报：
```copy
今天：{{date.DATA}} 
地区：{{region.DATA}} 
天气：{{weather.DATA}} 
气温：{{temp.DATA}} 
风向：{{wind_dir.DATA}} 
对你说的话：{{today_note.DATA}}
```



### 配置代码

将上面获得的几个值填入代码这几行
在 setting中设置几个环境变量
<img width="1071" height="345" alt="image" src="https://github.com/user-attachments/assets/55642906-3181-49fc-8b8e-f26f80475c16" />





地区在Actions 中设置



特别感谢  **技术爬爬虾**  提供的基础代码及思路，本项目基于作者改编而来！
