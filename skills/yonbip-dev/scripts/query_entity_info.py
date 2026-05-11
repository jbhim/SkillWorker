"""
根据实体 URI 查询实体信息

用法:
    python query_entity_info.py <entity_uri>

环境变量:
    YONBIP_BASE_URL     - YonBIP 基础 URL (默认: https://lhdftest.yonyoucloud.com)
    YONBIP_TOKEN_CACHE_DIR - Token 缓存目录 (默认: 脚本同目录下的 .token-cache)
"""

import os
import sys
import json
import urllib.request
from pathlib import Path

# 确保输出使用 UTF-8 编码，避免 Windows 终端乱码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 默认配置
DEFAULT_BASE_URL = "https://lhdftest.yonyoucloud.com"
CACHE_DIR_NAME = ".token-cache"
CACHE_FILE_NAME = "yht_access_token.json"


def get_base_url():
    """获取基础 URL"""
    return os.environ.get("YONBIP_BASE_URL", DEFAULT_BASE_URL)


def get_cache_dir():
    """获取缓存目录（技能根目录下的 .token-cache）"""
    cache_dir = os.environ.get("YONBIP_TOKEN_CACHE_DIR")
    if not cache_dir:
        # 脚本在 scripts/ 下，缓存放在技能根目录
        cache_dir = Path(__file__).parent.parent / ".token-cache"
    return Path(cache_dir)


def load_token():
    """从缓存加载 token"""
    cache_file = get_cache_dir() / CACHE_FILE_NAME
    if not cache_file.exists():
        print(f"[ERROR] 未找到缓存文件，请先运行 get_yht_access_token.py 获取 token", file=sys.stderr)
        sys.exit(1)

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["token"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[ERROR] 缓存文件格式无效: {e}", file=sys.stderr)
        sys.exit(1)


def query_entity_info(uri, token):
    """
    根据实体 URI 查询实体信息

    Args:
        uri: 实体 URI (例如: areaFormat.model.areaFormatRecord)
        token: yht_access_token

    Returns:
        dict: 响应 JSON 数据
    """
    base_url = get_base_url()
    url = f"{base_url}/iuap-metadata-base/ext/MDD/entity/db/info?uri={uri}"

    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Referer": f"{base_url}/iuap-metadata-base/ucf-wh/simple/index.html",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Cookie": f"yht_access_token={token}",
        "serviceDomain": "developplatform",
        "istenant": "true",
        "scope": "self",
        "businessObject": "false",
    }

    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8")

    return json.loads(body)


def main():
    if len(sys.argv) < 2:
        print("[ERROR] 用法: python query_entity_info.py <entity_uri>", file=sys.stderr)
        sys.exit(1)

    uri = sys.argv[1]
    token = load_token()

    print(f"[INFO] 正在查询实体: {uri}...", file=sys.stderr)
    try:
        result = query_entity_info(uri, token)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP 错误: {e.code} {e.reason}", file=sys.stderr)
        print(f"[ERROR] 响应: {e.read().decode('utf-8')[:500]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
