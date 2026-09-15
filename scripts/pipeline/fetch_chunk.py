import os
import sys
import argparse
from pathlib import Path
import requests
import urllib3

# 消除自签名证书警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 前端工程打包常见的 Chunk 暴露相对路径模板
DEFAULT_CANDIDATE_TEMPLATES = [
    "{base_url}/assets/{chunk}",
    "{base_url}/{chunk}",
    "{base_url}/js/{chunk}",
    "{base_url}/static/js/{chunk}",
    "{base_url}/static/assets/{chunk}"
]

class ChunkFetcher:
    """
    Invar 前端静态分包补全下载器 (具备代理穿透与多候选路径探测能力)
    """
    def __init__(self, proxy: str = "http://127.0.0.1:7897", timeout: int = 10):
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*"
        }

    def fetch(self, base_url: str, chunk_name: str, save_dir: Path) -> Path:
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / chunk_name
        base = base_url.rstrip("/")

        print("==================================================")
        print(" 📦 Invar 缺失前端分包 (Chunk) 动态补全引擎")
        print("==================================================")
        print(f"  ├─ 🎯 目标分包名称: {chunk_name}")
        print(f"  ├─ 🌐 基础域名站点: {base}")
        print(f"  ├─ 🛡️ 本地代理配置: {self.proxies.get('http') if self.proxies else '直连 (无代理)'}")
        print(f"  └─ 📁 保存目标路径: {save_path.resolve()}\n")

        for idx, tmpl in enumerate(DEFAULT_CANDIDATE_TEMPLATES, 1):
            url = tmpl.format(base_url=base, chunk=chunk_name)
            print(f"  [{idx}/{len(DEFAULT_CANDIDATE_TEMPLATES)}] 正在探测路径: {url} ...")
            try:
                resp = requests.get(
                    url,
                    headers=self.headers,
                    proxies=self.proxies,
                    timeout=self.timeout,
                    verify=False
                )
                # 过滤 Nginx 404 前端 HTML 伪响应，确保是真实 JS 内容
                if resp.status_code == 200 and len(resp.content) > 0 and not resp.text.strip().lower().startswith("<!doctype"):
                    save_path.write_bytes(resp.content)
                    print(f"\n[✓] 成功命中并下载 Chunk! 大小: {len(resp.content)} 字节")
                    print(f"[✓] 资源已无损落盘至: {save_path.resolve()}\n")
                    return save_path
                else:
                    print(f"      └─ 状态不符: HTTP [{resp.status_code}], 响应前缀非 JS 代码")
            except Exception as e:
                print(f"      └─ 请求异常: {str(e)}")

        print(f"\n[X] 探测完毕，未能在常规路径中定位到分包: {chunk_name}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Invar 前端分包自动补全下载器")
    parser.add_argument("base_url", help="目标基础 URL (如 https://example.com)")
    parser.add_argument("chunk", help="需要补全的 JS 文件名 (如 popover-vddj8Agd.js)")
    parser.add_argument("-o", "--output-dir", default="data/raw_js", help="保存目录 (默认 data/raw_js)")
    parser.add_argument("--proxy", default="http://127.0.0.1:7897", help="本地代理地址 (设为 none 则直连)")

    args = parser.parse_args()
    proxy_val = None if args.proxy.lower() == "none" else args.proxy
    
    fetcher = ChunkFetcher(proxy=proxy_val)
    fetcher.fetch(args.base_url, args.chunk, Path(args.output_dir))
