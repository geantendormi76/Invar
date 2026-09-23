import sys

try:
    from curl_cffi import requests
    print("✅ curl_cffi 已就绪！版本:", requests.__version__)
    h = {
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    r = requests.post(
        "https://cloud.ikuai8.com/api/v3/delegate/grant",
        json={},
        headers=h,
        impersonate="chrome124",
        timeout=10
    )
    print("HTTP 状态码:", r.status_code)
    print("响应正文预览:", r.text[:120])
except ImportError:
    print("❌ 当前虚拟环境尚未安装 curl_cffi")
except Exception as e:
    print("请求异常:", e)
