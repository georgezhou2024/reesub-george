#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鍏嶈垂鑺傜偣鑷姩娴嬫椿璁㈤槄姹?v2 鈥?鍏ㄥ崗璁?路 楂樼簿搴?路 浣庤鏉€
====================================================

鏋舵瀯锛堜笁闃舵娴佹按绾匡級:
  1. 鎶撳彇璁㈤槄婧?鈫?瑙ｆ瀽鍏ㄩ儴鍗忚 URI 涓虹粺涓€鑺傜偣瀵硅薄
     (vless/vmess/trojan/ss/hysteria2/tuic/anytls + reality + 鍏ㄩ儴浼犺緭灞?
  2. 鐪熷疄娴嬫椿锛坰ing-box v1.14 鍐呮牳锛岄€愯妭鐐?SOCKS 鍏ョ珯 + 鑺傜偣鍑虹珯锛?
     - 闃舵A 绔彛棰勬: TCP/QUIC 鐩磋繛鎻℃墜, 蹇€熶涪寮冩绔彛 (鍓婂噺 90% 鏃犳晥宸ヤ綔)
     - 闃舵B 鐪熷疄鎺㈡祴: 澶?URL 鎺㈡祴 (gstatic 204 / cloudflare trace) 
       + 缁忎唬鐞嗗彇鐪熷疄鍑哄彛 IP (api.ip.sb/geoip 鈫?涓€娆℃嬁 country+asn+isp)
       + Cloudflare 闄愭椂涓嬭浇娴嬮€?鈫?鏂祦鑺傜偣璇嗗埆 (鍚炲悙閲忎笉瓒?
       + cloudflare trace tls=VERIFIED 鈫?MITM/鍔寔鑺傜偣璇嗗埆
  3. 鍒嗙被涓庡鍑?
     - 鍥藉: 鍑哄彛 IP ip-api.com 鎵归噺(45req/min 鍏嶈垂) 鈫?MaxMind GeoLite2 鍏滃簳
     - 灞炴€? hosting=true/CDN缃戞/IDC ASN 鈫?鏈烘埧 | mobile=true 鈫?绉诲姩
            | 杩愯惀鍟嗙櫧鍚嶅崟+rDNS 鈫?瀹跺
     - 鍘婚噸: 鍑哄彛IP+绔彛 鍞竴鍖? 瀹跺鍖轰弗鏍奸槻鍚孖P鍒峰睆
"""

import os
import re
import io
import sys
import json
import time
import uuid
import base64
import shutil
import socket
import zipfile
import tarfile
import platform
import subprocess
import ipaddress
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    import yaml
    import maxminddb
except ImportError as e:
    print(f"[!] 缂哄皯渚濊禆: {e} 鈥?璇峰厛 pip install -r requirements.txt")
    sys.exit(1)

# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
# 閰嶇疆
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲

SOURCE_URLS = [
    "https://wild-cloud-9893.heleimail.workers.dev",
    "https://github.com/Au1rxx/free-vpn-subscriptions/raw/main/output/by-country/v2ray-base64-TW.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/all.txt",
    "https://raw.githubusercontent.com/10ium/HiN-VPN/main/subscription/base64/mix",
    "https://raw.githubusercontent.com/10ium/telegram-configs-collector/main/protocols/hysteria",
    "https://raw.githubusercontent.com/10ium/telegram-configs-collector/main/security/tls",
    "https://github.com/Au1rxx/free-vpn-subscriptions/raw/main/output/v2ray-base64.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://open.heleimail.workers.dev/",
    "https://www.ermao.net/sub/v2ray/ermao.net",
    "https://raw.githubusercontent.com/ishalumi/proxy-node-collector/main/output/nodes_base64.txt",
    "https://gist.githubusercontent.com/shuaidaoya/9e5cf2749c0ce79932dd9229d9b4162b/raw/base64.txt",
    "https://raw.githubusercontent.com/PuddinCat/BestClash/main/proxies.yaml",
    "https://raw.githubusercontent.com/twj0/subseek/refs/heads/master/data/sub_github.txt",
]

OUTPUT_DIR = "output"
COUNTRY_DIR = os.path.join(OUTPUT_DIR, "by-country")
RESIDENTIAL_COUNTRY_DIR = os.path.join(OUTPUT_DIR, "residential-by-country")

SINGBOX_VERSION = "v1.14.0"
WORKDIR = os.path.dirname(os.path.abspath(__file__))          # scripts/
BASEDIR = os.path.dirname(WORKDIR)                              # repo root
RUNTIME_DIR = os.path.join(BASEDIR, "runtime")                  # kernels & db
SINGBOX_BIN = os.path.join(RUNTIME_DIR, "sing-box")

# --- 娴嬫椿闃堝€?(姣/绉? ---
# 鈽?鍒嗗眰瓒呮椂: 棣栧嚮瀹?(12s 瀹规參鑺傜偣), 閲嶈瘯绐?(4s 蹇€熸斁寮冩鑺傜偣)
#   渚濇嵁 CI 瀹炴祴: 25 鍒嗛挓閲?~60% 鏃堕棿鐑у湪姝昏妭鐐?3脳12s 婊￠閲嶈瘯涓?
PROBE_TIMEOUT          = 12      # 娲绘€ч鍑昏秴鏃?(绉? 鈥?瀹圭撼鎱㈠惎鍔ㄨ妭鐐?
PROBE_RETRY_TIMEOUT    = 4       # 娲绘€ч噸璇曡秴鏃?(绉? 鈥?姝昏妭鐐瑰揩閫熸斁寮?
PORT_KNOCK_TIMEOUT     = 2.5     # 绔彛棰勬瓒呮椂
IP_ECHO_TIMEOUT        = 6.0     # 鍑哄彛 IP 妫€娴嬭秴鏃?
SPEED_TEST_BYTES       = 2_500_000   # 2.5MB 涓嬭浇娴嬮€?(2.5MB 瓒充互绠楀噯鍚炲悙涓?< 70KB/s 鍒ゅ畾绾夸笉鍙?
SPEED_TEST_BUDGET      = 5.0         # 娴嬮€熸椂闂撮绠?(绉? 鈥?2.5MB@70KB/s=36s 蹇呮柇娴? 5s 棰勭畻瓒冲鍒ゅ瀷
SPEED_MIN_BYTES_PER_S  = 70_000      # 鍚炲悙 < 70KB/s 鍒ゅ畾鏂祦/涓嶅彲鐢?(鏍囧噯涓嶅彉)
IP_ECHO_URLS = [                    # 缁忎唬鐞嗚幏鍙栧嚭鍙?IP (澶氳矾鍐椾綑)
    "https://api.ip.sb/geoip",                         # JSON: country_code/asn/isp
    "https://ipinfo.io/json",                          # JSON: country/org
    "http://ip-api.com/json/?fields=status,query,countryCode,isp,org,as",  # HTTP free
]
LIVENESS_URLS = [                    # 娲绘€ф帰娴?URL (鍏ㄩ儴瑕佹眰浠ｇ悊閾捐矾瀹屾暣)
    "https://www.gstatic.com/generate_204",       # 瀹炴祴 204 OK
    "https://www.google.com/generate_204",
    "http://connectivitycheck.gstatic.com/generate_204",
]
SPEED_TEST_URLS = [               # 娴嬮€熺鐐瑰璺?(瀹炴祴閮ㄥ垎鑺傜偣鍟嗗睆钄?speed.cloudflare.com)
    "https://speed.cloudflare.com/__down?bytes=" + str(SPEED_TEST_BYTES),
    "https://cachefly.cachefly.net/10mb.test",
]
TRACE_URL = "https://www.cloudflare.com/cdn-cgi/trace"      # warp=on 妫€娴嬪澹宠妭鐐?
MAX_WORKERS_TEST    = 48            # 鍚屾椂 sing-box 瀹炴祴鑺傜偣鏁?(Azure 2C7G 瀹炴祴 24鈫?8 绋冲畾; sing-box 鍗曞疄渚?< 30MB)
MAX_WORKERS_FETCH   = 8
MAX_WORKERS_CLASSIFY = 32

# ip-api.com 鍏嶈垂鎵归噺: 15 req/min, 姣?req 鈮?00 IP (浠?HTTP)
IP_API_BATCH_URL = "http://ip-api.com/batch?fields=status,countryCode,isp,org,as,asname,reverse,mobile,proxy,hosting,query"
IP_API_BATCH_SIZE = 100
IP_API_BATCH_RPS_INTERVAL = 4.2     # 60/15s 鈮?姣?4.2s 涓€鎵?

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
# 鍑哄彛 IP 鎯呮姤 (鏈湴绂荤嚎鍏滃簳)
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲

# Cloudflare 瀹樻柟 Anycast 鍏ㄧ綉娈?(鍛戒腑鍗?CDN 浠绘挱, 缁濋潪瀹跺)
CLOUDFLARE_IP_NETWORKS = [ipaddress.ip_network(n) for n in (
    "173.245.48.0/20","103.21.244.0/22","103.22.200.0/22","103.31.4.0/22",
    "141.101.64.0/18","108.162.192.0/18","190.93.240.0/20","188.114.96.0/20",
    "197.234.240.0/22","198.41.128.0/17","162.158.0.0/15","104.16.0.0/13",
    "104.24.0.0/14","172.64.0.0/13","131.0.72.0/22",
)]

# Google / Fastly / Akamai 绛夊父瑙?CDN 涓庝簯鍏ュ彛娈?(鍛戒腑鍗虫爣 CDN/鏈烘埧)
CDN_IP_NETWORKS_EXTRA = [ipaddress.ip_network(n) for n in (
    # Google
    "8.8.4.0/24","8.8.8.0/24","8.34.208.0/20","8.35.192.0/20","34.64.0.0/10","35.184.0.0/13",
    "35.192.0.0/14","35.196.0.0/15","35.200.0.0/13","35.216.0.0/15","35.220.0.0/14",
    "64.15.112.0/20","64.233.160.0/19","66.102.0.0/20","66.249.64.0/19","72.14.192.0/18",
    "74.125.0.0/16","108.177.0.0/17","142.250.0.0/15","172.217.0.0/16","173.194.0.0/16",
    "209.85.128.0/17","216.58.192.0/19","216.239.32.0/19",
    # Fastly
    "23.235.32.0/20","43.249.72.0/22","103.244.50.0/24","103.245.222.0/23",
    "104.156.80.0/20","140.248.64.0/18","146.75.0.0/16","151.101.0.0/16",
    "157.52.64.0/18","167.82.0.0/17","199.232.0.0/16","204.129.196.0/22",
    # Akamai (鏍稿績娈?
    "23.32.0.0/13","23.64.0.0/14","23.192.0.0/11","23.197.0.0/16",
    "95.100.0.0/15","104.64.0.0/10","184.24.0.0/13","184.84.0.0/14",
    # Cloudflare Spectrum / 鎵樼鍏ュ彛
    "104.16.0.0/12",
)]

# 宸茬煡浜?鏈烘埧 ASN (绂荤嚎鍏滃簳鐢? 鍦ㄧ嚎 ip-api hosting=true 涓轰富鍒ゆ嵁)
DATACENTER_ASNS = {
    13335,  # Cloudflare
    16509, 14618,  # AWS
    15169, 396982,  # Google
    8075, 8068,  # Microsoft
    24940,  # Hetzner
    16276,  # OVH
    14061,  # DigitalOcean
    31898, 63949,  # Oracle
    45102,  # Alibaba
    132203,  # Tencent
    20473,  # Choopa/Vultr 鏃╂湡
    60068,  # Datacamp (CDN77)
    55081,  # Hostinger
    197540,  # Hostinger EU
    51167,  # Contabo
    8560,  # 1&1 / IONOS
    42708,  # IONOS
    201814, 49981,  # Hosthatch/Hostkey 绫?
    212238, 46652,  # Serverius/OVH 绫?
    141995, 200019, 136907, 39351, 9009,  # M247/Hosthatch 绛?
    174, 3356, 1299, 2914, 6939,  # 楠ㄥ共 (Cogent/Lumen/Arelion/NTT/Hurricane)
    199524, 206096, 49505,  # Selectel/WorldStream
    62240, 49304, 34665, 209242, 219337, 44477,
    200651, 202685, 210644, 205628, 51852, 204544, 397373, 140224,  # 灏忓瀷 IDC
    54866,  # Parsebian/HydraTransit 绫?
    45899,  # VNPT 浜? 鏍囪涓?IDC
    # 鈽?瀹炴祴婕忕綉: 鏀惰喘瀹跺娈?浼 DSL rDNS 鐨勪簯杈圭綉缁?(ip-api proxy=true 妗堜緥琛ュ厖)
    62610,  # Zenlayer (AS62610, rDNS 甯?dsl.speakeasy.net 浣?proxy=true)
    60205,  # 62610 鍏宠仈娈?
    8342,  # Deltacomputers/Evrasia 绫?
    9009, 47692, 62041, 56630, 57502,  # Serverius/ProXmedia/Clouvider 绫?
}

# 姘戠敤瀹藉甫 ASN 鐧藉悕鍗?(绂荤嚎鍏滃簳; 鍏抽敭鍥藉涓绘祦杩愯惀鍟?
RESIDENTIAL_ASNS = {
    # 鍙版咕
    3462,    # Chunghwa Telecom (涓崕鐢典俊)
    9924, 17709, 4780, 18049,  # 浜氬お鐢典俊/杩滀紶/鍙版咕澶у摜澶?鍑摌
    9269, 3491,  # 鍙版咕纭曠綉/鍜屽畤瀹介
    # 棣欐腐
    4760, 476, 4515, 9229, 9266, 10103,  # PCCW/HKT/CUHK/HGC/HKBN/HKTBB
    9059, 38861,  # Hong Kong Broadband
    # 鏃ユ湰
    4713, 2516, 17676, 4721, 2497, 9605, 17511, 9318, 2518, 20193,
    # Softbank/NTT Communications/KDDI/IIJ/Sony/Plala/@nifty/JCN
    4766, 3786, 17816, 9357,
    # 闊╁浗
    4713, 9318, 17816, 9357, 4766,  # KT/LG/SK  
    # 缇庡浗
    701, 7018, 7922, 20115, 22773, 10796, 20057, 11427, 10507, 6128,
    33363, 21928, 10777, 33660, 33661, 33662, 36466, 53417, 55136,
    20057, 19024, 12271, 11404, 6983, 33554, 7155, 30162, 10790,
    # Comcast (7922/33487/22263...) / Charter (20115/10796/20057) / Cox / AT&T / Verizon
    702, 703, 704, 705, 706, 709, 710, 711, 712, 713, 714, 715,  # legacy Verizon
    2828, 20001, 3549,  # CenturyLink/Level3 (閮ㄥ垎涓哄瀹?
    6167, 6162, 7018,  # AT&T
    5056,  # Cox East
    10796,  # Charter
    11351,  # TWC
    6128,  # Atlantis
    # 鑻卞浗
    2856, 5607, 20650, 13285, 12576, 12725, 19541, 33950, 5413,
    # BT/TalkTalk/Orange/Virgin/Plusnet/Sky/Eclipse
    # 寰峰浗
    3320, 3209, 6805, 8888, 9145, 13237, 15366, 20879, 16097, 15594,
    # DT/Vodafone/EWE/netcup/Telef贸nica
    # 娉曞浗
    3215, 12322, 15557, 5410, 21590, 22869, 8228, 8220, 12670,
    # Orange/Free/SFR/Bouygues/LDN/9.tel
    # 鑽峰叞 / 姣斿埄鏃?
    33915, 20857, 5418, 6777, 15535, 6830, 8683,
    # KPN/Ziggo/Tele2/Solcon/Proximus/Telenet
    # 鍔犳嬁澶?
    577, 6539, 812, 7992, 22995, 23498, 30645, 11260, 5645, 13331,
    # Bell/Rogers/Corus/Cogeco/Videotron/Telus
    # 婢冲ぇ鍒╀簹 / 鏂拌タ鍏?
    1221, 4764, 4761, 4747, 4802, 4804, 38293, 9443, 23871, 4771,
    # Telstra/Optus/iinet/AAPT/Exetel/SparkNZ
    # 鏂板姞鍧?/ 椹潵瑗夸簹
    9506, 9224, 10091, 4657, 32308, 55553, 177545, 9534, 17971, 24210,
    # Singtel/StarHub/M1/MyRepublic/TM/Maxis/Time
    # 宸磋タ / 鎷夌編
    28573, 26599, 28598, 22085, 27699, 11014, 16832, 16397, 26615,
    # Claro/Vivo/Algar/Brisanet
    # 鍦熻€冲叾 / 淇勭綏鏂?/ 鍝堣惃鍏?
    9121, 34984, 15924, 31103, 47853, 25513, 12714, 8359, 12389,
    # T眉rk Telekom/Vodafone TR/MTS/Rostelecom/Kazakhtelecom
    # 鎰忓ぇ鍒?/ 瑗跨彮鐗?
    3269, 30722, 12874, 12392, 12474, 3352, 12479, 12430,
    # Telecom Italia/Fastweb/Vodafone IT/Telef贸nica ES
    # 鍗板害 / 瓒婂崡 / 娉板浗 / 鑿插緥瀹?/ 鍗板凹
    55836, 9829, 9498, 17813, 45899, 7552, 9675, 7568, 45773, 45543,
    7590, 17457, 7552, 131293, 9336, 23969, 17816, 24099, 38251,
    # 鍗板凹 Telkomsel/Indosat/Smartfren; 瓒婂崡 Viettel/FPT; 娉板浗 AIS/True
}

# rDNS / ISP 鍚嶇О鍏抽敭璇?(澶у皬鍐欎笉鏁忔劅; 绂荤嚎鍏滃簳)
IDC_NAME_PATTERNS = [
    "hosting", "hoster", "datacenter", "data center", "cloud", "server",
    "vps", "dedicated", "colo", "colocation", "compute", "storage",
    "amazon", "aws", "google cloud", "microsoft", "azure", "oracle",
    "digitalocean", "linode", "vultr", "choopa", "hetzner", "ovh",
    "contabo", "m247", "leaseweb", "online s.a.s", "scaleway",
    "alibaba", "tencent", "huawei cloud", "ucloud", "jdcloud", "ksyun",
    "fastly", "cloudflare", "akamai", "cdn", "anycast", "edge network",
    "hostkey", "selectel", "aeza", "justhost", "idnica", "hostinger",
    "ionos", "1&1", "godaddy", "namecheap", "sucuri", "ispxk",
    "zenlayer", "zencom", "g-core", "gcore", "netcup", "hetzner",
]

RESIDENTIAL_NAME_PATTERNS = [
    # 閫氱敤瀹跺鐗瑰緛
    "broadband", "pppoe", "pppoa", "dsl", "cable", "fiber", "ftth",
    "fibre", "dynamic", "dial", "dialup", "residential", "home",
    "consumer", "cust", "customer", "subscriber", "pool", "dynamic-ip",
    # 鍙版咕
    "chunghwa", "hinet", "taiwanmobile", "twn", "aptg", "kbro",
    "tfn", "sparq", "seednet", "data communication business group",
    # 棣欐腐
    "hkbn", "hong kong broadband", "pccw", "hkt", "hgc", "smartone",
    "netvigator", "citic telecom", "i-cable", "hk cable",
    # 鏃ユ湰
    "softbank", "ocn", "plala", "so-net", "iiJmio home", "eonet",
    "kddi", "jcom", "au broadband", "biglobe", "nifty",
    # 闊╁浗
    "korea telecom", "kt corp", "sk broadband", "lgu+", "lg uplus",
    # 缇庡浗
    "comcast", "charter communications", "spectrum", "cox communications",
    "at&t", "at and t", "bellsouth", "sbc internet", "qwest", "centurylink",
    "verizon fios", "verizon online", "frontier communications", "windstream",
    "altice", "optimum online", "rcn", "wave broadband", "consolidated",
    "hughes", "viasat", "starlink", "mediaserv",
    # 娆ф床
    "deutsche telekom", "telekom deutschland", "vodafone d2", "kabel deutschland",
    "british telecom", "bt broadband", "virgin media", "sky uk", "talktalk",
    "orange sa", "free SAS".lower(), "sfr", "bouygues", "bbox", "numericable",
    "kpn", "ziggo", "t-mobile netherlands", "proximus", "telenet",
    "telefonica", "movistar", "vodafone espana", "jazztel", "orange es",
    "telecom italia", "fastweb home", "iliad italia", "windtre",
    "swisscom", "a1 telekom", "magyar telekom", "o2 czech",
    "telia sweden", "telenor", "tele2 sweden", "bredband2",
    "rostelecom home", "mgts", "ertelecom", "dom.ru", "mtu-moscow",
    # 浜氬お鍏朵粬
    "singtel", "starhub", "m1 limited", "myrepublic", "viewqwest",
    "maxis", "unifi", "time dotcom", "tm net", "celcom",
    "ais", "true internet", "3bb", "dtac tri", "ntc net",
    "viettel", "vnpt", "fpt telecom", "cmc telecom", "vinaphone",
    "pldt", "globe telecom", "converge ict", "sky broadband ph",
    "telkomsel", "indosat", "xl axiata", "biznet networks", "first media",
    # 鎷夌編 / 鍦熻€冲叾 / 鍏朵粬
    "claro", "vivo", "tim brasil", "oi internet", "net servicos",
    "turk telekom", "superonline", "ttk", "kablonet", "vodafone net",
    " kazakhtelecom", "beeline kz", "izatelecom",
    "bigpond", "iinet", "optus", "tpg internet", "aussie broadband",
    "spark nz", "vodafone nz", "2degrees", "orcon", "slingshot",
]

# 鍗忚 鈫?鍏ㄧО (鍛藉悕鐢?
PROTOCOL_LABELS = {
    "vless": "VLESS", "vmess": "VMESS", "trojan": "Trojan",
    "ss": "Shadowsocks", "hysteria2": "Hysteria2", "tuic": "TUIC",
    "anytls": "AnyTLS",
}

COUNTRY_NAMES = {
    "HK": "涓浗棣欐腐 (Hong Kong)", "TW": "涓浗鍙版咕 (Taiwan)", "JP": "鏃ユ湰 (Japan)",
    "SG": "鏂板姞鍧?(Singapore)", "US": "缇庡浗 (United States)", "KR": "闊╁浗 (South Korea)",
    "DE": "寰峰浗 (Germany)", "GB": "鑻卞浗 (United Kingdom)", "CA": "鍔犳嬁澶?(Canada)",
    "FR": "娉曞浗 (France)", "NL": "鑽峰叞 (Netherlands)", "RU": "淇勭綏鏂?(Russia)",
    "IN": "鍗板害 (India)", "AU": "婢冲ぇ鍒╀簹 (Australia)", "IT": "鎰忓ぇ鍒?(Italy)",
    "ES": "瑗跨彮鐗?(Spain)", "TR": "鍦熻€冲叾 (Turkey)", "AE": "闃胯仈閰?(UAE)",
    "BR": "宸磋タ (Brazil)", "MY": "椹潵瑗夸簹 (Malaysia)", "TH": "娉板浗 (Thailand)",
    "VN": "瓒婂崡 (Vietnam)", "PH": "鑿插緥瀹?(Philippines)", "ID": "鍗板凹 (Indonesia)",
    "MX": "澧ㄨタ鍝?(Mexico)", "AR": "闃挎牴寤?(Argentina)", "CL": "鏅哄埄 (Chile)",
    "CO": "鍝ヤ鸡姣斾簹 (Colombia)", "PE": "绉橀瞾 (Peru)", "ZA": "鍗楅潪 (South Africa)",
    "EG": "鍩冨強 (Egypt)", "KE": "鑲凹浜?(Kenya)", "NG": "灏兼棩鍒╀簹 (Nigeria)",
    "UA": "涔屽厠鍏?(Ukraine)", "PL": "娉㈠叞 (Poland)", "SE": "鐟炲吀 (Sweden)",
    "NO": "鎸▉ (Norway)", "FI": "鑺叞 (Finland)", "DK": "涓归害 (Denmark)",
    "CH": "鐟炲＋ (Switzerland)", "AT": "濂ュ湴鍒?(Austria)", "BE": "姣斿埄鏃?(Belgium)",
    "IE": "鐖卞皵鍏?(Ireland)", "PT": "钁¤悇鐗?(Portugal)", "GR": "甯岃厞 (Greece)",
    "CZ": "鎹峰厠 (Czech)", "RO": "缃楅┈灏间簹 (Romania)", "HU": "鍖堢墮鍒?(Hungary)",
    "IL": "浠ヨ壊鍒?(Israel)", "SA": "娌欑壒 (Saudi Arabia)", "QA": "鍗″灏?(Qatar)",
    "KZ": "鍝堣惃鍏嬫柉鍧?(Kazakhstan)", "UZ": "涔屽吂鍒厠鏂潶 (Uzbekistan)",
    "PK": "宸村熀鏂潶 (Pakistan)", "BD": "瀛熷姞鎷?(Bangladesh)", "LK": "鏂噷鍏板崱 (Sri Lanka)",
    "NP": "灏兼硦灏?(Nepal)", "MM": "缂呯敻 (Myanmar)", "KH": "鏌煍瀵?(Cambodia)",
    "LA": "鑰佹対 (Laos)", "NZ": "鏂拌タ鍏?(New Zealand)", "EE": "鐖辨矙灏间簹 (Estonia)",
    "LV": "鎷夎劚缁翠簹 (Latvia)", "LT": "绔嬮櫠瀹?(Lithuania)", "BG": "淇濆姞鍒╀簹 (Bulgaria)",
    "RS": "濉炲皵缁翠簹 (Serbia)", "HR": "鍏嬬綏鍦颁簹 (Croatia)", "SK": "鏂礇浼愬厠 (Slovakia)",
    "SI": "鏂礇鏂囧凹浜?(Slovenia)", "IS": "鍐板矝 (Iceland)", "LU": "鍗㈡．鍫?(Luxembourg)",
    "MT": "椹€充粬 (Malta)", "CY": "濉炴郸璺柉 (Cyprus)", "GE": "鏍奸瞾鍚変簹 (Georgia)",
    "AM": "浜氱編灏间簹 (Armenia)", "AZ": "闃垮鎷滅枂 (Azerbaijan)", "MD": "鎽╁皵澶氱摝 (Moldova)",
    "BY": "鐧戒縿缃楁柉 (Belarus)", "SC": "濉炶垖灏?(Seychelles)", "OTHER": "鍏朵粬鍦板尯 (Other)",
}


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
# 宸ュ叿鍑芥暟
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲

def get_country_flag(country_code: str) -> str:
    if not country_code:
        return "馃寪"
    cc = country_code.upper()
    if cc in ("OTHER", "ZZ", "XX", "T1", "A1", "A2"):
        return "馃寪"
    if len(cc) == 2 and cc.isalpha() and cc.isascii():
        return chr(ord(cc[0]) + 127397) + chr(ord(cc[1]) + 127397)
    return "馃寪"


def b64_decode(data: str) -> str:
    """瀹归敊 base64 瑙ｇ爜 (鏀寔 URL-safe / 缂哄け padding)"""
    data = data.strip()
    try:
        pad = -len(data) % 4
        if data and data[-1] not in "=":
            data += "=" * pad
        raw = base64.urlsafe_b64decode(data)
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        pass
    try:
        raw = base64.b64decode(data + "=" * (-len(data) % 4))
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
# HTTP 浼氳瘽 (涓ゅ垎绂昏璁?:
#
# 銆愯璁″畾浣? 娴嬫椿瑙嗚 = GitHub Actions 缇庡浗寰蒋浜?(娴峰鐩磋繛鑺傜偣)銆?
#   鑺傜偣浠庢捣澶栧彲杈惧嵆鍏ュ簱; 澶ч檰鐢ㄦ埛缁忓墠缃唬鐞?閾惧紡)璁块棶 鈥斺€?涓?CI 鍚岃瑙掋€?
#   鍥犳: 鏈湴寮€鍙戞満 (澶ч檰缃戠粶) 鍙敤浜庤皟璇? 鎶撹闃呮簮闇€鍊熺郴缁熶唬鐞嗚繃澧?
#   鐢熶骇鐜 (Actions) 鏃犱唬鐞嗙洿杩? 澶╃劧姝ｇ‘銆?
#
#   - DIRECT_SESSION (trust_env=True): 鎶撹闃呮簮/涓嬭浇鏁版嵁搴?IP鎯呮姤/Scamalytics銆?
#       鏈湴: 缁忕郴缁熶唬鐞?(v2rayN) 杩囧; Actions: 鐩磋繛 鈥?涓ょ鐜閮芥纭€?
#   - PROBE_SESSION (trust_env=False): 缁?sing-box SOCKS 鎺㈡祴鑺傜偣銆?
#       寮哄埗闅旂鐜浠ｇ悊, 淇濊瘉娴嬬殑鏄?杩愯鏈衡啋鑺傜偣"鐪熷疄閾捐矾銆?
#       (鏈湴璋冭瘯鏃跺彈 GFW 褰卞搷鐨勫け璐?鈮?鑺傜偣姝讳骸, Actions 涓婁細寰楀埌鐪熷疄缁撴灉;
#        瀹佸彲鏈湴澶氭潃, 涓嶅彲 CI 璇潃 鈥?鐢熶骇鍒ゅ畾浠?Actions 涓哄噯)
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲

DIRECT_SESSION = requests.Session()
DIRECT_SESSION.trust_env = True    # 璺熼殢绯荤粺/鐜浠ｇ悊 (鏈湴澶ч檰缃戠粶鎶?GitHub 闇€瑕? Actions 鏃犱唬鐞嗙洿杩炰笉鍙楀奖鍝?
DIRECT_SESSION.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})

PROBE_SESSION = requests.Session()
PROBE_SESSION.trust_env = False    # 寮哄埗闅旂: 鑺傜偣鎺㈡祴閾捐矾缁濅笉缁忔湰鏈轰唬鐞? 闃叉薄鏌撴祴璇曠粨鏋?
PROBE_SESSION.headers.update({"User-Agent": USER_AGENT})


def http_get(url: str, timeout: int = 15, headers: dict = None) -> requests.Response:
    h = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        h.update(headers)
    return DIRECT_SESSION.get(url, timeout=timeout, headers=h)


def ensure_directories():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(COUNTRY_DIR, exist_ok=True)
    os.makedirs(RESIDENTIAL_COUNTRY_DIR, exist_ok=True)
    os.makedirs(RUNTIME_DIR, exist_ok=True)


def is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip())
        return True
    except ValueError:
        return False


def parse_host_port(hostinfo: str):
    """瑙ｆ瀽 '[v6]:port' 鎴?'v4:port' 鎴?'host:port'"""
    hostinfo = hostinfo.strip()
    if hostinfo.startswith("["):
        m = re.match(r"^\[([^\]]+)\](?::(\d+))?$", hostinfo)
        if m:
            return m.group(1), int(m.group(2)) if m.group(2) else 0
        return hostinfo, 0
    if hostinfo.count(":") == 1:
        host, _, port = hostinfo.rpartition(":")
        if host and port.isdigit():
            return host, int(port)
    if hostinfo.count(":") > 1 and is_ip_literal(hostinfo):
        return hostinfo, 0  # 瑁?IPv6 鏃犵鍙?
    parts = hostinfo.rsplit(":", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], int(parts[1])
    return hostinfo, 0


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
# 鐜鍑嗗 (sing-box / GeoLite)
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲

def download_file(url: str, dest: str, timeout: int = 300, retries: int = 3):
    """涓嬭浇鏂囦欢鍒版湰鍦? 鍒嗗潡娴佸紡 + 鍘熷瓙鏇挎崲 + 閲嶈瘯 + 闀滃儚鍒囨崲
    (GitHub 鐩磋繛澶辫触鑷姩灏濊瘯 jsdelivr 闀滃儚 鈥?鏈湴澶ч檰缃戠粶/CI 鍋跺彂闄愭祦閮芥洿绋?"""
    if os.path.exists(dest) and os.path.getsize(dest) > 1024:
        return
    # 闀滃儚: github.com/OWNER/REPO/... 鈫?cdn.jsdelivr.net/gh/OWNER/REPO@...
    mirrors = [url]
    m = re.match(r"^https://(?:github\.com|raw\.githubusercontent\.com)/([^/]+)/([^/]+)/(?:raw|releases/download)/(.+)$", url)
    if m and "releases/download" not in url:
        owner, repo, path = m.groups()
        mirrors.append(f"https://cdn.jsdelivr.net/gh/{owner}/{repo.replace('.git','')}@{path}")
    print(f"[*] 涓嬭浇: {url}")
    tmp = dest + ".part"
    last_err = None
    for mirror in mirrors:
        for attempt in range(retries):
            try:
                with DIRECT_SESSION.get(mirror, timeout=timeout, stream=True,
                                        headers={"Accept": "*/*"}) as r:
                    r.raise_for_status()
                    with open(tmp, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1 << 20):
                            if chunk:
                                f.write(chunk)
                if os.path.getsize(tmp) < 1024:
                    raise RuntimeError(f"涓嬭浇涓嶅畬鏁? {os.path.getsize(tmp)} bytes")
                os.replace(tmp, dest)
                return
            except Exception as e:
                last_err = e
                if attempt < retries - 1:
                    wait = 3 * (attempt + 1)
                    print(f"[!] 涓嬭浇澶辫触 (绗瑊attempt+1}娆?: {str(e)[:70]} 鈥?{wait}s 鍚庨噸璇?)
                    time.sleep(wait)
        if len(mirrors) > 1 and mirror != mirrors[-1]:
            print(f"[!] 鍒囨崲闀滃儚: {mirrors[1]}")
    # 娓呯悊澶辫触鐨勫崐鎴枃浠?
    try:
        if os.path.exists(tmp):
            os.remove(tmp)
    except OSError:
        pass
    raise RuntimeError(f"涓嬭浇鏈€缁堝け璐?({mirrors[0]}): {last_err}")


def setup_environment():
    print("[*] 鍑嗗 sing-box 鍐呮牳涓?GeoLite2 绂荤嚎鏁版嵁搴?...")
    os.makedirs(RUNTIME_DIR, exist_ok=True)

    # --- sing-box ---
    exe = SINGBOX_BIN + (".exe" if os.name == "nt" else "")
    if not os.path.exists(exe) or os.path.getsize(exe) < 1024:
        system = "windows" if os.name == "nt" else "linux"
        ext = "zip" if system == "windows" else "tar.gz"
        url = (f"https://github.com/SagerNet/sing-box/releases/download/"
               f"{SINGBOX_VERSION}/sing-box-{SINGBOX_VERSION.lstrip('v')}-{system}-amd64.{ext}")
        archive = os.path.join(RUNTIME_DIR, f"sing-box.{ext}")
        download_file(url, archive)
        if system == "windows":
            with zipfile.ZipFile(archive) as z:
                for name in z.namelist():
                    if name.endswith("sing-box.exe"):
                        with z.open(name) as src, open(exe, "wb") as dst:
                            shutil.copyfileobj(src, dst)
        else:
            with tarfile.open(archive) as t:
                for m in t.getmembers():
                    if m.name.endswith("sing-box"):
                        f = t.extractfile(m)
                        with open(exe, "wb") as dst:
                            shutil.copyfileobj(f, dst)
        os.chmod(exe, 0o755)
        try:
            os.remove(archive)
        except OSError:
            pass
    # 鏍￠獙鍐呮牳鍙繍琛?
    try:
        ver = subprocess.run([exe, "version"], capture_output=True, text=True, timeout=20)
        first = (ver.stdout or "").splitlines()[0] if ver.stdout else "?"
        print(f"[+] sing-box 鍐呮牳灏辩华: {first.strip()}")
    except Exception as e:
        print(f"[!] sing-box 鍐呮牳鏃犳硶杩愯: {e}")
        raise

    # --- GeoLite2 鏁版嵁搴?---
    country_db = os.path.join(RUNTIME_DIR, "Country.mmdb")
    asn_db = os.path.join(RUNTIME_DIR, "ASN.mmdb")
    download_file("https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb", country_db)
    download_file("https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-ASN.mmdb", asn_db)
    print(f"[+] GeoLite 鏁版嵁搴撳氨缁? Country={os.path.getsize(country_db)//1024}KB, ASN={os.path.getsize(asn_db)//1024}KB")


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# 鑺傜偣 URI 瑙ｆ瀽 (鍏ㄥ崗璁?鈫?sing-box outbound JSON)
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

def _query_dict(query: str) -> dict:
    return {k: v[0] for k, v in urllib.parse.parse_qs(query, keep_blank_values=True).items()}


def _parse_tls_params(params: dict, host: str) -> dict:
    """浠?URI query 鎻愬彇 TLS/Reality 璁剧疆 鈫?sing-box 鏍煎紡"""
    security = params.get("security", "").lower()
    tls = {}
    if security == "reality":
        pbk = params.get("pbk", "")
        if not pbk:
            return None
        tls = {
            "enabled": True,
            "server_name": params.get("sni", params.get("peer", host)),
            "utls": {"enabled": True, "fingerprint": params.get("fp", "chrome")},
            "reality": {"enabled": True, "public_key": pbk, "short_id": params.get("sid", "")},
        }
    elif security in ("tls", "xtls"):
        tls = {
            "enabled": True,
            "server_name": params.get("sni", params.get("peer", host)),
            "insecure": params.get("allowInsecure", "0") in ("1", "true"),
            "alpn": params.get("alpn", "").split(",") if params.get("alpn") else None,
        }
        if params.get("fp"):
            tls["utls"] = {"enabled": True, "fingerprint": params["fp"]}
        if tls.get("alpn") is None:
            del tls["alpn"]
    return tls or None


def _parse_transport(params: dict) -> dict:
    """浠?URI query 鎻愬彇浼犺緭灞?鈫?sing-box transport 鏍煎紡"""
    network = params.get("type", "tcp").lower()
    if network in ("tcp", "none", "raw"):
        return None
    if network == "ws":
        t = {"type": "ws"}
        if params.get("path"):
            t["path"] = urllib.parse.unquote(params["path"])
        if params.get("host"):
            t["headers"] = {"Host": params["host"]}
        # 0-RTT early data (v2ray ws 0-RTT: path 鍚??ed=2560 鏃剁敱 max-early-data 鎸囧畾)
        if params.get("ed"):
            t["max_early_data"] = 2560
            t["early_data_header_name"] = "Sec-WebSocket-Protocol"
        return t
    if network in ("grpc", "gun"):
        t = {"type": "grpc"}
        if params.get("serviceName"):
            t["service_name"] = urllib.parse.unquote(params["serviceName"])
        return t
    if network in ("h2", "http"):   # v2ray 鐢熸€佷袱绉嶅啓娉曢兘鏈? type=h2 / type=http (瀵煎嚭鐢?http, 鍏煎涓よ€?
        t = {"type": "http"}
        host = params.get("host", "")
        if host:
            t["host"] = [h for h in host.split(",") if h]
        if params.get("path"):
            t["path"] = urllib.parse.unquote(params["path"])
        return t
    if network == "httpupgrade":
        t = {"type": "httpupgrade"}
        if params.get("path"):
            t["path"] = urllib.parse.unquote(params["path"])
        if params.get("host"):
            t["host"] = params["host"]
        return t
    return None


def parse_vless(uri: str):
    """vless://uuid@host:port?params#name"""
    m = re.match(r"^vless://([^@#]+)@(\[[^\]]+\]|[^:@/]+):(\d+)(?:[/?]([^#]*))?(?:#(.*))?$", uri)
    if not m:
        return None
    user, host, port, query, _name = m.groups()
    params = _query_dict(query or "")
    tls = _parse_tls_params(params, host)
    if params.get("security", "").lower() == "reality" and tls is None:
        return None  # reality 缂?pbk 鏃犳硶娴?
    outbound = {
        "type": "vless",
        "tag": "node",
        "server": host,
        "server_port": int(port),
        "uuid": user,
    }
    flow = params.get("flow", "")
    if flow and ("vision" in flow or "xtls" in flow):
        outbound["flow"] = flow
    if tls:
        outbound["tls"] = tls
    transport = _parse_transport(params)
    if transport:
        outbound["transport"] = transport
    return outbound


def parse_vmess(uri: str):
    """vmess://base64({v,ps,add,port,id,aid,net,tls,sni,path,host,type})"""
    data = json.loads(b64_decode(uri[8:]))
    if not data:
        return None
    server = str(data.get("add", "")).strip()
    port = int(data.get("port", 0) or 0)
    if not server or port <= 0:
        return None
    outbound = {
        "type": "vmess",
        "tag": "node",
        "server": server,
        "server_port": port,
        "uuid": str(data.get("id", "")).strip(),
        "security": "auto",
    }
    aid = int(data.get("aid", 0) or 0)
    if aid > 0:
        outbound["alter_id"] = aid
    net = str(data.get("net", "tcp")).lower()
    if data.get("tls") in ("tls", "1", 1, True):
        outbound["tls"] = {
            "enabled": True,
            "server_name": str(data.get("sni") or data.get("host") or server).strip(),
            "insecure": str(data.get("verify_cert", "false")).lower() in ("true", "1"),
        }
    transport = None
    if net in ("ws",):
        transport = {"type": "ws"}
        if data.get("path"):
            transport["path"] = str(data["path"])
        if data.get("host"):
            transport["headers"] = {"Host": str(data["host"])}
    elif net in ("grpc", "gun"):
        transport = {"type": "grpc"}
        if data.get("path"):
            transport["service_name"] = str(data["path"])
    elif net == "h2":
        transport = {"type": "http"}
        if data.get("path"):
            transport["path"] = str(data["path"])
        if data.get("host"):
            transport["host"] = [str(data["host"])]
    elif net == "httpupgrade":
        transport = {"type": "httpupgrade"}
        if data.get("path"):
            transport["path"] = str(data["path"])
        if data.get("host"):
            transport["host"] = str(data["host"])
    if transport:
        outbound["transport"] = transport
    return outbound


def parse_trojan(uri: str):
    """trojan://password@host:port?params#name"""
    m = re.match(r"^trojan://([^@#]+)@(\[[^\]]+\]|[^:@/]+):(\d+)(?:[/?]([^#]*))?(?:#(.*))?$", uri)
    if not m:
        return None
    password, host, port, query, _ = m.groups()
    params = _query_dict(query or "")
    outbound = {
        "type": "trojan",
        "tag": "node",
        "server": host,
        "server_port": int(port),
        "password": urllib.parse.unquote(password),
        "tls": {
            "enabled": True,
            "server_name": params.get("sni", params.get("peer", host)),
            "insecure": params.get("allowInsecure", "0") in ("1", "true"),
        },
    }
    if params.get("alpn"):
        outbound["tls"]["alpn"] = params["alpn"].split(",")
    if params.get("fp"):
        outbound["tls"]["utls"] = {"enabled": True, "fingerprint": params["fp"]}
    transport = _parse_transport(params)
    if transport:
        outbound["transport"] = transport
    return outbound


def parse_ss(uri: str):
    """ss://base64(method:password)@host:port#name  鎴? ss://method:password@... (SIP002)"""
    body = uri[5:].split("#", 1)[0]
    name = urllib.parse.unquote(uri.split("#", 1)[1]) if "#" in uri else ""
    # SIP002: method:password@host:port
    if "@" in body:
        userinfo, _, hostinfo = body.rpartition("@")
        host, port = parse_host_port(hostinfo.split("/")[0].split("?")[0])
        method, password = "", ""
        if ":" in userinfo:
            method, _, password = userinfo.partition(":")
        else:
            dec = b64_decode(userinfo)
            if ":" in dec:
                method, _, password = dec.partition(":")
        method = urllib.parse.unquote(method)
        password = urllib.parse.unquote(password)
        if not (host and port > 0 and method and password):
            return None
        return _ss_outbound(host, port, method, password)
    # legacy: base64(method:password@host:port)
    dec = b64_decode(body)
    if "@" in dec:
        userinfo, _, hostinfo = dec.rpartition("@")
        host, port = parse_host_port(hostinfo.strip())
        method, _, password = userinfo.partition(":")
        if host and port > 0 and method:
            return _ss_outbound(host, port, urllib.parse.unquote(method), urllib.parse.unquote(password))
    return None


def _ss_outbound(host, port, method, password):
    return {
        "type": "shadowsocks",
        "tag": "node",
        "server": host,
        "server_port": int(port),
        "method": method.strip().lower(),
        "password": password,
    }


def parse_hysteria2(uri: str):
    """hy2:// / hysteria2:// auth@host:port?sni=..&obfs=salamander&obfs-password=..&insecure=1
    娉? auth 鍙兘鍚?: / 绛夌壒娈婂瓧绗?(濡?https:// 鍓嶇紑鐨勫瘑鐮? 鈥?浠ユ渶鍚庝竴涓?@ 涓洪敋鐐瑰垎鍓?""
    prefix = "hysteria2://" if uri.startswith("hysteria2://") else "hy2://"
    body = uri[len(prefix):].split("#", 1)[0]
    # 浠ユ渶鍚庝竴涓?@ 鍒嗗壊 (瀵嗙爜鍐呭彲鑳藉惈 @); host 閮ㄥ垎涓嶅惈 @
    at = body.rfind("@")
    if at <= 0:
        return None
    auth, rest = body[:at], body[at+1:]
    m = re.match(r"^(\[[^\]]+\]|[^:/?#]+):(\d+)(?:[/?]([^#]*))?$", rest)
    if not m:
        return None
    host, port, query = m.groups()
    params = _query_dict(query or "")
    outbound = {
        "type": "hysteria2",
        "tag": "node",
        "server": host,
        "server_port": int(port),
        "password": urllib.parse.unquote(auth),
        "tls": {
            "enabled": True,
            "server_name": params.get("sni", params.get("peer", host)),
            "insecure": params.get("allowInsecure", "0") in ("1", "true") or params.get("insecure", "0") in ("1", "true"),
        },
    }
    if params.get("alpn"):
        outbound["tls"]["alpn"] = params["alpn"].split(",")
    if params.get("obfs", "") and params["obfs"] not in ("none", ""):
        outbound["obfs"] = {"type": params["obfs"], "password": params.get("obfs-password", "")}
    mport = params.get("mport") or params.get("ports")
    if mport:
        # 瀹炴祴楠岃瘉: server_ports 鍙帴鍙?"start:end" 鍖洪棿; 瑁稿崟绔彛 "443" 浼?FATAL
        # 鍗曠鍙ｄ繚鐣欏湪 server_port, 鍖洪棿鏀?server_ports (涓よ€呭彲鍏卞瓨, 瀹炴祴 check 閫氳繃)
        singles, ranges = [], []
        for part in str(mport).split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, _, b = part.partition("-")
                if a.strip().isdigit() and b.strip().isdigit():
                    if a.strip() == b.strip():
                        singles.append(a.strip())
                    else:
                        ranges.append(f"{a.strip()}:{b.strip()}")
            elif part.isdigit():
                singles.append(part)
        if ranges or singles:
            # 鍏ㄩ儴杞负 "start:end" 鍖洪棿鏍煎紡 (瀹炴祴: 瑁稿崟绔彛 FATAL)
            outbound["server_ports"] = ranges + [f"{s}:{s}" for s in singles]
            outbound.pop("server_port", None)  # 绔彛璺宠穬鑺傜偣鏃犲浐瀹氬崟绔彛
    return outbound


def _parse_port_range(spec: str):
    """'2087-2097,443' 鈫?sing-box server_ports 鏍煎紡 ['2087:2097', '443:443'] (瀹炴祴: 瑁稿崟绔彛 FATAL, 蹇呴』鍖洪棿)"""
    result = []
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, _, b = part.partition("-")
            if a.strip().isdigit() and b.strip().isdigit():
                result.append(f"{a.strip()}:{b.strip()}")
        elif part.isdigit():
            result.append(f"{part}:{part}")
    return result


def parse_tuic(uri: str):
    """tuic://uuid:password@host:port?congestion_control=bbr&alpn=h3&sni=..&udp_relay_mode=native#name"""
    m = re.match(r"^tuic://([^@#/?]+)@(\[[^\]]+\]|[^:@/?]+):(\d+)(?:[/?]([^#]*))?$", uri.split("#")[0])
    if not m:
        return None
    userinfo, host, port, query = m.groups()
    if ":" not in userinfo:
        return None
    uuid_, _, password = userinfo.partition(":")
    params = _query_dict(query or "")
    outbound = {
        "type": "tuic",
        "tag": "node",
        "server": host,
        "server_port": int(port),
        "uuid": urllib.parse.unquote(uuid_),
        "password": urllib.parse.unquote(password),
        "congestion_control": params.get("congestion_control", "bbr"),
        "udp_relay_mode": params.get("udp_relay_mode", "native"),
        "tls": {
            "enabled": True,
            "server_name": params.get("sni", host),
            "insecure": params.get("allow_insecure", "0") in ("1", "true"),
            "alpn": [a for a in params.get("alpn", "h3").split(",") if a],
        },
    }
    return outbound


def parse_anytls(uri: str):
    """anytls://password@host:port?sni=..&insecure=1#name"""
    m = re.match(r"^anytls://([^@#/?]+)@(\[[^\]]+\]|[^:@/?]+):(\d+)(?:[/?]([^#]*))?$", uri.split("#")[0])
    if not m:
        return None
    password, host, port, query = m.groups()
    params = _query_dict(query or "")
    outbound = {
        "type": "anytls",
        "tag": "node",
        "server": host,
        "server_port": int(port),
        "password": urllib.parse.unquote(password),
        "tls": {
            "enabled": True,
            "server_name": params.get("sni", host),
            "insecure": params.get("insecure", "0") in ("1", "true") or params.get("allowInsecure", "0") in ("1", "true"),
        },
    }
    if params.get("alpn"):
        outbound["tls"]["alpn"] = params["alpn"].split(",")
    return outbound


def parse_ssh(uri: str):
    """ssh://user:pass@host:port#name (灏戣浜庡厤璐规睜, 椤烘墜鏀寔)"""
    m = re.match(r"^ssh://([^@#/?]+)@(\[[^\]]+\]|[^:@/?]+):(\d+)?", uri.split("#")[0])
    if not m:
        return None
    userinfo, host, port = m.groups()
    outbound = {
        "type": "ssh",
        "tag": "node",
        "server": host,
        "server_port": int(port or 22),
        "user": urllib.parse.unquote(userinfo.split(":")[0]),
    }
    if ":" in userinfo:
        outbound["user"] = urllib.parse.unquote(userinfo.split(":")[0])
        outbound["password"] = urllib.parse.unquote(userinfo.split(":", 1)[1])
    return outbound


PARSERS = {
    "vless://": parse_vless,
    "vmess://": parse_vmess,
    "trojan://": parse_trojan,
    "ss://": parse_ss,
    "hy2://": parse_hysteria2,
    "hysteria2://": parse_hysteria2,
    "tuic://": parse_tuic,
    "anytls://": parse_anytls,
    "ssh://": parse_ssh,
}

# 鎺掗櫎鏄庢樉鍔犲瘑娈嬬己/鍗犱綅鑺傜偣
BLACKLIST_NAME_HINTS = re.compile(r"(鍓╀綑娴侀噺|娴侀噺閲嶇疆|expire|expired|瀹樼綉|濂楅|telegram\.me|t\.me/|鑾峰彇璁㈤槄)", re.I)


def parse_node_uri(uri: str):
    """瑙ｆ瀽鑺傜偣 URI 鈫?(outbound, server, port, protocol) ; 澶辫触杩斿洖 None"""
    for prefix, parser in PARSERS.items():
        if uri.startswith(prefix):
            try:
                out = parser(uri)
            except Exception:
                return None
            if not out:
                return None
            proto = out["type"]
            port = out.get("server_port")
            if port is None:  # 绔彛璺宠穬鑺傜偣: 鏃犲浐瀹氱鍙? 鍙栧尯闂撮涓捣鐐圭敤浜庨妫€
                ports = out.get("server_ports") or []
                first = ports[0].split(":")[0] if ports else "0"
                port = int(first)
            if port <= 0:
                return None
            return out, out["server"], int(port), proto
    return None


def extract_nodes_from_text(text: str) -> set:
    results = set()
    if not text:
        return results
    probe = text.strip()
    # 鏈€澶氫笁灞?base64 瑙ｅ寘 (璁㈤槄甯歌鏁翠綋 base64)
    for _ in range(3):
        if any(p in probe for p in ("vmess://", "vless://", "ss://", "trojan://",
                                     "hy2://", "hysteria2://", "tuic://", "anytls://")):
            break
        decoded = b64_decode(probe)
        if not decoded or decoded == probe:
            break
        probe = decoded
    # 鐩存帴鏂囨湰涔熷彲鑳芥贩鏉?base64 琛?
    lines_blob = probe
    pattern = (r'((?:vmess|vless|trojan|ss|hy2|hysteria2|tuic|anytls|ssh)://'
               r'[^\s"\'<>\\]+)')
    for m in re.findall(pattern, lines_blob):
        clean = m.strip().rstrip(".,;'\"")
        if len(clean) > 12:
            results.add(clean)
    return results


def fetch_raw_nodes() -> list:
    nodes = set()
    print("[*] 鎶撳彇鍏ㄩ儴璁㈤槄婧?...")

    def _fetch(url):
        last_err = None
        # 閲嶈瘯 2 娆?(缃戠粶鎶栧姩/GFW 闂存瓏鎬ч噸缃? 閫€閬?3s)
        for attempt in range(3):
            try:
                r = http_get(url, timeout=30)
                if r.status_code == 200:
                    got = extract_nodes_from_text(r.text)
                    return url, got, None
                last_err = f"HTTP {r.status_code}"
            except Exception as e:
                last_err = str(e)[:70]
            if attempt < 2:
                time.sleep(3)
        return url, set(), last_err

    with ThreadPoolExecutor(MAX_WORKERS_FETCH) as ex:
        futs = [ex.submit(_fetch, u) for u in SOURCE_URLS]
        for f in as_completed(futs):
            url, got, err = f.result()
            if err:
                print(f"[!] 鎷夊彇澶辫触 {url} 鈫?{err}")
            else:
                print(f"[+] {url} 鈫?{len(got)} 鑺傜偣")
            nodes.update(got)
    print(f"[*] 鍒濆鎶撳彇鎬婚噺: {len(nodes)}")
    return list(nodes)


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# 闃舵 A: 绔彛棰勬 (鍓婂噺姝昏妭鐐? 閬垮厤鍚庨潰娴垂 sing-box 鍏ㄦ祦绋?
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

# DoH 鍩熷悕瑙ｆ瀽 (Cloudflare): 闃?DNS 姹℃煋 (鏈湴澶ч檰缃戠粶); Actions 涓婇『甯﹁烦杩囧叾鍥藉唴 DNS 闄愬埗
_DNS_CACHE = {}

def resolve_host(host: str) -> str:
    """DoH 瑙ｆ瀽 (甯︽湰鍦扮紦瀛?; 澶辫触閫€鍥炵郴缁?DNS"""
    if not host or is_ip_literal(host):
        return host or ""
    if host in _DNS_CACHE:
        return _DNS_CACHE[host]
    # 1) DoH (Cloudflare 1.1.1.1, 璧?DIRECT_SESSION 鍙繃澧?
    try:
        r = DIRECT_SESSION.get(
            f"https://cloudflare-dns.com/dns-query?name={urllib.parse.quote(host)}&type=A",
            headers={"Accept": "application/dns-json"}, timeout=5)
        if r.status_code == 200:
            answers = r.json().get("Answer") or []
            for a in answers:
                if a.get("type") == 1 and a.get("data"):
                    _DNS_CACHE[host] = a["data"]
                    return a["data"]
    except Exception:
        pass
    # 2) 绯荤粺 DNS 鍏滃簳
    try:
        return socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)[0][4][0]
    except Exception:
        return ""


def knock_port(server: str, port: int, protocol_type: str) -> bool:
    """TCP 鐩磋繛棰勬 (DoH 瑙ｆ瀽闃叉湰鍦?DNS 姹℃煋); QUIC 绫荤洿鎺ユ斁琛岄樁娈礏
    娉? 棰勬澶辫触涓嶆窐姹?(鏈湴澶ч檰瑙嗚鐨勫亣姝?鈮?鑺傜偣姝讳骸), 鍙奖鍝嶆帓搴?
        鐢熸鐢遍樁娈礏 sing-box 鍏ㄦ祦绋嬫祴娲昏鍐?(Actions 娴峰瑙嗚)"""
    if protocol_type in ("hysteria2", "tuic"):
        # QUIC 鏃犳硶杞婚噺棰勬 UDP 绔彛杩為€氭€? 涓旀湰鍦?UDP 甯歌 QoS 鈫?鏀捐浜ら樁娈礏
        return True
    try:
        ip = resolve_host(server)
        if not ip:
            return False
        with socket.create_connection((ip, port), timeout=PORT_KNOCK_TIMEOUT):
            return True
    except Exception:
        return False


def prefilter_candidates(candidates: list) -> list:
    """绔彛棰勬: 閫氳繃鑰呬紭鍏? 鏈€氳繃鑰呴檷绾т繚鐣?(闃叉鏈湴缃戠粶/GFW 瑙嗚璇潃;
    鐪熸鐢熸鐢遍樁娈礏 sing-box 鍏ㄦ祦绋嬫祴娲昏鍐?鈥?Actions 娴峰瑙嗚)"""
    print(f"[*] 绔彛棰勬 (TCP {PORT_KNOCK_TIMEOUT}s): {len(candidates)} 鍊欓€?...")
    passed, deferred = [], []

    def _knock(item):
        raw, outbound, server, port, proto = item
        return knock_port(server, port, proto)

    with ThreadPoolExecutor(max_workers=64) as ex:
        # ex.map 淇濆簭杩斿洖; 閫氳繃鑰呬紭鍏? 鏈€氳繃闄嶇骇淇濈暀 (涓嶆窐姹? 闃叉湰鍦拌瑙掕鏉€)
        for item, ok in zip(candidates, ex.map(_knock, candidates)):
            (passed if ok else deferred).append(item)
    print(f"[+] 棰勬閫氳繃: {len(passed)} | 棰勬鏈繃(淇濈暀浣庝紭鍏堢骇寰呭叏娴?: {len(deferred)}")
    # 棰勬鏈繃鐨勪粛杩涘叆鍏ㄦ祦绋?(鍙槸鎺掑湪鍚庨潰) 鈥?浜ょ粰 sing-box 鐪熷疄瑁佸喅
    return passed + deferred


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# 闃舵 B: sing-box 鐪熷疄娴嬫椿
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

def _alloc_socks_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def build_test_config(outbound: dict, socks_port: int, chain_relay: dict = None) -> dict:
    node = dict(outbound)
    node["tag"] = "node"

    outbounds = [node, {"type": "direct", "tag": "direct"}, {"type": "block", "tag": "block"}]

    # 鈺愨晲 閾惧紡鍓嶇疆 (瀹跺閾惧紡澶嶆祴鐢? 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
    # chain_relay: 宸查獙璇佸瓨娲荤殑 sing-box outbound dict 鈥?node 缁忓畠杞彂 (detour 鍙岃烦)
    # 妯℃嫙鐢ㄦ埛 v2rayN "閾惧紡/鍓嶇疆浠ｇ悊" 鍦烘櫙: 鍓嶇疆 鈫?瀹跺鑺傜偣 鈫?鐩爣
    if chain_relay:
        relay = dict(chain_relay)
        relay["tag"] = "chain-relay"
        # relay 鑷韩鍓?detour (閬垮厤涓?node 鐨?detour 寰幆)
        relay.pop("detour", None)
        outbounds.append(relay)
        node["detour"] = "chain-relay"

    # 鈺愨晲 鍓嶇疆浠ｇ悊 (閾惧紡) 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
    # 妯℃嫙 GitHub Actions 娴峰瑙嗚:
    #   - 鏈湴澶ч檰寮€鍙戞満: 缁忓墠缃唬鐞?榛樿 v2rayN 127.0.0.1:10808)鍑烘捣 鈫?绛夋晥 CI 瑙嗚
    #     (澶ч檰鐩磋繛鐩爣鑺傜偣浼氳 GFW 鎷︽埅, 閫犳垚鏈湴鍋囨 鈮?鑺傜偣姝讳骸)
    #   - GitHub Actions: FRONT_PROXY 涓虹┖ 鈫?鐩磋繛 (Azure US 鏈氨鏄捣澶栬瑙?
    # 鐢ㄦ硶: 鐜鍙橀噺 FRONT_PROXY=socks5://127.0.0.1:10808
    front = os.environ.get("FRONT_PROXY", "").strip()
    if front and not chain_relay:
        # 瑙ｆ瀽 socks5://host:port 鈫?socks outbound
        m = re.match(r"^(socks5h?|http)://([^:]+):(\d+)$", front)
        if m:
            scheme, fhost, fport = m.groups()
            ftype = "socks" if scheme.startswith("socks5") else "http"
            front_out = {
                "type": ftype, "tag": "front-proxy",
                "server": fhost, "server_port": int(fport),
            }
            if ftype == "socks":
                front_out["version"] = "5"
            outbounds.append(front_out)
            # 鑺傜偣鍑虹珯娴侀噺缁忓墠缃唬鐞?(detour 閾惧紡)
            node["detour"] = "front-proxy"
            print_once("_FRONT_ENABLED", f"[*] 鍓嶇疆浠ｇ悊宸插惎鐢? {front} (妯℃嫙 CI 娴峰瑙嗚)")

    config = {
        "log": {"level": "warn"},   # 瀹炴祴: silent 涓嶆槸鍚堟硶绾у埆 (trace/debug/info/warn/error/fatal/panic)
        "inbounds": [{
            "type": "socks",
            "tag": "socks-in",
            "listen": "127.0.0.1",
            "listen_port": socks_port,
            "sniff": False,
        }],
        "outbounds": outbounds,
        "route": {"rules": [], "final": "node"},
    }
    return config


_PRINTED_ONCE = set()


def print_once(key: str, msg: str):
    if key not in _PRINTED_ONCE:
        _PRINTED_ONCE.add(key)
        print(msg)


def test_single_node(item, keep_alive_check=True):
    """杩斿洖 dict 鎴?None; 鍚? 娲绘€?寤惰繜/鍑哄彛IP/鍥藉/ASN/ISP/閫熷害/MITM"""
    raw, outbound, server, port, proto = item
    socks_port = _alloc_socks_port()
    task_id = uuid.uuid4().hex[:10]
    cfg_path = os.path.join(RUNTIME_DIR, f"sb_{task_id}.json")

    # 鈽?閾惧紡鍓嶇疆 (chain relay): 娉ㄥ叆宸查獙璇佸瓨娲昏妭鐐逛綔鍓嶇疆 (chain_retest 鐢? 妯℃嫙 v2rayN 閾惧紡)
    chain_out = None
    chain_json = os.environ.get("CHAIN_RELAY_OUT", "").strip()
    if chain_json:
        try:
            chain_out = json.loads(chain_json)
        except Exception:
            chain_out = None
    config = build_test_config(outbound, socks_port, chain_relay=chain_out)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(config, f)

    exe = SINGBOX_BIN + (".exe" if os.name == "nt" else "")

    # --- 0) sing-box check 棰勬牎楠? 蹇€熸窐姹?schema 閿欒 (瀹炴祴鍙彂鐜?2022 瀵嗛挜闀垮害/绔彛鍖洪棿绛夐敊璇? ---
    try:
        chk = subprocess.run([exe, "check", "-c", cfg_path],
                             capture_output=True, text=True, timeout=15,
                             creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
        if chk.returncode != 0:
            return None  # 閰嶇疆绾ч敊璇?鈫?璇ヨ妭鐐规棤娉曡 sing-box 浣跨敤, 蹇呮窐姹?
    except Exception:
        pass  # check 鏈韩澶辫触涓嶉樆姝㈠悗缁?run 灏濊瘯

    proc = None
    result = None
    try:
        proc = subprocess.Popen(
            [exe, "run", "-c", cfg_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
        )
        # 绛?SOCKS 绔彛灏辩华 (涓诲姩鎺㈡祴鑰岄潪鐩?sleep 鈥?淇鏃х増璇潃)
        deadline = time.time() + 6
        ready = False
        while time.time() < deadline:
            if proc.poll() is not None:
                break  # 杩涚▼宕╂簝 (閰嶇疆閿欒/绔彛鍐茬獊)
            try:
                with socket.create_connection(("127.0.0.1", socks_port), timeout=0.4):
                    ready = True
                    break
            except Exception:
                time.sleep(0.15)
        if not ready:
            return None

        proxies = {"http": f"socks5h://127.0.0.1:{socks_port}",
                   "https": f"socks5h://127.0.0.1:{socks_port}"}

        # --- 1) 娲绘€ф帰娴? 鍒嗗眰瓒呮椂閲嶈瘯 (棣栧嚮瀹?12s 瀹规參鑺傜偣淇濆噯纭巼; 閲嶈瘯绐?4s 蹇€熸斁寮冩鑺傜偣) ---
        alive_hits, latency_ms = 0, 99999
        t0 = time.time()
        for i, url in enumerate(LIVENESS_URLS):
            timeout = PROBE_TIMEOUT if i == 0 else PROBE_RETRY_TIMEOUT
            try:
                r = PROBE_SESSION.get(url, proxies=proxies, timeout=timeout, allow_redirects=False)
                if r.status_code in (204, 200):
                    alive_hits += 1
                    latency_ms = min(latency_ms, (time.time() - t0) * 1000)
                    break  # 浠讳竴鎴愬姛鍗冲彲
            except Exception:
                continue
        if alive_hits == 0:
            return None

        # --- 2) 鐪熷疄鍑哄彛 IP (澶氳矾鍐椾綑) ---
        exit_ip, exit_country, exit_asn, exit_asn_org, exit_isp = None, None, None, None, None
        for url in IP_ECHO_URLS:
            try:
                r = PROBE_SESSION.get(url, proxies=proxies, timeout=IP_ECHO_TIMEOUT)
                if r.status_code != 200:
                    continue
                j = r.json()
                ip = (j.get("ip") or j.get("query") or j.get("your_ip") or "").strip()
                if not ip:
                    continue
                exit_ip = ip
                if url.startswith("https://api.ip.sb"):
                    exit_country = j.get("country_code")
                    exit_asn = j.get("asn")
                    exit_asn_org = (j.get("asn_organization") or j.get("organization") or "")
                    exit_isp = (j.get("isp") or j.get("organization") or "")
                elif url.startswith("https://ipinfo.io"):
                    exit_country = exit_country or (j.get("country") or "").upper()
                    org = j.get("org") or ""
                    if org and not exit_asn:
                        mm = re.match(r"^AS(\d+)\s+(.*)", org)
                        if mm:
                            exit_asn, exit_asn_org = int(mm.group(1)), mm.group(2)
                    exit_isp = exit_isp or org
                elif "ip-api.com" in url:
                    exit_country = exit_country or (j.get("countryCode") or "").upper()
                    exit_asn = exit_asn or j.get("as")
                    exit_asn_org = exit_asn_org or j.get("asname") or j.get("org") or ""
                    exit_isp = exit_isp or j.get("isp") or j.get("org") or ""
                break
            except Exception:
                continue

        # --- 3) MITM 鍔寔妫€娴?(杞婚噺: 澶嶇敤娲绘€ч鍑荤殑 gstatic 璇锋眰宸查獙璇佽瘉涔﹂摼) ---
        # 3a) 鐙珛澶嶆涓€娆″甫 verify=True 鐨勮姹? SSLError = TLS 鎷︽埅
        mitm_risk = False
        try:
            r = PROBE_SESSION.get("https://www.gstatic.com/generate_204", proxies=proxies,
                                  timeout=PROBE_RETRY_TIMEOUT, verify=True)
            if r.status_code in (204, 200):
                mitm_risk = False
            else:
                mitm_risk = r.status_code in (301, 302, 403, 407, 502, 503) or len(r.content) > 0
        except requests.exceptions.SSLError:
            # 璇佷功閾鹃獙璇佸け璐?= TLS 鎷︽埅 (MITM) 鎴栧姡璐ㄨ嚜绛惧姭鎸?
            mitm_risk = True
        except Exception:
            pass  # 缃戠粶灞傚け璐ヤ笉绠?MITM (娲绘€ф帰娴嬪凡閫氳繃)

        # 3b) cloudflare trace: warp=on = 濂楀３ WARP 鑺傜偣 (闈炵湡瀹炲嚭鍙? 闄嶆潈鏍囪) 鈥?4s 绐勮秴鏃?
        is_warp = False
        try:
            r = PROBE_SESSION.get(TRACE_URL, proxies=proxies, timeout=PROBE_RETRY_TIMEOUT, verify=True)
            if r.status_code == 200:
                if re.search(r"^warp=on", r.text, re.M):
                    is_warp = True
        except Exception:
            pass

        # --- 4) 鏂祦妫€娴? 闄愭椂涓嬭浇娴嬮€?(chunked 璇?+ 绌洪棽璁℃椂; 澶氱鐐瑰厹搴曢槻娴嬮€熺珯琚睆钄? ---
        # 鏂祦绛惧悕: 杩炴帴寤虹珛涓旈鍖呮甯? 浣嗕腑閫斿仠姝㈤€佹暟鎹?鈫?绌洪棽瓒呮椂寮烘柇
        speed_bps = 0
        for speed_url in SPEED_TEST_URLS:
            downloaded = 0
            t_speed = time.time()
            last_chunk_time = time.time()
            try:
                with PROBE_SESSION.get(speed_url, proxies=proxies,
                                       timeout=(5, SPEED_TEST_BUDGET), stream=True) as r:
                    if r.status_code == 200:
                        for chunk in r.iter_content(chunk_size=65536):
                            now = time.time()
                            if chunk:
                                downloaded += len(chunk)
                                last_chunk_time = now
                            # 鎬婚绠楄秴闄?鈫?姝ｅ父鎴柇 (鎷垮凡鏈夋暟鎹畻鍚炲悙)
                            if now - t_speed > SPEED_TEST_BUDGET:
                                break
                            # 绌洪棽 > 3s 鏃犱换浣曟暟鎹?鈫?鏂祦绛惧悕, 绔嬪嵆涓
                            if now - last_chunk_time > 3.0:
                                break
                elapsed = max(time.time() - t_speed, 0.001)
                if downloaded > 0:
                    speed_bps = int(downloaded / elapsed)
                    break  # 棣栦釜鎴愬姛绔偣鐨勭粨鏋滃嵆鏈夋晥
            except Exception:
                continue
        # 鍏ㄩ儴绔偣閮藉け璐?(涓嬭浇0瀛楄妭) 鈫?瑙嗕负鏂祦 (娲绘€у凡杩囦絾鏃犳硶鎵胯浇鏁版嵁娴?

        # 鏂祦鍒ゅ畾: 杩?70KB/s 閮借揪涓嶅埌 鈫?鏂祦/鏋佹參, 鐪熷疄涓嶅彲鐢?
        is_stalled = speed_bps < SPEED_MIN_BYTES_PER_S

        result = {
            "raw": raw,
            "server": server,
            "port": port,
            "proto": proto,
            "alive": True,
            "latency_ms": int(latency_ms),
            "exit_ip": exit_ip,
            "exit_country_online": exit_country,
            "exit_asn_online": exit_asn,
            "exit_asn_org_online": (exit_asn_org or "")[:120],
            "exit_isp_online": (exit_isp or "")[:120],
            "mitm_risk": mitm_risk,
            "is_warp": is_warp,
            "speed_bps": speed_bps,
            "is_stalled": is_stalled,
        }
        return result
    except Exception:
        return None
    finally:
        if proc and proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=3)
            except Exception:
                pass
        try:
            if os.path.exists(cfg_path):
                os.remove(cfg_path)
        except OSError:
            pass


def run_liveness_test(candidates: list) -> list:
    print(f"[*] sing-box 鍏ㄥ崗璁湡瀹炴祴娲? {len(candidates)} 鑺傜偣 (骞跺彂 {MAX_WORKERS_TEST}) ...")
    results = []
    done_count = [0]

    def _work(item):
        return test_single_node(item)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS_TEST) as ex:
        futs = {ex.submit(_work, it): it for it in candidates}
        for fut in as_completed(futs):
            done_count[0] += 1
            r = fut.result()
            if r:
                results.append(r)
            if done_count[0] % 40 == 0:
                print(f"[*] 娴嬫椿杩涘害: {done_count[0]}/{len(candidates)}, 閫氳繃 {len(results)}")

    alive = [r for r in results if r["alive"] and not r["is_stalled"]]
    mitm = sum(1 for r in results if r["mitm_risk"])
    stalled = sum(1 for r in results if r["is_stalled"])
    print(f"[+] 娴嬫椿瀹屾垚: 鐪熸椿 {len(alive)} | 鏂祦娣樻卑 {stalled} | MITM 椋庨櫓 {mitm}")
    return results  # 淇濈暀鍏ㄩ儴淇℃伅, 鍒嗙被闃舵鍐嶅喅瀹氬幓鐣?


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# 闃舵 B2: 瀹跺閾惧紡澶嶆祴 (chain relay retest)
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲

def chain_retest(test_results: list) -> list:
    """瀹跺閾惧紡澶嶆祴: 妯℃嫙鐢ㄦ埛 v2rayN 閾惧紡 (鍓嶇疆 鈫?瀹跺鑺傜偣 鈫?鐩爣)

    瀹炴祴鑳屾櫙: 鐢ㄦ埛鍙嶉瀹跺鑺傜偣鍦?v2rayN 閾惧紡浠ｇ悊涓嬩粎 ~50% 鍙敤銆?
    鏍瑰洜: 鍗曡烦娴嬫椿閫氳繃 鈮?鍙岃烦鍙敤 (閮ㄥ垎鑺傜偣涓嶅厑璁?宸茶浠ｇ悊鐨勬祦閲?鍐嶅叆,
    鎴?UDP/QUIC 鑺傜偣鏃犳硶杩?socks 閾?銆傝В鍐? CI 閲岀敤鏈€蹇瓨娲昏妭鐐瑰綋鍓嶇疆,
    瀵瑰瀹藉€欓€夊仛鍙岃烦澶嶆祴 鈥?鍙岃烦閫氳繃鐨勬墠杩涘瀹戒笓鍖恒€?

    娴佺▼: 鍏堣窇涓€閬嶈交閲忓垎绫绘嬁鍒板瀹藉€欓€?鈫?鍙栨渶蹇瓨娲昏妭鐐瑰仛 relay 鈫?
    瀹跺鍊欓€夐€愪釜鍙岃烦澶嶆祴 鈫?鍙岃烦涔熸椿鐨勪繚鐣? 鍙岃烦姝荤殑闄嶇骇鏅€氬尯銆?
    杩斿洖: 鏇存柊 net_type 鍚庣殑 test_results (鍘熷璞″師鍦颁慨鏀?銆?
    """
    # 1) 杞婚噺鍒嗙被鎷垮瀹藉€欓€?(澶嶇敤 classify_and_export 鐨勫€欓€夊垽瀹? 浣嗕笉瀵煎嚭)
    #    瀹跺鍊欓€?= ip-api/mmdb 鍏俊鍙峰垽 residential/mobile 鐨勮妭鐐?
    ip_api_info = {}
    all_exit_ips = list({r["exit_ip"] for r in test_results if r.get("exit_ip")})
    if all_exit_ips:
        try:
            ip_api_info = ip_api_batch_lookup(all_exit_ips)
        except Exception as e:
            print(f"[!] 閾惧紡澶嶆祴: ip-api 鎵归噺澶辫触 ({e}), 璺宠繃閾惧紡澶嶆祴")
            return test_results

    res_candidates = {}
    for r in test_results:
        if not (r.get("alive") and not r.get("is_stalled")):
            continue
        rec = ip_api_info.get(r.get("exit_ip"), {})
        t, c = classify_network_type(r["exit_ip"], r.get("exit_country_online"),
                                     r.get("exit_asn_online"),
                                     r.get("exit_asn_org_online"), rec or None)
        if t in ("residential", "mobile") and c >= 60:
            res_candidates[(r["server"].lower(), r["port"], r["proto"])] = r

    if not res_candidates:
        print("[*] 閾惧紡澶嶆祴: 鏃犲瀹藉€欓€? 璺宠繃")
        return test_results
    print(f"[*] 閾惧紡澶嶆祴: {len(res_candidates)} 涓瀹藉€欓€?)

    # 2) 閫?relay: 鍏ㄤ綋瀛樻椿鑺傜偣閲屽欢杩熸渶浣庛€侀潪瀹跺鍊欓€夎嚜宸?(閬垮厤鑷繁濂楄嚜宸?
    alive_sorted = sorted(
        [r for r in test_results if r.get("alive") and not r.get("is_stalled")],
        key=lambda x: x.get("latency_ms", 99999))
    relay_result = None
    for r in alive_sorted:
        if (r["server"].lower(), r["port"], r["proto"]) not in res_candidates:
            relay_result = r
            break
    if not relay_result:
        print("[!] 閾惧紡澶嶆祴: 鏃犲彲鐢?relay 鑺傜偣, 璺宠繃")
        return test_results
    relay_out = relay_result.get("outbound")
    if not relay_out:
        # 閲嶆柊瑙ｆ瀽 relay 鐨?raw 鎷?outbound
        p = parse_node_uri(relay_result["raw"])
        if p:
            relay_out = p[0]
    if not relay_out:
        print("[!] 閾惧紡澶嶆祴: relay outbound 鏋勫缓澶辫触, 璺宠繃")
        return test_results
    # relay 蹇呴』鍓ョ detour (鍓嶇疆閾惧鐢ㄦ椂闃插惊鐜?
    relay_out = dict(relay_out)
    relay_out.pop("detour", None)
    print(f"[*] 閾惧紡 relay: {relay_result['proto']} {relay_result['server']}:{relay_result['port']} "
          f"(寤惰繜 {relay_result['latency_ms']}ms)")

    # 3) 瀹跺鍊欓€夐€愪釜鍙岃烦澶嶆祴 (娉ㄥ叆 CHAIN_RELAY_OUT, test_single_node 鑷姩鍔?detour)
    os.environ["CHAIN_RELAY_OUT"] = json.dumps(relay_out)
    chain_alive, chain_dead = [], []
    try:
        for key, r in res_candidates.items():
            item = (r["raw"], r.get("outbound") or (parse_node_uri(r["raw"]) or [None])[0],
                    r["server"], r["port"], r["proto"])
            if not item[1]:
                chain_dead.append(r)
                continue
            recheck = test_single_node(item)
            if recheck and recheck.get("alive") and not recheck.get("is_stalled"):
                chain_alive.append(r)
            else:
                chain_dead.append(r)
    finally:
        os.environ.pop("CHAIN_RELAY_OUT", None)

    # 4) 鍙岃烦澶辫触鐨?鈫?闄嶇骇鏅€氬尯 (涓嶄粠璁㈤槄鍒犻櫎, 鐢ㄦ埛鐩磋繛鍦烘櫙浠嶅彲鑳藉彲鐢?
    for r in chain_dead:
        r["_chain_failed"] = True

    print(f"[+] 閾惧紡澶嶆祴瀹屾垚: 鍙岃烦鍙敤 {len(chain_alive)} | 鍙岃烦澶辫触闄嶇骇 {len(chain_dead)}")
    return test_results


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# 闃舵 C: 鍑哄彛 IP 鎵归噺鎯呮姤 (ip-api.com 鍏嶈垂 batch) + 绂荤嚎鍏滃簳
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

def ip_api_batch_lookup(ip_list: list) -> dict:
    """ip-api.com batch (鍏嶈垂 HTTP, 鈮?00/req, 15 req/min 鈫?1500 IP/min)"""
    info = {}
    session = requests.Session()
    session.trust_env = True  # 鐩磋繛鍗冲彲; ip-api.com 鍏嶈垂灞傚叏鐞冨彲杈?(CI 鏃犱唬鐞?鏈湴璧扮郴缁熶唬鐞嗗潎鍙?
    total_batches = (len(ip_list) + IP_API_BATCH_SIZE - 1) // IP_API_BATCH_SIZE
    for bi, i in enumerate(range(0, len(ip_list), IP_API_BATCH_SIZE), 1):
        chunk = ip_list[i:i + IP_API_BATCH_SIZE]
        payload = [{"query": ip} for ip in chunk]
        for attempt in range(3):
            try:
                r = session.post(IP_API_BATCH_URL, json=payload, timeout=20)
                if r.status_code == 200:
                    for rec in r.json():
                        q = rec.get("query")
                        if q:
                            info[q] = rec
                    break
                elif r.status_code == 429:
                    time.sleep(4 + attempt * 3)
                else:
                    time.sleep(2)
            except Exception:
                time.sleep(2)
        if total_batches >= 3 and (bi % 5 == 0 or bi == total_batches):
            print(f"[*] ip-api 杩涘害: 鎵?{bi}/{total_batches} ({len(info)} IP 宸叉煡)")
        time.sleep(IP_API_BATCH_RPS_INTERVAL)
    return info


def offline_ip_lookup(ip: str, country_reader, asn_reader) -> tuple:
    """GeoLite2 绂荤嚎鏌ヨ 鈫?(country, asn, org)"""
    country, asn, org = None, None, None
    try:
        c = country_reader.get(ip)
        if c and c.get("country", {}).get("iso_code"):
            country = c["country"]["iso_code"]
    except Exception:
        pass
    try:
        a = asn_reader.get(ip)
        if a:
            asn = a.get("autonomous_system_number")
            org = a.get("autonomous_system_organization", "")
    except Exception:
        pass
    return country, asn, org


def get_rdns(ip: str) -> str:
    old = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(2.0)
        host, _, _ = socket.gethostbyaddr(ip)
        return host.lower()
    except Exception:
        return ""
    finally:
        socket.setdefaulttimeout(old)


def classify_network_type(ip: str, country: str, asn, org: str, ip_api_rec: dict = None) -> tuple:
    """
    杩斿洖 (net_type, confidence):
      net_type 鈭?{datacenter, residential, mobile, cdn, unknown}
    浼樺厛绾? ip-api.com hosting/mobile 瀛楁 > CDN 缃戞 > ASN 鐧?榛戝悕鍗?> 鍚嶇О鍏抽敭璇?
    """
    ip_str = str(ip)
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return "unknown", 0

    # 1) CDN / Anycast 缃戞 (纭垽鎹?
    for net in CLOUDFLARE_IP_NETWORKS:
        if ip_obj in net:
            return "cdn", 100
    for net in CDN_IP_NETWORKS_EXTRA:
        if ip_obj in net:
            return "cdn", 95

    asn_int = None
    if isinstance(asn, int):
        asn_int = asn
    elif isinstance(asn, str) and asn:
        m = re.match(r"AS(\d+)", asn)
        if m:
            asn_int = int(m.group(1))

    org_lower = (org or "").lower()
    hosting_flag = False
    mobile_flag = False
    proxy_flag = False

    # 2) ip-api.com 鍦ㄧ嚎瀛楁 (鏈€楂樺彲淇?
    if ip_api_rec:
        hosting_flag = bool(ip_api_rec.get("hosting"))
        mobile_flag = bool(ip_api_rec.get("mobile"))
        proxy_flag = bool(ip_api_rec.get("proxy"))
        rec_asn = ip_api_rec.get("as") or ""
        m = re.match(r"AS(\d+)", str(rec_asn))
        if m and asn_int is None:
            asn_int = int(m.group(1))
        org_lower = (ip_api_rec.get("asname") or ip_api_rec.get("org") or org_lower).lower()

    if hosting_flag:
        return "datacenter", 90
    # 鈽?proxy/VPN/Tor 鍑哄彛鏍囧織 (ip-api) 鈥?纭惁鍐冲瀹?姘戠敤
    # 瀹炴祴 AS62610 Zenlayer (鏀惰喘 speakeasy DSL legacy 娈?: hosting=false 浣?proxy=true
    # 姝ょ被"鏈烘埧鏀惰喘瀹跺娈?鏄亣瀹跺涓昏褰㈡€? rDNS 甯?dsl/pppoe 涔熶笉鑳戒俊
    if proxy_flag:
        return "datacenter", 88
    if mobile_flag:
        return "mobile", 85

    # 3) ASN 鐧?榛戝悕鍗?
    if asn_int:
        if asn_int in DATACENTER_ASNS:
            return "datacenter", 80
        if asn_int in RESIDENTIAL_ASNS:
            return "residential", 82

    # 4) ISP 鍚嶇О鍏抽敭璇?
    if org_lower:
        for kw in IDC_NAME_PATTERNS:
            if kw in org_lower:
                return "datacenter", 70
        for kw in RESIDENTIAL_NAME_PATTERNS:
            if kw in org_lower:
                return "residential", 70

    # 5) rDNS 鍏滃簳
    rdns = get_rdns(ip_str)
    if rdns:
        for kw in IDC_NAME_PATTERNS:
            if kw in rdns:
                return "datacenter", 60
        for kw in RESIDENTIAL_NAME_PATTERNS:
            if kw in rdns:
                return "residential", 60

    return "unknown", 30


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# 鑺傜偣 鈫?鍚勫鎴风閰嶇疆杞崲
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

def outbound_to_clash(node: dict, name: str) -> dict:
    """sing-box outbound 鈫?Clash (Meta/mihomo) proxy dict"""
    t = node.get("type")
    server, port = node["server"], node["server_port"]
    proxy = {"name": name, "server": server, "port": port, "udp": True}

    if t == "vless":
        proxy["type"] = "vless"
        proxy["uuid"] = node["uuid"]
        if node.get("flow"):
            proxy["flow"] = node["flow"]
        tls = node.get("tls") or {}
        if tls.get("reality"):
            proxy["tls"] = True
            proxy["reality-opts"] = {"public-key": tls["reality"]["public_key"]}
            if tls["reality"].get("short_id"):
                proxy["reality-opts"]["short-id"] = tls["reality"]["short_id"]
            proxy["servername"] = tls.get("server_name") or server
            if tls.get("utls"):
                proxy["client-fingerprint"] = tls["utls"].get("fingerprint", "chrome")
        elif tls.get("enabled"):
            proxy["tls"] = True
            proxy["servername"] = tls.get("server_name") or server
            proxy["skip-cert-verify"] = bool(tls.get("insecure"))
            if tls.get("utls"):
                proxy["client-fingerprint"] = tls["utls"].get("fingerprint", "chrome")
        transport = node.get("transport") or {}
        if transport.get("type"):
            proxy["network"] = transport["type"]
            if transport["type"] == "ws":
                proxy["ws-opts"] = {"path": transport.get("path", "/")}
                if transport.get("headers"):
                    proxy["ws-opts"]["headers"] = transport["headers"]
            elif transport["type"] == "grpc":
                proxy["grpc-opts"] = {"grpc-service-name": transport.get("service_name", "")}
            elif transport["type"] == "http":
                proxy["network"] = "h2"
                proxy["h2-opts"] = {"host": transport.get("host", []),
                                    "path": transport.get("path", "/")}
            elif transport["type"] == "httpupgrade":
                proxy["network"] = "httpupgrade"
                proxy["httpupgrade-opts"] = {"path": transport.get("path", "/"),
                                              "headers": {"Host": transport.get("host", "")}}
    elif t == "vmess":
        proxy["type"] = "vmess"
        proxy["uuid"] = node["uuid"]
        proxy["alterId"] = node.get("alter_id", 0)
        proxy["cipher"] = "auto"
        tls = node.get("tls") or {}
        if tls.get("enabled"):
            proxy["tls"] = True
            proxy["servername"] = tls.get("server_name") or server
            proxy["skip-cert-verify"] = bool(tls.get("insecure"))
        transport = node.get("transport") or {}
        if transport.get("type"):
            proxy["network"] = transport["type"]
            if transport["type"] == "ws":
                proxy["ws-opts"] = {"path": transport.get("path", "/")}
                if transport.get("headers"):
                    proxy["ws-opts"]["headers"] = transport["headers"]
            elif transport["type"] == "grpc":
                proxy["grpc-opts"] = {"grpc-service-name": transport.get("service_name", "")}
            elif transport["type"] == "http":
                proxy["network"] = "h2"
                proxy["h2-opts"] = {"host": transport.get("host", []),
                                    "path": transport.get("path", "/")}
    elif t == "trojan":
        proxy["type"] = "trojan"
        proxy["password"] = node["password"]
        tls = node.get("tls") or {}
        proxy["sni"] = tls.get("server_name") or server
        proxy["skip-cert-verify"] = bool(tls.get("insecure"))
        transport = node.get("transport") or {}
        if transport.get("type"):
            proxy["network"] = transport["type"]
            if transport["type"] == "ws":
                proxy["ws-opts"] = {"path": transport.get("path", "/")}
            elif transport["type"] == "grpc":
                proxy["grpc-opts"] = {"grpc-service-name": transport.get("service_name", "")}
    elif t == "shadowsocks":
        proxy["type"] = "ss"
        proxy["cipher"] = node["method"]
        proxy["password"] = node["password"]
    elif t == "hysteria2":
        proxy["type"] = "hysteria2"
        proxy["password"] = node["password"]
        tls = node.get("tls") or {}
        proxy["sni"] = tls.get("server_name") or server
        proxy["skip-cert-verify"] = bool(tls.get("insecure"))
        if node.get("obfs"):
            proxy["obfs"] = node["obfs"].get("type")
            proxy["obfs-password"] = node["obfs"].get("password", "")
        if node.get("server_ports"):
            proxy["ports"] = ",".join(p.replace(":", "-") for p in node["server_ports"])
    elif t == "tuic":
        proxy["type"] = "tuic"
        proxy["uuid"] = node["uuid"]
        proxy["password"] = node["password"]
        tls = node.get("tls") or {}
        proxy["sni"] = tls.get("server_name") or server
        proxy["skip-cert-verify"] = bool(tls.get("insecure"))
        proxy["congestion-controller"] = node.get("congestion_control", "bbr")
        proxy["udp-relay-mode"] = node.get("udp_relay_mode", "native")
        if tls.get("alpn"):
            proxy["alpn"] = tls["alpn"]
    elif t == "anytls":
        proxy["type"] = "anytls"
        proxy["password"] = node["password"]
        tls = node.get("tls") or {}
        proxy["sni"] = tls.get("server_name") or server
        proxy["skip-cert-verify"] = bool(tls.get("insecure"))
    else:
        return None
    return proxy


def outbound_to_v2ray_link(node: dict, name: str) -> str:
    """sing-box outbound 鈫?v2rayN 鍏煎 URI"""
    t = node.get("type")
    # 绔彛璺宠穬鑺傜偣 (hy2 mport): 鏃?server_port 鏃跺彇 server_ports 棣栧尯闂磋捣濮嬬鍙?
    if "server_port" in node:
        port = node["server_port"]
    elif node.get("server_ports"):
        port = int(str(node["server_ports"][0]).split(":")[0])
    else:
        return ""
    server = node["server"]
    tls = node.get("tls") or {}
    transport = node.get("transport") or {}

    if t == "vmess":
        ttype = transport.get("type", "tcp")
        data = {
            "v": "2", "ps": name, "add": server, "port": str(port),
            "id": node["uuid"], "aid": str(node.get("alter_id", 0)),
            "scy": "auto", "net": ttype,
            "type": "none",
            "host": "", "path": "",
            "tls": "tls" if tls.get("enabled") else "",
            "sni": tls.get("server_name", ""),
        }
        if ttype == "ws":
            if transport.get("path"):
                data["path"] = transport["path"]
            if (transport.get("headers") or {}).get("Host"):
                data["host"] = transport["headers"]["Host"]
            if transport.get("max_early_data"):
                data["path"] = (data["path"] or "") + f"?ed={transport['max_early_data']}"
        elif ttype == "grpc":
            if transport.get("service_name"):
                data["path"] = transport["service_name"]
        elif ttype == "http":
            if transport.get("path"):
                data["path"] = transport["path"]
            if transport.get("host"):
                data["host"] = ",".join(transport["host"])
        elif ttype == "httpupgrade":
            if transport.get("path"):
                data["path"] = transport["path"]
            if transport.get("host"):
                data["host"] = transport["host"]
        return "vmess://" + base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode()
    if t == "vless":
        q = {}
        ttype = transport.get("type")
        if ttype:
            q["type"] = ttype
            if ttype == "ws":
                if transport.get("path"):
                    q["path"] = transport["path"]
                if (transport.get("headers") or {}).get("Host"):
                    q["host"] = transport["headers"]["Host"]
                if transport.get("max_early_data"):
                    q["ed"] = str(transport["max_early_data"])
            elif ttype == "grpc":
                if transport.get("service_name"):
                    q["serviceName"] = transport["service_name"]
            elif ttype == "http":
                if transport.get("host"):
                    q["host"] = ",".join(transport["host"])
                if transport.get("path"):
                    q["path"] = transport["path"]
            elif ttype == "httpupgrade":
                if transport.get("path"):
                    q["path"] = transport["path"]
                if transport.get("host"):
                    q["host"] = transport["host"]
        if tls.get("reality"):
            q["security"] = "reality"
            q["pbk"] = tls["reality"]["public_key"]
            q["sid"] = tls["reality"].get("short_id", "")
            q["fp"] = (tls.get("utls") or {}).get("fingerprint", "chrome")
            if tls.get("server_name"):
                q["sni"] = tls["server_name"]
        elif tls.get("enabled"):
            q["security"] = "tls"
            if tls.get("server_name"):
                q["sni"] = tls["server_name"]
            if tls.get("alpn"):
                q["alpn"] = ",".join(tls["alpn"])
            if tls.get("utls"):
                q["fp"] = tls["utls"].get("fingerprint", "chrome")
            if tls.get("insecure"):
                q["allowInsecure"] = "1"
        if node.get("flow"):
            q["flow"] = node["flow"]
        query = urllib.parse.urlencode(q)
        return f"vless://{node['uuid']}@{server}:{port}?{query}#{urllib.parse.quote(name)}"
    if t == "trojan":
        q = {"security": "tls"}
        if tls.get("server_name"):
            q["sni"] = tls["server_name"]
        if tls.get("alpn"):
            q["alpn"] = ",".join(tls["alpn"])
        if (tls.get("utls") or {}).get("fingerprint"):
            q["fp"] = tls["utls"]["fingerprint"]
        if tls.get("insecure"):
            q["allowInsecure"] = "1"
        ttype = transport.get("type")
        if ttype:
            q["type"] = ttype
            if ttype == "ws":
                if transport.get("path"):
                    q["path"] = transport["path"]
                if (transport.get("headers") or {}).get("Host"):
                    q["host"] = transport["headers"]["Host"]
                if transport.get("max_early_data"):
                    q["ed"] = str(transport["max_early_data"])
            elif ttype == "grpc":
                if transport.get("service_name"):
                    q["serviceName"] = transport["service_name"]
            elif ttype == "httpupgrade":
                if transport.get("path"):
                    q["path"] = transport["path"]
                if transport.get("host"):
                    q["host"] = transport["host"]
        query = urllib.parse.urlencode(q)
        return f"trojan://{urllib.parse.quote(node['password'])}@{server}:{port}?{query}#{urllib.parse.quote(name)}"
    if t == "shadowsocks":
        # SIP002: userinfo = urlsafe-base64(method:password), 鈽?蹇呴』淇濈暀 padding ("=")
        # 瀹炴祴: rstrip("=") 鐮?padding 鍚?v2rayN 瑙ｆ瀽澶辫触 (鏃?padding 鐨勭暩褰?base64)
        # urlsafe 瀛楁瘝琛?(A-Za-z0-9-_) + "=" 鍧囦负 URI 鍚堟硶瀛楃, 涓嶉渶鍐?quote (quote 鍙嶈€岀牬鍧?"=")
        userinfo = base64.urlsafe_b64encode(
            f"{node['method']}:{node['password']}".encode()).decode()
        return f"ss://{userinfo}@{server}:{port}#{urllib.parse.quote(name)}"
    if t == "hysteria2":
        q = {}
        if tls.get("server_name"):
            q["sni"] = tls["server_name"]
        if tls.get("insecure"):
            q["insecure"] = "1"
        if node.get("obfs"):
            q["obfs"] = node["obfs"].get("type", "salamander")
            q["obfs-password"] = node["obfs"].get("password", "")
        if node.get("server_ports"):
            q["mport"] = ",".join(p.replace(":", "-") for p in node["server_ports"])
        query = urllib.parse.urlencode(q)
        return f"hysteria2://{urllib.parse.quote(node['password'])}@{server}:{port}?{query}#{urllib.parse.quote(name)}"
    if t == "tuic":
        q = {
            "congestion_control": node.get("congestion_control", "bbr"),
            "udp_relay_mode": node.get("udp_relay_mode", "native"),
            "alpn": ",".join((tls.get("alpn") or ["h3"])),
        }
        if tls.get("server_name"):
            q["sni"] = tls["server_name"]
        if tls.get("insecure"):
            q["allow_insecure"] = "1"
        query = urllib.parse.urlencode(q)
        return f"tuic://{urllib.parse.quote(node['uuid'])}:{urllib.parse.quote(node['password'])}@{server}:{port}?{query}#{urllib.parse.quote(name)}"
    if t == "anytls":
        q = {}
        if tls.get("server_name"):
            q["sni"] = tls["server_name"]
        if tls.get("insecure"):
            q["insecure"] = "1"
        query = urllib.parse.urlencode(q)
        return f"anytls://{urllib.parse.quote(node['password'])}@{server}:{port}?{query}#{urllib.parse.quote(name)}"
    return ""


def outbound_to_singbox(node: dict, name: str) -> dict:
    n = dict(node)
    n["tag"] = name
    return n


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# 鍒嗙被 + 瀵煎嚭
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

def scamalytics_fraud_score(ip: str) -> int:
    """Scamalytics 鍏嶈垂椋庢帶璇勫垎 (HTML 鎶撳彇, subs-check 鍚屾鏂规)
    杩斿洖 0-100: 瓒婇珮瓒婂嵄闄? 澶辫触杩斿洖 -1 (涓嶅弬涓庡垽瀹?"""
    try:
        r = DIRECT_SESSION.get(f"https://scamalytics.com/ip/{ip}", timeout=10)
        if r.status_code != 200:
            return -1
        m = re.search(r"Fraud Score:\s*(\d+)", r.text)
        return int(m.group(1)) if m else -1
    except Exception:
        return -1


def ipapi_is_verify(ip: str) -> dict:
    """ipapi.is 鍏嶈垂浜ゅ弶婧?(1000 req/澶? 鏃?key)
    瀹炴祴瀵?AS62610 Zenlayer (鏀惰喘 speakeasy DSL 娈典吉瑁呭瀹? 鑳界粰鍑?
    company=Bunny Communications; 瀵圭湡瀹跺 (SK Broadband) 缁欒繍钀ュ晢鍚嶃€?
    浠呯敤鍏?company/asn 瀛楁鍋氬瀹藉€欓€夌殑浜屾鍚﹀喅銆傚け璐ヨ繑鍥?{}"""
    try:
        r = DIRECT_SESSION.get(f"https://api.ipapi.is/?q={ip}", timeout=10)
        if r.status_code != 200:
            return {}
        j = r.json()
        return {"company": j.get("company") or "", "asn": j.get("asn") or "",
                "country": j.get("country") or ""}
    except Exception:
        return {}


def classify_and_export(test_results: list):
    print("[*] 鍑哄彛 IP 鎯呮姤涓庡垎绫?...")
    # 鏀堕泦鍏ㄩ儴鍑哄彛 IP
    all_exit_ips = []
    seen_ip = set()
    no_exit_ip = []
    for r in test_results:
        if r["exit_ip"] and r["exit_ip"] not in seen_ip:
            seen_ip.add(r["exit_ip"])
            all_exit_ips.append(r["exit_ip"])
    print(f"[*] 寰呮煡璇㈠嚭鍙?IP: {len(all_exit_ips)} 涓?(ip-api.com 鎵归噺 {len(test_results)} 鑺傜偣)")

    ip_api_info = {}
    scam_scores = {}
    if all_exit_ips:
        try:
            est_batches = (len(all_exit_ips) + IP_API_BATCH_SIZE - 1) // IP_API_BATCH_SIZE
            print(f"[*] ip-api 鎵归噺: {est_batches} 鎵?脳 ~4.2s 鈮?{est_batches * 4.2:.0f}s (鍏嶈垂闄?15 req/min, 璇疯€愬績) ...")
            ip_api_info = ip_api_batch_lookup(all_exit_ips)
            print(f"[+] ip-api.com 鎵归噺鎯呮姤: {len(ip_api_info)}/{len(all_exit_ips)}")
        except Exception as e:
            print(f"[!] ip-api 鎵归噺澶辫触, 灏嗗叏閲忚蛋绂荤嚎: {e}")

    country_reader = asn_reader = None
    try:
        country_reader = maxminddb.open_database(os.path.join(RUNTIME_DIR, "Country.mmdb"))
        asn_reader = maxminddb.open_database(os.path.join(RUNTIME_DIR, "ASN.mmdb"))
    except Exception as e:
        print(f"[!] MaxMind 鏁版嵁搴撴墦寮€澶辫触: {e}")

    nodes = []
    for r in test_results:
        exit_ip = r["exit_ip"]
        online_country = r.get("exit_country_online")
        country = online_country
        asn, org = r.get("exit_asn_online"), r.get("exit_asn_org_online")
        if isinstance(asn, int):
            pass
        elif isinstance(asn, str):
            m = re.match(r"AS(\d+)", asn)
            asn = int(m.group(1)) if m else None

        # 鍦ㄧ嚎鎯呮姤缂哄け 鈫?绂荤嚎 mmdb 鍏滃簳
        if country_reader and (not country or not asn):
            off_c, off_asn, off_org = offline_ip_lookup(exit_ip, country_reader, asn_reader)
            country = country or off_c
            asn = asn or off_asn
            org = org or off_org

        # 鈽?鍑哄彛 IP 鏌ヤ笉鍒板浗瀹?(浜戝唴缃?涓浆闅ч亾) 鈫?鍥為€€鐢ㄥ叆鍙ｆ湇鍔″櫒 IP 瀹氫綅鍥藉
        #    (涓浆鑺傜偣鍑哄彛甯告槸鍐呯綉鍦板潃, mmdb 涔熸煡涓嶅埌; 鍏ュ彛鍥?鈮?鍑哄彛鍥戒絾鑷冲皯缁欑敤鎴峰彲鐢ㄥ湴鍖?
        if (not country or country in ("OTHER", "ZZ")) and r.get("server"):
            srv_ip = r["server"] if is_ip_literal(r["server"]) else resolve_host(r["server"])
            if srv_ip and country_reader:
                off_c, srv_asn, srv_org = offline_ip_lookup(srv_ip, country_reader, asn_reader)
                if off_c and off_c not in ("OTHER", "ZZ"):
                    country = off_c
                    asn, org = asn or srv_asn, org or srv_org

        rec = ip_api_info.get(exit_ip, {})
        net_type, confidence = classify_network_type(
            exit_ip, country, asn, org, rec or None)

        # 鏃犵湡瀹炲嚭鍙?IP 鐨勮妭鐐? 鍥藉鏈煡, 涓嶅叆瀹跺鍖?
        if not exit_ip:
            country = country or "OTHER"

        nodes.append({
            "raw": r["raw"],
            "server": r["server"],
            "port": r["port"],
            "proto": r["proto"],
            "outbound": r.get("outbound"),
            "country": (country or "OTHER").upper(),
            "net_type": net_type,
            "confidence": confidence,
            "exit_ip": exit_ip,
            "asn": asn,
            "org": org,
            "isp": r.get("exit_isp_online") or (rec.get("isp") if rec else ""),
            "latency_ms": r["latency_ms"],
            "speed_bps": r["speed_bps"],
            "mitm_risk": r["mitm_risk"],
            "is_stalled": r["is_stalled"],
        })

    if country_reader:
        country_reader.close()
    if asn_reader:
        asn_reader.close()

    # 鈹€鈹€ 椋庨櫓杩囨护 鈹€鈹€
    # MITM 鍔寔鑺傜偣: 楂樺嵄, 鐩存帴涓㈠純 (204 鑳介€氫絾璇佷功琚姭鎸?= 涓棿浜?
    safe_nodes = [n for n in nodes if not n["mitm_risk"]]
    mitm_dropped = len(nodes) - len(safe_nodes)
    # 鏂祦鑺傜偣宸叉棤 (鍦?liveness 闃舵娣樻卑), 浣?double-check
    safe_nodes = [n for n in safe_nodes if not n["is_stalled"]]
    print(f"[*] MITM 鍔寔楂橀闄╄妭鐐瑰凡鍓旈櫎: {mitm_dropped}")

    # 鈹€鈹€ Scamalytics 椋庢帶璇勫垎 (鍏嶈垂 HTML, 閫愪釜; 鍙煡瀹跺鍊欓€?+ 鎶芥牱鏅€氳妭鐐? 鈹€鈹€
    # 瀹跺鍊欓€? 鍏ㄦ煡 (瀹佺己姣嬫互); 鏅€氳妭鐐? 姣?IP 鏌ヤ竴娆?(閫氬父 <= 鍑哄彛 IP 鏁?
    scam_candidates = set()
    for n in safe_nodes:
        if n["net_type"] in ("residential", "mobile") and n["exit_ip"]:
            scam_candidates.add(n["exit_ip"])
    if scam_candidates:
        print(f"[*] Scamalytics 椋庢帶璇勫垎: 鏌ヨ {len(scam_candidates)} 涓瀹藉€欓€夊嚭鍙?IP ...")
        def _scam(ip):
            return ip, scamalytics_fraud_score(ip)
        with ThreadPoolExecutor(max_workers=6) as ex:
            for ip, score in ex.map(_scam, scam_candidates):
                scam_scores[ip] = score
        got = sum(1 for v in scam_scores.values() if v >= 0)
        print(f"[+] Scamalytics 璇勫垎鑾峰緱: {got}/{len(scam_candidates)}")

    # 鈹€鈹€ ipapi.is 浜ゅ弶鏍搁獙 (鍙煡瀹跺鍊欓€? 鍏嶈垂 1000 娆?澶? 鈹€鈹€
    # ip-api 鍒?hosting/proxy 涔熸湁婕?(浼瀹跺: 鏀惰喘 DSL 娈电殑浜戣竟缃戠粶)銆?
    # ipapi.is 鐙珛鏁版嵁婧? company 鍚?IDC 璇?鈫?鍚﹀喅瀹跺
    ipapi_verify = {}
    verify_candidates = set()
    for n in safe_nodes:
        if n["net_type"] in ("residential", "mobile") and n["exit_ip"]:
            verify_candidates.add(n["exit_ip"])
    if verify_candidates:
        print(f"[*] ipapi.is 浜ゅ弶鏍搁獙: {len(verify_candidates)} 涓瀹藉€欓€?...")
        def _verify(ip):
            return ip, ipapi_is_verify(ip)
        with ThreadPoolExecutor(max_workers=4) as ex:
            for ip, info in ex.map(_verify, verify_candidates):
                ipapi_verify[ip] = info
        # 鍚﹀喅: company/asn 鍚満鎴胯瘝
        vetoed = 0
        for n in safe_nodes:
            if n["net_type"] not in ("residential", "mobile"):
                continue
            info = ipapi_verify.get(n["exit_ip"]) or {}
            comp_asn = (info.get("company", "") + " " + info.get("asn", "")).lower()
            if any(kw in comp_asn for kw in (
                "zenlayer", "bunny", "cloudflare", "akamai", "fastly",
                "amazon", "google llc", "microsoft", "digitalocean", "vultr",
                "hetzner", "ovh", "contabo", "leaseweb", "datacamp",
                "serverius", "clouvider", "m247", "gcore", "g-core",
                "choopa", "linode", "alibaba", "tencent", "huawei cloud",
            )):
                n["net_type"] = "datacenter"
                n["confidence"] = 85
                vetoed += 1
        if vetoed:
            print(f"[*] ipapi.is 鍚﹀喅鍋囧瀹? {vetoed} 涓?(浜戝晢鏀惰喘瀹跺娈典吉瑁?")

    # 椋庨櫓鍒?>= 75 鐨勫瀹藉€欓€夐檷绾т负鏅€?(fraud 姹?琚互鐢?IP 缁濅笉鍏ュ瀹藉尯)
    downgraded = 0
    for n in safe_nodes:
        sc = scam_scores.get(n["exit_ip"], -1)
        n["fraud_score"] = sc
        if n["net_type"] in ("residential", "mobile") and sc >= 75:
            n["net_type"] = "datacenter"  # 楂?fraud 鍒? 澶ф鐜囦唬鐞嗘睜婊ョ敤 IP
            n["confidence"] = 60
            downgraded += 1
    if downgraded:
        print(f"[*] 楂?fraud 鍒?(鈮?5) 瀹跺鍊欓€夐檷绾? {downgraded} 涓?)

    # 鈹€鈹€ 鍘婚噸 (鍚屽嚭鍙P+绔彛 鍙暀鏈€蹇? 鈹€鈹€
    best_by_key = {}
    for n in safe_nodes:
        key = f"{n['exit_ip']}:{n['port']}" if n["exit_ip"] else f"{n['server']}:{n['port']}|{n['raw'][:64]}"
        cur = best_by_key.get(key)
        if not cur or n["latency_ms"] < cur["latency_ms"]:
            best_by_key[key] = n
    unique_nodes = list(best_by_key.values())
    dup_dropped = len(safe_nodes) - len(unique_nodes)
    print(f"[*] 鍘婚噸: {len(safe_nodes)} 鈫?{len(unique_nodes)} (鍓旈櫎閲嶅 {dup_dropped})")

    # 鍘婚噸: 鍑哄彛IP+绔彛 鍞竴鍖? 瀹跺鍖轰弗鏍奸槻鍚孖P鍒峰睆
    # 鈽?閾惧紡澶嶆祴 (chain_retest) 鍙岃烦澶辫触鐨勫瀹藉€欓€?鈫?涓嶈繘瀹跺涓撳尯 (闄嶇骇鏅€?
    chain_failed_raws = set()
    for r in test_results:
        if r.get("_chain_failed"):
            chain_failed_raws.add(r.get("raw"))
    residential = []
    res_seen_ip = set()
    for n in unique_nodes:
        if n["net_type"] in ("residential", "mobile") and n["confidence"] >= 60:
            if n.get("raw") in chain_failed_raws:
                n["net_type"] = "datacenter"
                n["confidence"] = 70
                continue
            if n["exit_ip"] and n["exit_ip"] not in res_seen_ip:
                res_seen_ip.add(n["exit_ip"])
                residential.append(n)
    # fraud 鍒嗘瀬楂?(鈮?0) 鐨勮妭鐐规暣浣撳墧闄?(浠讳綍鍖洪兘涓嶈)
    before_total = len(unique_nodes)
    unique_nodes = [n for n in unique_nodes if not (0 <= n.get("fraud_score", -1) >= 90)]
    residential = [n for n in residential if not (0 <= n.get("fraud_score", -1) >= 90)]
    if len(unique_nodes) < before_total:
        print(f"[*] 鏋侀珮鍗辫妭鐐?(fraud鈮?0) 鍓旈櫎: {before_total - len(unique_nodes)} 涓?)

    non_residential = [n for n in unique_nodes if n not in residential]
    print(f"[*] 瀹跺/绉诲姩缃戠粶鑺傜偣: {len(residential)} | 鏅€?鏈烘埧/CDN): {len(non_residential)}")

    # 鎺掑簭: 瀹跺鍦ㄥ墠, 寤惰繜鍗囧簭
    unique_nodes.sort(key=lambda x: (0 if x in residential else 1, x["latency_ms"]))
    residential.sort(key=lambda x: x["latency_ms"])
    non_residential.sort(key=lambda x: x["latency_ms"])
    # 鈽?閾惧紡澶嶆祴鍙岃烦澶辫触鐨勫瀹?鈫?闄嶇骇鏅€氬尯 (v2rayN 閾惧紡鍦烘櫙涓嶅彲闈?
    #    淇濈暀鍦ㄦ€昏闃?鍥藉璁㈤槄閲?(鐩磋繛鍦烘櫙浠嶅彲鐢?, 鍙槸閫€鍑哄瀹戒笓鍖?

    # 閲嶅缓 outbound (娴嬫椿闃舵鐨?outbound 宸查獙璇佸彲鐢?; 鍓ョ娴嬭瘯涓撶敤瀛楁 (detour 绛夌粷涓嶅叆璁㈤槄)
    for n in unique_nodes:
        parsed = parse_node_uri(n["raw"])
        if parsed:
            ob = parsed[0]
            ob.pop("detour", None)
            n["outbound"] = ob
        else:
            n["outbound"] = None

    return unique_nodes, residential, non_residential


def make_node_name(item, idx, force_residential=False):
    cc = item["country"]
    flag = get_country_flag(cc)
    cname = COUNTRY_NAMES.get(cc, cc)
    is_res = item["net_type"] in ("residential", "mobile") and (item["confidence"] >= 60 or force_residential)
    tag = ""
    if is_res:
        tag = " (瀹跺)" if item["net_type"] == "residential" else " (绉诲姩瀹跺)"
    # Scamalytics 椋庢帶鍒? 楂橀闄╄妭鐐瑰悕鍐呮爣娉?(R鍒嗘暟), 浣庡嵄涓嶆爣 (淇濇寔绠€娲?
    fraud = item.get("fraud_score", -1)
    risk_tag = f" R{fraud}" if 0 <= fraud < 75 and fraud >= 40 else (" 鈿燫" if fraud >= 75 else "")
    return f"{flag} {cname} {idx:02d}{tag}{risk_tag} - xiaohe"


def export_all(unique_nodes, residential, non_residential):
    ensure_directories()

    def build_group(nodes_list, force_res=False):
        links, proxies, sb_nodes = [], [], []
        for idx, item in enumerate(nodes_list, start=1):
            name = make_node_name(item, idx, force_res)
            ob = item["outbound"]
            if not ob:
                continue
            links.append(outbound_to_v2ray_link(ob, name))
            cp = outbound_to_clash(ob, name)
            if cp:
                proxies.append(cp)
            sb_nodes.append(outbound_to_singbox(ob, name))
        return links, proxies, sb_nodes

    # 1) 鍏ㄩ噺
    all_links, all_proxies, all_sb = build_group(unique_nodes)
    with open(os.path.join(OUTPUT_DIR, "v2ray.txt"), "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(all_links).encode()).decode())
    export_clash_yaml(all_proxies, os.path.join(OUTPUT_DIR, "clash.yaml"))
    export_singbox_json(all_sb, os.path.join(OUTPUT_DIR, "singbox.json"))

    # 2) 瀹跺鎬昏闃?
    res_links, res_proxies, res_sb = build_group(residential, force_res=True)
    with open(os.path.join(OUTPUT_DIR, "residential.txt"), "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(res_links).encode()).decode())
    if res_proxies:
        export_clash_yaml(res_proxies, os.path.join(OUTPUT_DIR, "residential-clash.yaml"))
        export_singbox_json(res_sb, os.path.join(OUTPUT_DIR, "residential-singbox.json"))
    else:
        for fn in ("residential-clash.yaml", "residential-singbox.json"):
            p = os.path.join(OUTPUT_DIR, fn)
            if os.path.exists(p):
                os.remove(p)

    # 3) 鎸夊浗瀹?- 鏅€氬尯
    shutil.rmtree(COUNTRY_DIR, ignore_errors=True)
    os.makedirs(COUNTRY_DIR, exist_ok=True)
    by_cc = {}
    for n in non_residential:
        by_cc.setdefault(n["country"], []).append(n)
    for cc, lst in by_cc.items():
        l, p, s = build_group(lst)
        with open(os.path.join(COUNTRY_DIR, f"{cc}.txt"), "w", encoding="utf-8") as f:
            f.write(base64.b64encode("\n".join(l).encode()).decode())
        export_clash_yaml(p, os.path.join(COUNTRY_DIR, f"clash-{cc}.yaml"))
        export_singbox_json(s, os.path.join(COUNTRY_DIR, f"singbox-{cc}.json"))

    # 4) 鎸夊浗瀹?- 瀹跺鍖?
    shutil.rmtree(RESIDENTIAL_COUNTRY_DIR, ignore_errors=True)
    os.makedirs(RESIDENTIAL_COUNTRY_DIR, exist_ok=True)
    res_by_cc = {}
    for n in residential:
        res_by_cc.setdefault(n["country"], []).append(n)
    for cc, lst in res_by_cc.items():
        l, p, s = build_group(lst, force_res=True)
        with open(os.path.join(RESIDENTIAL_COUNTRY_DIR, f"{cc}.txt"), "w", encoding="utf-8") as f:
            f.write(base64.b64encode("\n".join(l).encode()).decode())
        export_clash_yaml(p, os.path.join(RESIDENTIAL_COUNTRY_DIR, f"clash-{cc}.yaml"))
        export_singbox_json(s, os.path.join(RESIDENTIAL_COUNTRY_DIR, f"singbox-{cc}.json"))

    print(f"[*] 瀵煎嚭瀹屾瘯: 鍏ㄩ噺 {len(all_links)} | 瀹跺 {len(res_links)}")
    return len(all_links), len(res_links)


def export_clash_yaml(clash_proxies, filepath):
    names = [p["name"] for p in clash_proxies]
    config = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "proxies": clash_proxies,
        "proxy-groups": [
            {"name": "PROXIES", "type": "select", "proxies": ["AUTO"] + names},
            {"name": "AUTO", "type": "url-test", "url": "https://www.gstatic.com/generate_204",
             "interval": 300, "proxies": names},
        ],
        "rules": ["MATCH,PROXIES"],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def export_singbox_json(sb_nodes, filepath):
    names = [n["tag"] for n in sb_nodes]
    outbounds = sb_nodes + [
        {"type": "selector", "tag": "select", "outbounds": ["auto"] + names},
        {"type": "urltest", "tag": "auto", "outbounds": names,
         "url": "https://www.gstatic.com/generate_204"},
        {"type": "direct", "tag": "direct"},
        {"type": "block", "tag": "block"},
    ]
    config = {"log": {"level": "warn"},
              "outbounds": outbounds}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# README 鐢熸垚
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

def update_readme(total_count, res_count):
    repo_name = os.environ.get("GITHUB_REPOSITORY", "georgezhou2024/reesub").strip()
    cache_bust = ""
    # 绉佹湁鍖栭儴缃?Worker 鑴氭湰閲岀殑浠撳簱鍙傛暟 (榛樿鍊煎厹搴?
    try:
        owner, repo = repo_name.split("/", 1)
    except ValueError:
        owner, repo = "georgezhou2024", "reesub"

    def count_file(path):
        if not os.path.exists(path):
            return 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                c = f.read().strip()
                if not c:
                    return 0
                decoded = base64.b64decode(c).decode("utf-8", errors="ignore")
                return len([ln for ln in decoded.splitlines() if ln.strip()])
        except Exception:
            return 0

    res_counts, normal_counts = {}, {}
    for d, store in ((RESIDENTIAL_COUNTRY_DIR, res_counts), (COUNTRY_DIR, normal_counts)):
        if os.path.exists(d):
            for fn in os.listdir(d):
                if fn.endswith(".txt"):
                    cnt = count_file(os.path.join(d, fn))
                    if cnt > 0:
                        store[fn[:-4]] = cnt

    def table_rows(counts, sub):
        rows = []
        for cc in sorted(counts, key=lambda x: counts[x], reverse=True):
            flag = get_country_flag(cc)
            name = COUNTRY_NAMES.get(cc, cc)
            cnt = counts[cc]
            v2 = f"[CDN 鐩撮摼](https://cdn.jsdelivr.net/gh/{repo_name}@main/output/{sub}/{cc}.txt) 路 [Raw 鐩撮摼](https://raw.githubusercontent.com/{repo_name}/main/output/{sub}/{cc}.txt)"
            cl = f"[CDN 鐩撮摼](https://cdn.jsdelivr.net/gh/{repo_name}@main/output/{sub}/clash-{cc}.yaml) 路 [Raw 鐩撮摼](https://raw.githubusercontent.com/{repo_name}/main/output/{sub}/clash-{cc}.yaml)"
            sb = f"[CDN 鐩撮摼](https://cdn.jsdelivr.net/gh/{repo_name}@main/output/{sub}/singbox-{cc}.json) 路 [Raw 鐩撮摼](https://raw.githubusercontent.com/{repo_name}/main/output/{sub}/singbox-{cc}.json)"
            rows.append(f"| {flag} {name} | {cnt} | {v2} | {cl} | {sb} |")
        return "\n".join(rows) if rows else "| 鏆傛棤鍙敤鑺傜偣 | 0 | - | - | - |"

    res_table = table_rows(res_counts, "residential-by-country")
    normal_table = table_rows(normal_counts, "by-country")

    readme = f"""# 馃殌 鍏嶈垂鑺傜偣鑷姩娴嬫椿璁㈤槄姹?(鍚湡瀹炲瀹?浣忓畢IP鐢勯€?

> 馃懁 **瀹氬埗瑙勮寖鍛藉悕**: 鎵€鏈夎闃呰妭鐐瑰潎閲嶅懡鍚嶄负 `鍥芥棗 鍦板尯 搴忓彿 (瀹跺) - xiaohe`
> 鈿?**鐪熷疄鍙敤淇濋殰**: 鎵€鏈夎妭鐐圭敱 `sing-box v{SINGBOX_VERSION}` 鍐呮牳寤虹珛瀹為檯浠ｇ悊闅ч亾, 瀹屾垚鐪熷疄 HTTPS 鍙屽悜浼犺緭鎻℃墜 + 鍑哄彛 IP 绌块€忛獙璇?+ Cloudflare 闄愰€熶笅杞芥柇娴佹娴?+ TLS 璇佷功鏍￠獙 (MITM 鍔寔璇嗗埆), 鎷掔粷铏氬亣閫氱晠銆佹柇娴佽妭鐐逛笌楂樺嵄鍔寔鑺傜偣銆?
> 馃洝锔?**鍏ㄥ崗璁敮鎸?*: VLESS (Reality/Vision) 路 VMESS 路 Trojan 路 Shadowsocks 路 Hysteria2 路 TUIC 路 AnyTLS

---

## 馃搶 鍏ㄩ儴鑺傜偣鎬昏闃呴摼鎺?

| 瀹㈡埛绔?/ 鏍煎紡绫诲瀷 | 鑺傜偣鎬绘暟 | 鍏嶇炕 CDN 璁㈤槄鐩撮摼 (鍥藉唴鐩磋繛) | 瀹樻柟鍘熺敓 Raw 鐩撮摼 (寮€鍚唬鐞? |
| :--- | :---: | :--- | :--- |
| 馃殌 **Clash (YAML 鏍煎紡)** | `{total_count}` | [鍏嶇炕 CDN 鐩撮摼](https://cdn.jsdelivr.net/gh/{repo_name}@main/output/clash.yaml) | [瀹樻柟 Raw 鐩撮摼](https://raw.githubusercontent.com/{repo_name}/main/output/clash.yaml) |
| 鈿?**V2RayN (Base64 鏍煎紡)** | `{total_count}` | [鍏嶇炕 CDN 鐩撮摼](https://cdn.jsdelivr.net/gh/{repo_name}@main/output/v2ray.txt) | [瀹樻柟 Raw 鐩撮摼](https://raw.githubusercontent.com/{repo_name}/main/output/v2ray.txt) |
| 馃摝 **sing-box (JSON 鏍煎紡)** | `{total_count}` | [鍏嶇炕 CDN 鐩撮摼](https://cdn.jsdelivr.net/gh/{repo_name}@main/output/singbox.json) | [瀹樻柟 Raw 鐩撮摼](https://raw.githubusercontent.com/{repo_name}/main/output/singbox.json) |

---

## 馃彔 鎸夌収瀹跺鍒嗙被鑺傜偣璁㈤槄 (浣忓畢 IP 涓撳尯)

> 瀹跺鍒ゅ畾鍏噸淇″彿: 鈶?ip-api.com `hosting` 瀛楁 鈶?`mobile` 绉诲姩缃戠粶瀛楁 鈶?Cloudflare/涓绘祦 CDN Anycast 缃戞姣斿 鈶?MaxMind GeoLite2 ASN 鐧?榛戝悕鍗?(瑕嗙洊 60+ 鍥藉涓绘祦姘戠敤杩愯惀鍟? 鈶?rDNS/ISP 鍚嶇О鐗瑰緛 鈶?Scamalytics 椋庢帶璇勫垎澶嶆牳 (fraud 鈮?5 闄嶇骇銆佲墺90 鍓旈櫎)銆傛帓闄ゆ墍鏈変簯涓绘満/鏁版嵁涓績/CDN 浠绘挱, 淇濈暀鐪熷疄姘戠敤瀹藉甫涓庣Щ鍔ㄧ綉缁溿€?

| 瀹跺鍦板尯 | 鑺傜偣鏁?| V2RayN 涓撳睘璁㈤槄 | Clash 涓撳睘璁㈤槄 | sing-box 涓撳睘璁㈤槄 |
| :--- | :---: | :---: | :---: | :---: |
{res_table}

---

## 馃椇锔?鎸夌収鍥藉鍒嗙被鑺傜偣璁㈤槄 (闈炲瀹?鏁版嵁涓績鑺傜偣)

| 鍦板尯/鍥藉 | 鑺傜偣鏁?| V2RayN 涓撳睘璁㈤槄 | Clash 涓撳睘璁㈤槄 | sing-box 涓撳睘璁㈤槄 |
| :--- | :---: | :---: | :---: | :---: |
{normal_table}

---

## 馃敀 绉佹湁浠撳簱锛圥rivate锛夋棤鎰熷厤缈昏闃呮柟妗?(鍩轰簬 Cloudflare Workers)

> 濡傛灉浣犲笇鏈涘皢鏈?GitHub 浠撳簱璁剧疆涓?**Private (绉佹湁浠撳簱)** 淇濇姢鑺傜偣璧勪骇锛屽閮ㄥ鎴风鏃犳硶鐩存帴鎷夊彇鍘熺敓 Raw 鎴栧叕鍏?CDN 閾炬帴锛屽彲浠ラ€氳繃浠ヤ笅 Cloudflare Worker 鎼缓杞婚噺绾х瀵嗙綉鍏冲弽浠ｏ細

### 1. 鑾峰彇 GitHub 姘镐箙涓汉浠ょ墝 (PAT)
1. 杩涘叆 GitHub -> **Settings** -> **Developer Settings** -> **Personal access tokens (classic)**銆?
2. 鐐瑰嚮 **Generate new token (classic)**锛屽嬀閫?`repo` 鏉冮檺锛屾湁鏁堟湡璁句负 `No expiration`锛堟案涓嶈繃鏈燂級銆?
3. 澶嶅埗淇濆瓨鐢熸垚鐨勪互 `ghp_` 寮€澶寸殑 Token銆?

### 2. 閮ㄧ讲 Cloudflare Worker
鐧诲綍 Cloudflare Dashboard锛屽垱寤轰竴涓柊鐨?Worker锛屽鍒朵互涓嬭剼鏈矘璐村苟閮ㄧ讲锛堟妸 `OWNER`/`REPO`/`GITHUB_TOKEN` 鏀规垚浣犺嚜宸辩殑锛夛細

```javascript
export default {{
  async fetch(request) {{
    const GITHUB_TOKEN = "ghp_浣犵殑GitHub姘镐箙璁块棶浠ょ墝";
    const OWNER = "{owner}";
    const REPO = "{repo}";
    const BRANCH = "main";

    const url = new URL(request.url);
    const filePath = "output" + url.pathname;
    const ghUrl = "https://raw.githubusercontent.com/" + OWNER + "/" + REPO + "/" + BRANCH + "/" + filePath;

    const res = await fetch(ghUrl, {{
      headers: {{
        "Authorization": "token " + GITHUB_TOKEN,
        "User-Agent": "Cloudflare-Worker"
      }}
    }});

    if (!res.ok) {{
      return new Response("Not Found", {{ status: 404 }});
    }}

    return new Response(await res.text(), {{
      headers: {{
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache"
      }}
    }});
  }}
}}
```

### 3. 绉佹湁璁㈤槄閾炬帴鏄犲皠鏂瑰紡
閮ㄧ讲鍚?Worker 浼氬垎閰嶄竴涓笓灞炲煙鍚嶏紙渚嬪 `my-sub.yourname.workers.dev`锛夛紝浣犵殑瀹㈡埛绔彲浠ョ洿鎺ユ棤鎰熻闃咃細
* **鎬?V2RayN 璁㈤槄**: `https://浣犵殑鍩熷悕.workers.dev/v2ray.txt`
* **鎬?Clash 璁㈤槄**: `https://浣犵殑鍩熷悕.workers.dev/clash.yaml`
* **鎬?sing-box 璁㈤槄**: `https://浣犵殑鍩熷悕.workers.dev/singbox.json`
* **鍙版咕瀹跺 V2RayN**: `https://浣犵殑鍩熷悕.workers.dev/residential-by-country/TW.txt`
* **棣欐腐瀹跺 Clash**: `https://浣犵殑鍩熷悕.workers.dev/residential-by-country/clash-HK.yaml`
* **鏃ユ湰瀹跺 sing-box**: `https://浣犵殑鍩熷悕.workers.dev/residential-by-country/singbox-JP.json`

---

## 猸?椤圭洰鐑害

[![Star History Chart](https://api.star-history.com/svg?repos={repo_name}&type=Date)](https://star-history.com/#{repo_name}&Date)

---

## 馃洜锔?椤圭洰浣跨敤璇存槑
1. **鑷姩鏇存柊鏈哄埗**锛欸itHub Actions 姣?6 灏忔椂鍏ㄨ嚜鍔ㄨ繍琛屽苟鍒锋柊涓婅堪鍏ㄩ儴璁㈤槄涓庢暟鎹€?
2. **娴嬫椿鏍囧噯**锛氳妭鐐瑰繀椤婚€氳繃 鈶?绔彛棰勬 鈶?sing-box 瀹為檯闅ч亾 3 涓?generate_204 鎺㈡祴 鈶?鐪熷疄鍑哄彛 IP 绌块€忚幏鍙?鈶?Cloudflare 5MB 闄愭椂涓嬭浇 (鍚炲悙 鈮?70KB/s) 鈶?TLS 璇佷功鏍￠獙闈?MITM, 鏂瑰彲鍏ュ簱銆?
3. **澶氬鎴风鍏煎**锛欳lash / v2rayN / sing-box 鍏ㄦ牸寮忚闃呫€?
"""
    with open(os.path.join(BASEDIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"[+] README.md 鏇存柊瀹屾瘯: 鎬昏妭鐐?{total_count}, 瀹跺 {res_count}")


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# 涓绘祦绋?
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺怤鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

def main():
    t_start = time.time()
    print(f"==== 鍏嶈垂鑺傜偣娴嬫椿璁㈤槄姹?v2 路 鍚姩浜?{datetime.now(timezone.utc).isoformat()} ====")
    ensure_directories()
    setup_environment()

    # 1. 鎶撳彇
    raw_nodes = fetch_raw_nodes()

    # 2. 瑙ｆ瀽
    candidates = []
    parse_fail = 0
    for uri in raw_nodes:
        parsed = parse_node_uri(uri)
        if not parsed:
            parse_fail += 1
            continue
        outbound, server, port, proto = parsed
        # 灞忚斀鍗犱綅/骞垮憡鑺傜偣
        if BLACKLIST_NAME_HINTS.search(urllib.parse.unquote(uri.split("#", 1)[-1] if "#" in uri else "")):
            continue
        candidates.append((uri, outbound, server, port, proto))

    # 2.5 鈽?娴嬪墠寮哄幓閲?(鍑嵁鎸囩汗鍘婚噸: 鍚?鍑嵁+鐩爣+鍗忚 鍙祴涓€娆? 缁撴灉鍥炲～鍏ㄩ儴閲嶅鑺傜偣)
    #     key = (server, port, proto, 鍑嵁鎸囩汗): 鍑嵁涓嶅悓 鈫?鏈嶅姟绔牎楠岀粨鏋滃彲鑳戒笉鍚? 涓嶅彲鍚堝苟
    #     鍑嵁鎸囩汗: uuid/password 鍚勫崗璁殑鏍稿績韬唤瀛楁 (vless uuid / vmess id+alterId /
    #               trojan password / ss 2022瀵嗛挜 / hy2 auth / tuic uuid+passwd / anytls password)
    #     瀹屽叏鐩稿悓 = 鍚屼竴鑺傜偣琚婧愰噸澶嶆敹褰?(鍏嶈垂姹犲父鎬? 30+ 浠戒笉鍚屽悕瀛? 鈫?鍙祴涓€娆?
    def cred_fingerprint(outbound: dict, proto: str) -> str:
        try:
            if proto == "vless":
                return f"{outbound.get('uuid','')}"
            if proto == "vmess":
                return f"{outbound.get('uuid','') or outbound.get('user_id','')}"
            if proto == "trojan":
                return f"{outbound.get('password','')}"
            if proto == "shadowsocks":
                return f"{outbound.get('method','')}|{outbound.get('password','')}"
            if proto == "hysteria2":
                return f"{outbound.get('password','') or ''}|{outbound.get('server_ports','')}"
            if proto == "tuic":
                return f"{outbound.get('uuid','')}|{outbound.get('password','')}"
            if proto == "anytls":
                return f"{outbound.get('password','')}"
            return json.dumps({k: v for k, v in outbound.items()
                              if k in ("uuid", "password", "user_id", "method")}, sort_keys=True)
        except Exception:
            return ""  # 鎸囩汗澶辫触 鈫?涓嶅悎骞?(瀹佹參涓嶉敊)

    seen_keys, deduped, dup_count = {}, [], 0
    for item in candidates:
        uri, outbound, server, port, proto = item
        key = (server.lower() if server else "", port, proto, cred_fingerprint(outbound, proto))
        if key in seen_keys:
            seen_keys[key].append(uri)  # 璁板綍閲嶅 URI, 娴嬫椿鍚庡洖濉?
            dup_count += 1
        else:
            seen_keys[key] = [uri]
            deduped.append(item)
    if dup_count:
        print(f"[*] 娴嬪墠鍘婚噸(鍑嵁鎸囩汗): {len(candidates)} 鈫?{len(deduped)} (鍓旈櫎閲嶅 {dup_count} 鈥?缁撴灉灏嗗洖濉?")
    DEDUP_MAP = seen_keys  # 渚涙祴娲诲悗鍥炲～ (鍏ㄥ眬)
    candidates = deduped

    proto_stat = {}
    for _, _, _, _, p in candidates:
        proto_stat[p] = proto_stat.get(p, 0) + 1
    print(f"[*] 瑙ｆ瀽鎴愬姛(鍘婚噸鍚?: {len(candidates)} | 澶辫触 {parse_fail} | 鍗忚鍒嗗竷 {proto_stat}")

    if not candidates:
        print("[!] 鏃犲彲娴嬭妭鐐?(璁㈤槄婧愬叏閮ㄥけ鏁?) 鈥?淇濈暀涓婃 output, 涓嶈鐩栬闃呮枃浠?)
        return

    # 3. 绔彛棰勬
    candidates = prefilter_candidates(candidates)

    # 4. 鐪熷疄娴嬫椿 (鍙祴鍘婚噸鍚庣殑浠ｈ〃鑺傜偣)
    test_results = run_liveness_test(candidates)

    # 4.5 鈽?閲嶅鑺傜偣缁撴灉鍥炲～: 鍚?鍑嵁+鐩爣 鐨勯噸澶?URI 缁ф壙娴嬫椿缁撴灉 (鍑嵁鐩稿悓 鈫?鏈嶅姟绔〃鐜颁竴鑷?
    if DEDUP_MAP:
        result_by_key = {}
        for r in test_results:
            key = ((r["server"] or "").lower(), r["port"], r["proto"])
            result_by_key[key] = r
        expanded = list(test_results)
        backfilled = 0
        # 鍙嶅悜绱㈠紩: server:port:proto 鈫?鍘熷 fingerprint (浠?DEDUP_MAP 鐨?key 鐩存帴缁ф壙)
        for key, uris in DEDUP_MAP.items():
            if len(uris) <= 1:
                continue
            # 鐢?key 鐨勫墠涓夋 (server, port, proto) 鎵炬祴娲荤粨鏋?
            lookup = (key[0], key[1], key[2])
            r = result_by_key.get(lookup)
            if not r or not r.get("alive"):
                continue
            for extra_uri in uris[1:]:
                clone = dict(r)
                clone["raw"] = extra_uri
                expanded.append(clone)
                backfilled += 1
        if backfilled:
            print(f"[+] 閲嶅鑺傜偣鍥炲～: +{backfilled} (缁ф壙浠ｈ〃娴嬫椿缁撴灉)")
        test_results = expanded

    # 5. 鈽?瀹跺閾惧紡澶嶆祴: 鐢ㄦ渶蹇瓨娲昏妭鐐瑰仛鍓嶇疆鍙岃烦澶嶆祴瀹跺鍊欓€?
    #    (妯℃嫙鐢ㄦ埛 v2rayN 閾惧紡鍦烘櫙, 鍙岃烦澶辫触鐨勫瀹介檷绾ф櫘閫氬尯 鈥?鎻愰珮閾惧紡鍙敤鐜?
    test_results = chain_retest(test_results)

    # 6. 鍒嗙被 + 瀵煎嚭 (鏃犵湡娲昏妭鐐规椂淇濈暀涓婃 output, 涓嶅啓绌鸿闃呰鐩栫嚎涓婃暟鎹?
    if not test_results:
        print("[!] 鍏ㄩ儴鑺傜偣娴嬫椿澶辫触 鈥?淇濈暀涓婃 output, 涓嶈鐩栬闃呮枃浠?)
        return
    unique_nodes, residential, non_residential = classify_and_export(test_results)
    if not unique_nodes:
        print("[!] 鍒嗙被鍚庢棤瀛樻椿鑺傜偣 鈥?淇濈暀涓婃 output")
        return
    total, res = export_all(unique_nodes, residential, non_residential)
    update_readme(total, res)


    # 缁熻鎶ュ憡
    elapsed = time.time() - t_start
    print("\n===== 杩愯鎶ュ憡 =====")
    print(f"鎬昏€楁椂: {elapsed:.0f}s | 鎶撳彇 {len(raw_nodes)} 鈫?瑙ｆ瀽鎴愬姛 {len(candidates)} 鈫?鐪熸椿 {len(test_results)} 鈫?鍘婚噸鍚?{len(unique_nodes)} 鈫?瀹跺 {len(residential)}")
    by_type = {}
    for n in unique_nodes:
        by_type[n["net_type"]] = by_type.get(n["net_type"], 0) + 1
    print(f"鑺傜偣绫诲瀷鍒嗗竷: {by_type}")
    by_proto = {}
    for n in unique_nodes:
        by_proto[n["proto"]] = by_proto.get(n["proto"], 0) + 1
    print(f"鍗忚鍒嗗竷(鍑哄簱): {by_proto}")
    by_country = {}
    for n in unique_nodes:
        by_country[n["country"]] = by_country.get(n["country"], 0) + 1
    top_c = sorted(by_country.items(), key=lambda x: -x[1])[:10]
    print(f"鍥藉 Top10: {top_c}")


if __name__ == "__main__":
    main()
