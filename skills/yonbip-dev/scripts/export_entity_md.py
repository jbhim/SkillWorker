"""
查询实体元数据并生成 Markdown 文档（带缓存）

用法:
    python export_entity_md.py <entity_uri> [output_dir]

说明:
    - 首次查询会请求 API 并生成 Markdown 文档
    - 结果自动缓存，后续查询直接从缓存读取
    - 输出文件名: {entity_name}.md

环境变量:
    YONBIP_BASE_URL        - YonBIP 基础 URL
    YONBIP_TOKEN_CACHE_DIR - Token 缓存目录
    YONBIP_ENTITY_CACHE_DIR - 实体文档缓存目录 (默认: 脚本同目录下的 .entity-cache)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 确保输出使用 UTF-8 编码，避免 Windows 终端乱码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 导入共用模块
sys.path.insert(0, os.path.dirname(__file__))
from query_entity_info import load_token, query_entity_info

# 默认配置
CACHE_DIR_NAME = ".entity-cache"

# 类型映射
TYPE_DISPLAY = {
    "String": "文本",
    "Short": "短整数",
    "Integer": "整数",
    "Long": "长整数",
    "Float": "单精度浮点",
    "Double": "双精度浮点",
    "Boolean": "布尔",
    "DateTime": "日期时间",
    "Date": "日期",
    "Time": "时间",
    "Timestamp": "时间戳",
    "BigDecimal": "高精度数字",
    "Binary": "二进制",
    "Byte": "字节",
    "Char": "字符",
}

BIZTYPE_DISPLAY = {
    "text": "文本",
    "quote": "单选引用",
    "short": "短整数",
    "int": "整数",
    "long": "长整数",
    "double": "双精度浮点",
    "float": "单精度浮点",
    "dateTime": "日期时间",
    "date": "日期",
    "boolean": "布尔",
    "UserDefine": "自定义特征",
}

TERM_DISPLAY = {
    "ConfigData": "配置数据",
    "doc": "档案数据",
    "isMain": "是否可被引用",
    "MasterData": "主数据",
    "nullable": "非空校验",
    "isName": "名称",
    "notGenerate": "不生成",
    "uiHide": "UI隐藏",
    "dataAuth": "数据权限管控",
    "data_auth": "数据权限管控",
    "isSyncKey": "同步键",
    "REF.ID": "引用ID",
}


def get_cache_dir():
    """获取实体文档缓存目录"""
    cache_dir = os.environ.get("YONBIP_ENTITY_CACHE_DIR")
    if not cache_dir:
        cache_dir = Path(__file__).parent.parent / CACHE_DIR_NAME
    return Path(cache_dir)


def get_cache_file(entity_uri):
    """获取缓存文件路径"""
    cache_dir = get_cache_dir()
    # 用 URI 作为文件名，/ 替换为 _
    filename = entity_uri.replace("/", "_") + ".md"
    return cache_dir / filename


def load_cached_md(entity_uri):
    """从缓存加载 Markdown"""
    cache_file = get_cache_file(entity_uri)
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    return None


def save_md(entity_uri, content):
    """保存 Markdown 到缓存"""
    cache_file = get_cache_file(entity_uri)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(content, encoding="utf-8")


def get_type_display(attr):
    """获取字段类型的显示名称"""
    # 优先从 biztype 映射
    biztype = attr.get("biztype", "")
    if biztype in BIZTYPE_DISPLAY:
        return BIZTYPE_DISPLAY[biztype]

    # 从 type 字段判断
    type_val = attr.get("type", "")
    if isinstance(type_val, dict):
        type_name = type_val.get("name", type_val.get("title", ""))
    else:
        type_name = type_val

    if type_name in TYPE_DISPLAY:
        return TYPE_DISPLAY[type_name]

    # 如果是 UUID 格式，说明是引用类型
    if type_name and len(type_name) > 20:
        return "引用"

    return type_name or "-"


def get_ref_display(attr):
    """获取引用信息"""
    type_uri = attr.get("typeUri", "")
    if type_uri and type_uri not in ("String", "Short", "Integer", "Long",
                                      "Float", "Double", "Boolean", "DateTime",
                                      "Date", "Time", "Timestamp", "BigDecimal",
                                      "Binary", "Byte", "Char"):
        return type_uri
    return "-"


def get_tags_display(attr):
    """获取字段标签（去重，基于最终显示文本）"""
    terms = attr.get("terms", [])
    seen_labels = set()
    tags = []
    for t in terms:
        code = t.get("code", "")
        label = TERM_DISPLAY.get(code)
        if label and label not in seen_labels:
            seen_labels.add(label)
            tags.append(label)
    return "; ".join(tags) if tags else "-"


def get_description(attr):
    """获取字段描述"""
    desc = attr.get("description", "")
    # description 可能在 mul_language_resid 中
    if not desc:
        mul_lang = attr.get("mul_language_resid", {})
        desc = mul_lang.get("description", "")
    return desc


def get_source(attr):
    """获取字段来源"""
    uri = attr.get("uri", "")
    # 从 uri 中提取实体部分 (uri格式: entity.fieldName)
    parts = uri.rsplit(".", 1)
    if len(parts) > 1:
        return parts[0]
    return "-"


def get_schema(data):
    """推断 schema 名称（从实体 URI 的第一段）"""
    uri = data.get("uri", "")
    if uri:
        parts = uri.split(".")
        if len(parts) >= 2:
            return parts[0]
    # 其次从 domain 推断
    domain = data.get("domain", "")
    if domain:
        return domain
    return "-"


def parse_attributes(data):
    """解析实体所有属性（主实体 + 扩展）"""
    all_attrs = []
    seen_field_names = set()

    # 主实体属性
    for attr in data.get("attributes", []):
        # 编码取 name（业务编码），没有则 fallback 到 fieldName
        code = attr.get("name", "")
        if not code:
            code = attr.get("fieldName", "")
        if not code:
            continue

        if code in seen_field_names:
            continue
        seen_field_names.add(code)

        all_attrs.append({
            "code": code,
            "displayName": attr.get("title", attr.get("displayName", "")),
            "type": get_type_display(attr),
            "ref": get_ref_display(attr),
            "tags": get_tags_display(attr),
            "source": get_source(attr),
            "tableName": data.get("tableName", ""),
            "columnName": attr.get("columnName", ""),
            "description": get_description(attr),
        })

    # 扩展实体 (suppliers) 中独有的字段
    for supplier in data.get("suppliers", []):
        for attr in supplier.get("attributes", []):
            code = attr.get("name", "")
            if not code:
                code = attr.get("fieldName", "")
            if not code:
                continue
            if code in seen_field_names:
                continue
            seen_field_names.add(code)

            all_attrs.append({
                "code": code,
                "displayName": attr.get("title", attr.get("displayName", "")),
                "type": get_type_display(attr),
                "ref": get_ref_display(attr),
                "tags": get_tags_display(attr),
                "source": get_source(attr),
                "tableName": data.get("tableName", ""),
                "columnName": attr.get("columnName", ""),
                "description": get_description(attr),
            })

    return all_attrs


def generate_md(data, entity_uri):
    """生成 Markdown 文档"""
    lines = []

    # === 基本信息 ===
    lines.append("## 基本信息")
    lines.append("")
    lines.append(f"| 项目 | 值 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 名称 | {data.get('title', data.get('displayName', ''))} |")
    lines.append(f"| 编码 | {data.get('name', '')} |")
    lines.append(f"| 实体URI | {entity_uri} |")
    lines.append(f"| 业务对象 | {data.get('title', '')} |")
    lines.append(f"| 业务对象编码 | {data.get('businessObjectId', '')} |")
    lines.append(f"| 表名 | {data.get('tableName', '')} |")
    lines.append(f"| 服务域 | {data.get('domain', '')} |")

    # 标签
    terms = data.get("terms", [])
    term_labels = []
    for t in terms:
        code = t.get("code", "")
        label = TERM_DISPLAY.get(code, code)
        if label:
            term_labels.append(label)
    lines.append(f"| 标签 | {', '.join(term_labels)} |" if term_labels else "| 标签 | - |")

    # schema
    schema = get_schema(data)
    lines.append(f"| schema | {schema} |")

    # 继承
    super_uri = data.get("superUri", "")
    if super_uri:
        lines.append(f"| 继承 | {super_uri} |")
    else:
        lines.append("| 继承 | - |")

    # 引用接口 (suppliers)
    suppliers = data.get("suppliers", [])
    if suppliers:
        supplier_names = [s.get("title", s.get("displayName", s.get("name", ""))) for s in suppliers]
        lines.append(f"| 引用接口 | {', '.join(supplier_names)} |")
    else:
        lines.append("| 引用接口 | - |")

    lines.append("")

    # === 约束信息 ===
    constraints = data.get("constraints", [])
    if constraints:
        lines.append("## 约束")
        lines.append("")
        for c in constraints:
            title = c.get("title", c.get("name", ""))
            ctype = c.get("type", "")
            unique_attrs = c.get("uniqueAttributes", [])
            if unique_attrs:
                lines.append(f"- **{title}** ({ctype}): {', '.join(unique_attrs)}")
            else:
                lines.append(f"- **{title}** ({ctype})")
        lines.append("")

    # === 属性列表 ===
    attrs = parse_attributes(data)

    lines.append("## 属性列表")
    lines.append("")
    lines.append("| 序号 | 编码 | 名称 | 类型 | 引用 | 标签 | 来源 | 表名 | 表字段名 | 描述 |")
    lines.append("|------|------|------|------|------|------|------|------|----------|------|")

    for i, attr in enumerate(attrs, 1):
        desc = attr["description"].replace("|", "\\|").replace("\n", " ")
        table_name = attr["tableName"] if attr["tableName"] else "-"
        col_name = attr["columnName"] if attr["columnName"] else "-"
        lines.append(
            f"| {i} | {attr['code']} | {attr['displayName']} | {attr['type']} "
            f"| {attr['ref']} | {attr['tags']} | {attr['source']} "
            f"| {table_name} | {col_name} | {desc} |"
        )

    lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("[ERROR] 用法: python export_entity_md.py <entity_uri> [output_dir]", file=sys.stderr)
        sys.exit(1)

    entity_uri = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    # 尝试从缓存加载
    cached = load_cached_md(entity_uri)
    if cached:
        print(f"[INFO] 缓存命中: {entity_uri}", file=sys.stderr)
        print(cached)
        return

    # 获取 token 并查询
    print(f"[INFO] 正在查询实体: {entity_uri}...", file=sys.stderr)
    token = load_token()
    result = query_entity_info(entity_uri, token)

    data = result.get("data", {})
    md = generate_md(data, entity_uri)

    # 保存到缓存
    save_md(entity_uri, md)
    print(f"[INFO] 已缓存: {entity_uri}", file=sys.stderr)
    print(md)


if __name__ == "__main__":
    main()
