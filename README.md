# [考拉 IP 归属地](https://ip.jackjyq.com/)

![](./src/static/favicon_io/android-chrome-192x192.png)

查询我的 IP 地址、归属地、设备类型、操作系统、浏览器版本、屏幕分辨率、经纬度、地理位置等。

## 快速开始

![](https://img.shields.io/badge/Ubuntu-22%20LTS-orange)
![](https://img.shields.io/badge/macOS-Sonoma-white)

注：因用到 [sh](https://pypi.org/project/sh/) 而不兼容 Windows。此外，由于大陆网路原因，`查看 Whois 信息` 功能或不可用。

### 安装

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# 安装 Python 依赖
uv sync

# 下载 ip2region 数据库
uv run ./src/update_ip2region.py

# 下载 GeoLite2 数据库
bash -c ./src/update_geolite2.sh

# 安装 whois
sudo apt install whois
```

### 运行

```bash
# 调试模式
DEBUG="True" uv run ./src/main.py runserver

# 生产模式
uv run gunicorn --workers 3 --worker-class=gevent src.main
```

## API 文档

### 我的 IP(文本格式)

- `curl 'https://ip.jackjyq.com/text'`
- `curl 'https://ip.jackjyq.com/'`

### 我的 IP(JSON 格式)

- `curl 'https://ip.jackjyq.com/json'`
- `curl 'https://ip.jackjyq.com/' -H 'Content-Type: application/json'`

### 批量查询 IP 归属地

**HTTP POST**: https://ip.jackjyq.com/ips

**请求**:

```json
{
  "ips": ["127.0.0.1", "114.114.114.114", "8.8.8.8"],
  "database": "both"
}
```

database 选项：

- both: 默认值，返回完整
- ip2region: 速度快，请求数量大
- GeoLite2: 可选

**例如**:

```shell
curl -X POST -H "Content-Type: application/json" -d '{
  "ips": ["127.0.0.1", "114.114.114.114", "8.8.8.8"],
  "database": "both"
}' https://ip.jackjyq.com/ips
```

**返回**:

```json
{
  "127.0.0.1": {
    "ip": "127.0.0.1",
    "country": null,
    "region": null,
    "province": null,
    "city": "内网IP",
    "isp": "内网IP",
    "database_name": "ip2region",
    "database_href": "https://gitee.com/lionsoul/ip2region/"
  },
  "114.114.114.114": {
    "ip": "114.114.114.114",
    "country": "中国",
    "region": null,
    "province": "江苏省",
    "city": "南京市",
    "isp": null,
    "database_name": "ip2region",
    "database_href": "https://gitee.com/lionsoul/ip2region/"
  },
  "8.8.8.8": {
    "ip": "8.8.8.8",
    "country": "美国",
    "region": null,
    "province": "加州",
    "city": "洛杉矶",
    "isp": null,
    "database_name": "GeoLite2",
    "database_href": "https://www.maxmind.com/"
  }
}
```

## 数据源

### IP 归属地

- 国内 IP: [ip2region](https://github.com/lionsoul2014/ip2region)
- 国外 IP: [MaxMind GeoLite2](https://www.maxmind.com/en/home)

### 经纬度位置

- [Nominatim](https://nominatim.org/)

## 参考

- [Information about your Web browser](http://www.alanwood.net/demos/browserinfo.html)
