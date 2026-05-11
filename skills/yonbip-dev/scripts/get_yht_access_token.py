"""
获取友互通 Token (yht_access_token)

用法:
    python get_yht_access_token.py [userId] [--reset]

说明:
    - 不带参数时自动使用缓存的 userId
    - 如果未缓存过 userId，会提示用户输入
    - 如果获取 token 失败，会提示用户重新确认 userId
    - --reset 强制重新输入 userId

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

# 确保输出使用 UTF-8 编码，避免 Windows 终端乱码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 默认配置
DEFAULT_BASE_URL = "https://lhdftest.yonyoucloud.com"
CACHE_DIR_NAME = ".token-cache"
CACHE_FILE_NAME = "yht_access_token.json"
USER_ID_FILE_NAME = "user_id.txt"
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


def load_cached_user_id():
    """从缓存加载 userId"""
    cache_file = get_cache_dir() / USER_ID_FILE_NAME
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8").strip()
    return None


def save_user_id(user_id):
    """保存 userId 到缓存"""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / USER_ID_FILE_NAME
    cache_file.write_text(user_id, encoding="utf-8")


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

    jo = json.loads(res_body)
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


def request_user_id():
    """请求提供 userId（非交互式，仅输出错误信息供 AI 解析）"""
    sys.stderr.flush()
    print("[ERROR] 未配置 userId，无法获取 Token。", file=sys.stderr)
    print("[ERROR] 请提供 userId 参数，例如: python get_yht_access_token.py <userId>", file=sys.stderr)
    print("[ERROR] userId 可从浏览器 Cookie 或 YonBIP 个人中心获取。", file=sys.stderr)
    sys.stderr.flush()
    sys.exit(1)


def main():
    args = sys.argv[1:]

    # 检查 --reset 参数
    force_reset = "--reset" in args
    if force_reset:
        # 清除缓存的 userId 和 token
        cache_dir = get_cache_dir()
        uid_file = cache_dir / USER_ID_FILE_NAME
        token_file = cache_dir / CACHE_FILE_NAME
        if uid_file.exists():
            uid_file.unlink()
        if token_file.exists():
            token_file.unlink()
        print("[重置] 已清除缓存的 userId 和 token。", file=sys.stderr)

    user_id_from_arg = None
    for arg in args:
        if arg != "--reset":
            user_id_from_arg = arg

    # 尝试从缓存加载 token
    cached_token = load_cached_token()
    if cached_token and not force_reset:
        print(cached_token)
        return

    # 确定 userId：优先使用命令行参数，其次使用缓存
    if user_id_from_arg:
        user_id = user_id_from_arg
    else:
        user_id = load_cached_user_id()
        if not user_id:
            # 非交互式：直接报错，请求用户提供 userId
            request_user_id()

    # 获取 token
    try:
        token = get_yht_access_token(user_id)
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] 获取 token 失败 (userId={user_id}): {error_msg}", file=sys.stderr)
        print(f"[ERROR] userId 可能无效，请确认或更换新 userId。", file=sys.stderr)
        sys.exit(1)

    save_token(token, user_id)
    if not load_cached_user_id():
        save_user_id(user_id)
    print(token)


if __name__ == "__main__":
    main()
