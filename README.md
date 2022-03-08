# IP 归属地查询器

一个查看 IP 地址归属地的工具

## 使用说明

### 查看本机 IP 归属地

https://ip.jackjyq.com/

```bash
curl 'https://ip.jackjyq.com/' -H 'Content-Type: application/json'
```

### 查看指定 IP 归属地

https://ip.jackjyq.com/?ip=114.114.114.114

```bash
curl 'https://ip.jackjyq.com/?ip=114.114.114.114' -H 'Content-Type: application/json'
```

## IP 数据库

- 国内 IP: [ip2region](https://github.com/lionsoul2014/ip2region)
- 国外 IP: [MaxMind GeoLite2](https://www.maxmind.com/en/home)

## 本地部署

### 初始化

- 我用的是 Python 3.10, 旧版本（3.8+）可能也能运行
- 不需要安装 mySQL
- ip2region 数据库较小，因此包含在 Git 仓库里，不用单独下载

```bash
python -m virtualenv venv   # 创建虚拟环境
pip install -r requirements.txt     # 安装依赖
chmod +x update_GeoLite2.sh
./update_GeoLite2.sh   # 下载 IP 数据库
```

### 运行

```bash
DEBUG=True python main.py runserver
# 或者
gunicorn main
```
