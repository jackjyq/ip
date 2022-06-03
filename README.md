# 考拉 IP 归属地

![](./static/favicon_io/android-chrome-192x192.png)

我的 IP 查询, 可查询我的 IP 地址及归属地, 及访问本站所使用的设备、操作系统及浏览器版本。

## 使用说明

### 查看本机 IP 归属地

https://ip.jackjyq.com/

```bash
# 获取 JSON 格式
curl 'https://ip.jackjyq.com/' -H 'Content-Type: application/json'
```

## IP 数据库

- 国内 IP: [ip2region](https://github.com/lionsoul2014/ip2region)
- 国外 IP: [MaxMind GeoLite2](https://www.maxmind.com/en/home)

## 本地部署

### 初始化

```bash
python3.10 -m virtualenv venv
pip install -r requirements.txt

# 下载 IP 数据库
chmod +x download_ip_data.sh
./download_ip_data.sh
```

### 运行

```bash
DEBUG=True python main.py runserver
# 或者
gunicorn main
```
