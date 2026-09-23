import sys
from pathlib import Path
SRC = Path(r"C:\dev\Invar\python\packages\core\src")
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import json
from harness.sandbox_executor import AdaptiveSandboxExecutor
from harness.research_adapter import ResearchTaskAdapter

tasks_file = Path(r"C:\dev\Invar\artifacts\reports\targeted_research_tasks_78.json")
tasks = json.loads(tasks_file.read_text(encoding='utf-8'))['tasks']
p0_tasks = [t for t in tasks if t.get('priority') == 'P0']
executor = AdaptiveSandboxExecutor()

print(f'=== P0 任务 URL 解析验证（前 3 个）===')
for idx, t in enumerate(p0_tasks[:3], 1):
    ep = ResearchTaskAdapter.task_to_endpoint(t)
    url = executor._build_url(ep)
    print(f'[{idx}] {ep.method} {ep.path} -> {url}')

print('\n=== 全量 P0 任务 URL 解析（全部）===')
for idx, t in enumerate(p0_tasks, 1):
    ep = ResearchTaskAdapter.task_to_endpoint(t)
    url = executor._build_url(ep)
    print(f'[{idx:02d}] {ep.method} {ep.path} -> {url}')
