# IP 归属地查询器

一个查看 IP 地址归属地的工具

## 查看本机 IP 归属地

https://ip.jackjyq.com/

```bash
curl 'https://ip.jackjyq.com/' -H 'Content-Type: application/json'
```

## 查看指定 IP 归属地

https://ip.jackjyq.com/?ip=114.114.114.114

```bash
curl 'https://ip.jackjyq.com/?ip=114.114.114.114' -H 'Content-Type: application/json'
```

## IP 数据库

- 国内 IP: [ip2region](https://github.com/lionsoul2014/ip2region)
- 国外 IP: [MaxMind GeoLite2](https://www.maxmind.com/en/home)
