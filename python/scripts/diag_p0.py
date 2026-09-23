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

print(f'=== 12 个 P0 任务的 URL 解析与源文件清单 ===')
for idx, t in enumerate(p0_tasks, 1):
    ep = ResearchTaskAdapter.task_to_endpoint(t)
    url = executor._build_url(ep)
    src = Path(t.get('source_file', '')).parts[-2:]
    src_str = '/'.join(src) if src else 'N/A'
    print(f'[{idx:02d}] {ep.method:<6} {ep.path:<30} -> {url} (src: {src_str})')

print('\n=== 探测第 1 个任务并打印底层证据快照 ===')
target_ep = ResearchTaskAdapter.task_to_endpoint(p0_tasks[0])
res = executor.probe_endpoint_with_research(target_ep)
print(f'URL: {res.evidence.request.url}')
print(f'Finding Type: {res.evidence.finding_type}')
print(f'HTTP Status: {res.evidence.response.status_code}')
print(f'Attempts: {len(res.research_case.attempts)}')
print(f'Notes / Error: {res.evidence.notes}')
