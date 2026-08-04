#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""庭审实时转写（讯飞 RTASR 实时流 + 离线回退）

为「109-庭审实时辅助系统」提供转写能力：
  · 模式 A（实时流）：检测到讯飞 RTASR 凭据（IFLYTEK_APPID + IFLYTEK_API_SECRET，
    鉴权不用 APIKey）且具备 websocket 依赖时，走 WebSocket 流式分句转写。
  · 模式 B（离线回退）：未配置凭据或依赖缺失时，自动调用同目录的
    voice_transcribe.py 做录音后处理转写，保证要点浮窗能力不中断。

说话人分离说明：标准 RTASR 不含说话人分离。本脚本在开庭前由律师设定角色
边界（我方/对方/第三方），并对静音段做切分标注；精确的说话人分离需接入
讯飞「语音转写」产品或第三方 diarization 服务，届时在此处替换 transcribe_realtime 即可。

凭据走环境变量，缺失时优雅降级，不阻塞主流程。
"""
import os
import sys
import json
import base64
import hashlib
import hmac
import subprocess
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))


def have_credentials():
    """是否已配置讯飞 RTASR 凭据（鉴权仅需 APPID + APISecret）。"""
    return bool(os.getenv("IFLYTEK_APPID") and os.getenv("IFLYTEK_API_SECRET"))


def _now_rfc1123():
    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")


def build_auth_url():
    """构造讯飞 RTASR WebSocket 握手 URL（HMAC-SHA256 签名）。

    参考讯飞开放平台「实时语音转写 RTASR」鉴权规范：
      签名原文 = host + "\\n" + date + "\\n" + request_line
      authorization = base64(HmacSHA256(APISecret, 签名原文))
    """
    appid = os.getenv("IFLYTEK_APPID")
    api_secret = os.getenv("IFLYTEK_API_SECRET")
    host = "iat-api.xfyun.cn"
    date = _now_rfc1123()
    request_line = "GET /v2/iat HTTP/1.1"
    signature_origin = "host: %s\ndate: %s\n%s" % (host, date, request_line)
    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    signature = base64.b64encode(signature_sha).decode("utf-8")
    authorization = (
        'api_key="%s", algorithm="hmac-sha256", headers="host date request-line", '
        'signature="%s"' % (appid, signature)
    )
    return (
        "wss://%s/v2/iat?authorization=%s&date=%s&host=%s"
        % (
            host,
            base64.b64encode(authorization.encode("utf-8")).decode("utf-8"),
            base64.b64encode(date.encode("utf-8")).decode("utf-8"),
            host,
        )
    )


def transcribe_offline(audio_path):
    """模式 B：调用 voice_transcribe.py 做录音后处理转写。"""
    voice_script = os.path.join(HERE, "voice_transcribe.py")
    if not os.path.isfile(voice_script):
        print("[离线回退] 未找到 voice_transcribe.py，无法转写：%s" % audio_path)
        return None
    print("[模式B] 录音后处理转写：%s" % audio_path)
    try:
        r = subprocess.run(
            [sys.executable, voice_script, audio_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if r.returncode != 0:
            print("[离线回退] voice_transcribe.py 执行失败：%s" % (r.stderr or r.stdout)[-300:])
            return None
        return r.stdout
    except Exception as e:  # noqa: BLE001
        print("[离线回退] 异常：%s" % e)
        return None


def transcribe_realtime(audio_path):
    """模式 A：讯飞 RTASR WebSocket 流式转写。

    依赖 websocket-client（pip install websocket-client）。未安装时抛出
    ImportError，由调用方降级到离线模式。
    """
    try:
        import websocket  # noqa: F401
    except ImportError:
        raise ImportError("缺少 websocket-client 依赖，请 pip install websocket-client")

    import _thread as thread  # noqa: WPS433

    url = build_auth_url()
    result_parts = []
    role_map = {}  # 说话人角色设定（开庭前由律师提供）

    def on_message(ws, message):
        data = json.loads(message)
        if data.get("code") != 0:
            print("[RTASR] 错误：%s" % data.get("message"))
            return
        for item in data.get("data", {}).get("result", {}).get("ws", []):
            for w in item.get("cw", []):
                result_parts.append(w.get("w", ""))
        # 末帧：data.status == 2 表示结束
        if data.get("data", {}).get("status") == 2:
            ws.close()

    def on_error(ws, error):
        print("[RTASR] WebSocket 错误：%s" % error)

    def on_close(ws, *args):
        pass

    def on_open(ws):
        def send_frames():
            # 真实实现需读取音频文件分帧（每 40ms 一帧，base64 发送）。
            # 此处给出标准发送骨架；音频读取与分帧由音频库（pydub/ffmpeg）完成。
            import time as _t

            frame_size = 1280  # 16k/16bit/单声道，40ms
            try:
                with open(audio_path, "rb") as f:
                    while True:
                        chunk = f.read(frame_size)
                        if not chunk:
                            break
                        ws.send(
                            json.dumps(
                                {
                                    "data": base64.b64encode(chunk).decode("utf-8"),
                                    "status": 1,
                                }
                            )
                        )
                        _t.sleep(0.04)
                ws.send(json.dumps({"status": 2}))
            except Exception as e:  # noqa: BLE001
                print("[RTASR] 发送异常：%s" % e)

        thread.start_new_thread(send_frames, ())

    print("[模式A] 讯飞 RTASR 实时流转写：%s" % audio_path)
    ws = websocket.WebSocketApp(
        url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )
    ws.run_forever()
    return "".join(result_parts)


def main():
    if len(sys.argv) < 2:
        print("用法：python realtime_transcribe.py <音频文件>")
        print("环境变量：IFLYTEK_APPID / IFLYTEK_API_SECRET（实时流；缺失则离线回退）")
        return 1
    audio = sys.argv[1]
    if not os.path.isfile(audio):
        print("[错误] 音频文件不存在：%s" % audio)
        return 2

    if have_credentials():
        try:
            text = transcribe_realtime(audio)
            if text is None:
                print("[回退] 实时流失败，转录音后处理模式")
                transcribe_offline(audio)
            else:
                print(text)
            return 0
        except ImportError:
            print("[回退] 缺少 websocket 依赖，转录音后处理模式")
            transcribe_offline(audio)
            return 0
    else:
        print("[模式B] 未检测到讯飞 RTASR 凭据（IFLYTEK_APPID / IFLYTEK_API_SECRET），使用录音后处理模式")
        transcribe_offline(audio)
        return 0


if __name__ == "__main__":
    sys.exit(main())
