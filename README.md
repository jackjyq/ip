# 考拉 IP 归属地

![](./static/favicon_io/android-chrome-192x192.png)

查询我的 IP 地址、归属地、设备类型、操作系统、浏览器版本、屏幕分辨率、经纬度及地理位置。

## API

### 网页格式

https://ip.jackjyq.com/

### 文本格式

`curl 'https://ip.jackjyq.com/'`

### JSON 格式

`curl 'https://ip.jackjyq.com/' -H 'Content-Type: application/json'`

## 部署运行

### 部署

```bash
# 配置虚拟环境
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

## 数据源

### IP 归属地

- 国内 IP: [ip2region](https://github.com/lionsoul2014/ip2region)
- 国外 IP: [MaxMind GeoLite2](https://www.maxmind.com/en/home)

### 经纬度位置

- [Nominatim](https://nominatim.org/)
