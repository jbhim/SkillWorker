"""
获取友互通 Token (yht_access_token)

用法:
    python get_yht_access_token.py <userId>

环境变量:
    YONBIP_BASE_URL - YonBIP 基础 URL (默认: https://lhdftest.yonyoucloud.com)
    YONBIP_TOKEN_CACHE_DIR - Token 缓存目录 (默认: 脚本同目录下的 .token-cache)
"""

import os
import sys
import re
import json
import http.cookiejar
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timedelta

# 默认配置
DEFAULT_BASE_URL = "https://lhdftest.yonyoucloud.com"
CACHE_DIR_NAME = ".token-cache"
CACHE_FILE_NAME = "yht_access_token.json"
CACHE_EXPIRE_HOURS = 12  # token 缓存有效期（小时）


def get_base_url():
    """获取基础 URL，优先从环境变量读取"""
    return os.environ.get("YONBIP_BASE_URL", DEFAULT_BASE_URL)


def get_cache_dir():
    """获取缓存目录（技能根目录下的 .token-cache）"""
    cache_dir = os.environ.get("YONBIP_TOKEN_CACHE_DIR")
    if not cache_dir:
        # 脚本在 scripts/ 下，缓存放在技能根目录
        cache_dir = Path(__file__).parent.parent / ".token-cache"
    return Path(cache_dir)


def load_cached_token():
    """从缓存加载 token，如果未过期则返回"""
    cache_file = get_cache_dir() / CACHE_FILE_NAME
    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        cached_at = datetime.fromisoformat(data["cached_at"])
        if datetime.now() - cached_at > timedelta(hours=CACHE_EXPIRE_HOURS):
            return None  # 已过期

        return data["token"]
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def save_token(token, user_id):
    """保存 token 到缓存文件"""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / CACHE_FILE_NAME
    data = {
        "token": token,
        "user_id": user_id,
        "cached_at": datetime.now().isoformat(),
    }

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def decode_response(data: bytes) -> str:
    """解码响应数据，优先 UTF-8，失败则尝试 GBK，最后用 replace 容错"""
    for encoding in ("utf-8", "gbk", "gb2312", "latin-1"):
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, ValueError):
            continue
    return data.decode("utf-8", errors="replace")


def do_get(url, headers=None):
    """发送 GET 请求，返回响应体"""
    if headers is None:
        headers = {}

    req = urllib.request.Request(url)
    for key, value in headers.items():
        req.add_header(key, value)

    with urllib.request.urlopen(req, timeout=30) as response:
        return decode_response(response.read())


def do_get_with_cookies(url, headers=None):
    """发送 GET 请求并捕获 Cookie，返回 (响应体, Cookie列表)"""
    if headers is None:
        headers = {}

    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar)
    )

    req = urllib.request.Request(url)
    for key, value in headers.items():
        req.add_header(key, value)

    with opener.open(req, timeout=30) as response:
        body = decode_response(response.read())

    cookies = []
    for cookie in cookie_jar:
        cookies.append({"name": cookie.name, "value": cookie.value})

    return body, cookies


def get_yht_access_token(user_id):
    """
    获取友互通 token

    Args:
        user_id: 用户 ID

    Returns:
        str: yht_access_token 值

    Raises:
        RuntimeError: 获取 token 失败
    """
    base_url = get_base_url()

    # 步骤1: 获取登录 token
    url_str = f"{base_url}/cas/exclusive/genLoginTokenByUserIdLimitIp?userId={user_id}"
    res_body = do_get(url_str)

    import json as json_mod

    jo = json_mod.loads(res_body)
    token = jo.get("token")
    if not token:
        raise RuntimeError(f"获取 token 失败，响应: {res_body}")

    # 步骤2: 构造最终跳转链接
    work_bench_url = f"{base_url}/login?service="
    encode_redirect_url = urllib.parse.quote(base_url, safe="")
    send_redirect_url = urllib.parse.quote(work_bench_url + encode_redirect_url, safe="")
    final_url = f"{base_url}/cas/login?token={token}&service={send_redirect_url}"

    # 步骤3: 访问跳转链接，获取 location.href
    res_body2, _ = do_get_with_cookies(final_url)

    if not res_body2.strip():
        raise RuntimeError("获取友互通 Token 结果为空!")

    # 使用正则表达式提取 location.href 中的 URL
    pattern = re.compile(r'location\.href\s*=\s*"([^"]+)"')
    matcher = pattern.search(res_body2)

    location_href_url = ""
    if matcher:
        location_href_url = matcher.group(1).strip()
        # 移除可能存在的尾部反斜杠
        location_href_url = re.sub(r"\\+$", "", location_href_url)

    if not location_href_url:
        raise RuntimeError(f"未能解析 location.href，响应体: {res_body2[:500]}")

    # 步骤4: 访问最终 URL，从 Cookie 中提取 yht_access_token
    _, cookies = do_get_with_cookies(location_href_url)

    for cookie in cookies:
        if cookie["name"] == "yht_access_token":
            return cookie["value"]

    raise RuntimeError("未能从 Cookie 中找到 yht_access_token!")


def main():
    if len(sys.argv) < 2:
        print("用法: python get_yht_access_token.py <userId>")
        print("环境变量: YONBIP_BASE_URL (默认: https://lhdftest.yonyoucloud.com)")
        sys.exit(1)

    user_id = sys.argv[1]

    # 尝试从缓存加载
    cached = load_cached_token()
    if cached:
        print(f"[缓存命中] yht_access_token: {cached[:20]}...")
        print(cached)
        return

    # 获取新 token
    print(f"正在获取 token (userId={user_id})...")
    try:
        token = get_yht_access_token(user_id)
        save_token(token, user_id)
        print(f"yht_access_token: {token}")
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
