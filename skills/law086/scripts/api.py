#!/usr/bin/env python3
"""案件云 Open API 调用脚本

用法:
    python3 api.py GET /cases
    python3 api.py GET "/cases?keyword=张三&g_status=1"
    python3 api.py POST /calendar '{"title":"开庭","htime":"2026-04-30 14:00","endtime":"2026-04-30 15:00"}'
    python3 api.py PATCH /cases/ABC123 '{"stage_text":"已开庭"}'
    python3 api.py PUT /calendar/abc123 '{"title":"新标题"}'
    python3 api.py DELETE /calendar/abc123
    python3 api.py UPLOAD /cases/ABC123/files /path/to/file.pdf
    python3 api.py UPLOAD /cases/ABC123/files /path/to/file.pdf '{"folder_id":0}'

自动从同目录的 .env 文件加载 API_BASE_URL 和 PAT_TOKEN。
"""

import sys
import os
import json
import re
import io

try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from urllib.parse import quote, urlparse, quote_plus
except ImportError:
    from urllib2 import Request, urlopen, HTTPError, URLError

import mimetypes
import uuid


def load_env():
    """从 skill 目录加载 .env（先找脚本同级，再找上级 skill 根目录）"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, '.env'),
        os.path.join(script_dir, '..', '.env'),
    ]
    env_path = None
    for p in candidates:
        if os.path.exists(p):
            env_path = p
            break

    env = {}
    if not env_path:
        print(json.dumps({
            'code': -1,
            'msg': '.env 文件不存在',
            'hint': '请复制 .env.example 为 .env 并填入 PAT_TOKEN'
        }, ensure_ascii=False))
        sys.exit(1)

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()

    base_url = env.get('API_BASE_URL', '').rstrip('/')
    token = env.get('PAT_TOKEN', '')

    if not base_url:
        print(json.dumps({'code': -1, 'msg': 'API_BASE_URL 未配置'}, ensure_ascii=False))
        sys.exit(1)

    if not token or 'xxx' in token:
        print(json.dumps({
            'code': -1,
            'msg': 'PAT_TOKEN 未配置或仍为占位值',
            'hint': '请在案件云 OA「个人设置 > AI管理」中生成 PAT，填入 .env'
        }, ensure_ascii=False))
        sys.exit(1)

    return base_url, token


def make_request(method, base_url, token, path, body=None):
    """发送 HTTP 请求并返回格式化的响应"""
    # 确保 path 以 / 开头
    if not path.startswith('/'):
        path = '/' + path

    # 对 URL 中的非 ASCII 字符进行编码
    if '?' in path:
        path_base, query = path.split('?', 1)
        pairs = []
        for part in query.split('&'):
            if '=' in part:
                k, v = part.split('=', 1)
                pairs.append('{}={}'.format(quote_plus(k), quote_plus(v, safe='')))
            else:
                pairs.append(quote_plus(part))
        path = path_base + '?' + '&'.join(pairs)

    url = base_url + path

    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'Accept': 'application/json',
    }

    data = None
    if body is not None:
        headers['Content-Type'] = 'application/json; charset=utf-8'
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')

    req = Request(url, data=data, headers=headers)
    req.method = method.upper()

    try:
        response = urlopen(req, timeout=30)
        resp_bytes = response.read()
        encoding = response.headers.get_content_charset() or 'utf-8'
        resp_text = resp_bytes.decode(encoding)

        try:
            resp_json = json.loads(resp_text)
        except (json.JSONDecodeError, ValueError):
            return {'code': -1, 'msg': '响应非 JSON', 'raw': resp_text[:500]}

        return resp_json

    except HTTPError as e:
        body_text = ''
        try:
            body_text = e.read().decode('utf-8', errors='replace')[:500]
        except Exception:
            pass

        if e.code == 401:
            return {
                'code': 2,
                'msg': 'Token 无效或已过期，请重新生成 PAT',
                'http_status': e.code
            }
        elif e.code == 403:
            return {
                'code': 3,
                'msg': '权限不足，请检查 PAT 的 scope 设置',
                'http_status': e.code
            }
        elif e.code == 404:
            return {
                'code': -1,
                'msg': '接口不存在: {} {}'.format(method, path),
                'http_status': e.code
            }
        else:
            return {
                'code': -1,
                'msg': 'HTTP {} 错误'.format(e.code),
                'http_status': e.code,
                'detail': body_text
            }

    except URLError as e:
        return {
            'code': -1,
            'msg': '网络错误: {}'.format(str(e.reason)),
            'hint': '请检查网络连接和 API_BASE_URL 是否正确'
        }

    except Exception as e:
        return {
            'code': -1,
            'msg': '请求异常: {}'.format(str(e))
        }


def make_upload_request(method, base_url, token, path, file_path, extra_fields=None):
    """发送 multipart/form-data 上传文件请求并返回格式化的响应"""
    if not path.startswith('/'):
        path = '/'

    url = base_url + path

    if not os.path.exists(file_path):
        return {'code': -1, 'msg': '文件不存在: {}'.format(file_path)}

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # 10MB 限制提示
    if file_size > 10 * 1024 * 1024:
        return {'code': -1, 'msg': '文件大小超过10MB限制，请到 OA 网页端上传'}

    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'

    boundary = uuid.uuid4().hex
    lines = []

    # 添加额外字段
    if extra_fields:
        for key, value in extra_fields.items():
            lines.append('--{}'.format(boundary))
            lines.append('Content-Disposition: form-data; name="{}"'.format(key))
            lines.append('')
            lines.append(str(value))

    # 添加文件字段
    lines.append('--{}'.format(boundary))
    lines.append('Content-Disposition: form-data; name="file"; filename="{}"'.format(file_name))
    lines.append('Content-Type: {}'.format(content_type))
    lines.append('')
    lines.append('')

    body_prefix = '\r\n'.join(lines).encode('utf-8')
    body_suffix = '\r\n--{}--\r\n'.format(boundary).encode('utf-8')

    with open(file_path, 'rb') as f:
        body = body_prefix + f.read() + body_suffix

    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'Content-Type': 'multipart/form-data; boundary={}'.format(boundary),
    }

    req = Request(url, data=body, headers=headers)
    req.method = 'POST'

    try:
        response = urlopen(req, timeout=60)
        resp_bytes = response.read()
        encoding = response.headers.get_content_charset() or 'utf-8'
        resp_text = resp_bytes.decode(encoding)

        try:
            resp_json = json.loads(resp_text)
        except (json.JSONDecodeError, ValueError):
            return {'code': -1, 'msg': '响应非 JSON', 'raw': resp_text[:500]}

        return resp_json

    except HTTPError as e:
        body_text = ''
        try:
            body_text = e.read().decode('utf-8', errors='replace')[:500]
        except Exception:
            pass

        if e.code == 401:
            return {'code': 2, 'msg': 'Token 无效或已过期，请重新生成 PAT', 'http_status': e.code}
        elif e.code == 403:
            return {'code': 3, 'msg': '权限不足，请检查 PAT 的 scope 设置', 'http_status': e.code}
        else:
            return {'code': -1, 'msg': 'HTTP {} 错误'.format(e.code), 'http_status': e.code, 'detail': body_text}

    except URLError as e:
        return {'code': -1, 'msg': '网络错误: {}'.format(str(e.reason))}

    except Exception as e:
        return {'code': -1, 'msg': '请求异常: {}'.format(str(e))}


def _ensure_stdout_utf8():
    """强制 stdout/stderr 使用 UTF-8 编码，避免中文乱码"""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def main():
    _ensure_stdout_utf8()

    if len(sys.argv) < 3:
        print('用法: python3 api.py <METHOD> <PATH> [JSON_BODY]')
        print('      python3 api.py UPLOAD <PATH> <FILE_PATH> [JSON_FIELDS]')
        print('示例: python3 api.py GET /cases')
        print('      python3 api.py POST /calendar \'{"title":"开庭"}\'')
        print('      python3 api.py PATCH /records/abc123 \'{"hstatus":1}\'')
        print('      python3 api.py UPLOAD /cases/ABC123/files /path/to/file.pdf')
        sys.exit(1)

    method = sys.argv[1].upper()
    path = sys.argv[2]

    if method == 'UPLOAD':
        if len(sys.argv) < 4:
            print('用法: python3 api.py UPLOAD <PATH> <FILE_PATH> [JSON_FIELDS]')
            sys.exit(1)

        file_path = sys.argv[3]
        extra_fields = None
        if len(sys.argv) > 4:
            try:
                extra_fields = json.loads(sys.argv[4])
            except json.JSONDecodeError as e:
                print(json.dumps({
                    'code': -1,
                    'msg': 'JSON 解析失败: {}'.format(str(e)),
                    'input': sys.argv[4][:200]
                }, ensure_ascii=False))
                sys.exit(1)

        base_url, token = load_env()
        result = make_upload_request('UPLOAD', base_url, token, path, file_path, extra_fields)

    elif method not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
        print(json.dumps({
            'code': -1,
            'msg': '不支持的 HTTP 方法: {}'.format(method),
            'supported': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'UPLOAD']
        }, ensure_ascii=False))
        sys.exit(1)

    else:
        body = None
        if len(sys.argv) > 3:
            try:
                body = json.loads(sys.argv[3])
            except json.JSONDecodeError as e:
                print(json.dumps({
                    'code': -1,
                    'msg': 'JSON 解析失败: {}'.format(str(e)),
                    'input': sys.argv[3][:200]
                }, ensure_ascii=False))
                sys.exit(1)

        base_url, token = load_env()
        result = make_request(method, base_url, token, path, body)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
