#requires -Version 5.1
<#
.SYNOPSIS
    Invar 当前阶段“整理与收口”脚本。

.DESCRIPTION
    目标：
    1. 保护当前工作区，先生成收口前快照；
    2. 删除本次误加入的 Agent/LLM 实验文件；
    3. 仅在 scan_pipeline.py 的差异全部属于已知 Agent 改动时，恢复该文件到 HEAD；
    4. 不移动核心源码，不改 Rust/Python 架构，不删除研究数据；
    5. 用项目现有 uv 环境执行测试；
    6. 重新执行静态扫描，验证基线。

    重要：
    - 本脚本只操作 C:\dev\Invar 内的指定文件。
    - 如果 scan_pipeline.py 存在无法确认的其他本地修改，脚本会停止，不会覆盖。
    - 本脚本不会执行 git clean、不会删除 data、不会删除 tmp。
#>

[CmdletBinding()]
param(
    [string]$Root = 'C:\dev\Invar',
    [switch]$SkipTests,
    [switch]$SkipBaseline
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Step([string]$Message) {
    Write-Host "`n==================================================" -ForegroundColor DarkGray
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor DarkGray
}

function Assert-Path([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "路径不存在：$Path"
    }
}

function Read-Text([string]$Path) {
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

function Get-RelativeGitStatus {
    $output = @(git -C $Root status --short)
    return $output
}

Assert-Path $Root

Write-Step "1/6 检查 Git 与项目边界"

$gitDir = Join-Path $Root '.git'
Assert-Path $gitDir

$scanPipeline = Join-Path $Root 'scripts\pipeline\scan_pipeline.py'
$agentDir = Join-Path $Root 'src-tauri\python\src\agent'
$modelProvider = Join-Path $agentDir 'model_provider.py'
$researchAgent = Join-Path $agentDir 'research_agent.py'

Assert-Path $scanPipeline
Assert-Path $agentDir

$status = @(git -C $Root status --short)
Write-Host "当前工作区状态："
if ($status.Count -eq 0) {
    Write-Host "  [干净]" -ForegroundColor Green
} else {
    $status | ForEach-Object { Write-Host "  $_" }
}

Write-Step "2/6 创建收口前快照"

$snapshotDir = Join-Path $Root ("tmp\closure_snapshot_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $snapshotDir -Force | Out-Null

$snapshotStatus = Join-Path $snapshotDir 'git_status.txt'
$snapshotDiff = Join-Path $snapshotDir 'git_diff.patch'
$snapshotDiffStat = Join-Path $snapshotDir 'git_diff_stat.txt'

git -C $Root status --short | Out-File -LiteralPath $snapshotStatus -Encoding utf8
git -C $Root diff -- scripts/pipeline/scan_pipeline.py | Out-File -LiteralPath $snapshotDiff -Encoding utf8
git -C $Root diff --stat | Out-File -LiteralPath $snapshotDiffStat -Encoding utf8

Copy-Item -LiteralPath $scanPipeline `
    -Destination (Join-Path $snapshotDir 'scan_pipeline.py.before') `
    -Force

Write-Host "快照目录：$snapshotDir" -ForegroundColor Green

Write-Step "3/6 删除错误的 Agent/LLM 实验文件"

$deleted = @()

foreach ($path in @($modelProvider, $researchAgent)) {
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Force
        $deleted += $path
        Write-Host "[删除] $path" -ForegroundColor Yellow
    } else {
        Write-Host "[已不存在] $path"
    }
}

Write-Step "4/6 精确回滚 scan_pipeline.py"

$diff = git -C $Root diff -- scripts/pipeline/scan_pipeline.py

# 允许的变化：
# - --agent
# - --agent-max-candidates
# - 与上述两个参数直接相关的变量/分支/导入
#
# 如果发现其他修改，停止，不覆盖用户文件。
$forbiddenMarkers = @(
    'model_provider',
    'research_agent'
)

foreach ($marker in $forbiddenMarkers) {
    if ($diff -match [regex]::Escape($marker)) {
        Write-Host "检测到已知错误 Agent 代码：$marker" -ForegroundColor Yellow
    }
}

$agentMarkerPresent = (
    ($diff -match '--agent') -or
    ($diff -match 'agent-max-candidates') -or
    ($diff -match 'research_agent') -or
    ($diff -match 'model_provider')
)

if (-not $agentMarkerPresent) {
    Write-Host "scan_pipeline.py 没有检测到本次已知 Agent 改动，保持原文件不动。" -ForegroundColor Green
} else {
    # 先只允许 diff 行涉及本次已知 Agent 改动关键词。
    # 任何看不懂的新增/删除上下文都停止，避免误覆盖。
    $changedLines = @(
        $diff -split "`r?`n" |
        Where-Object {
            ($_ -match '^\+[^+]') -or ($_ -match '^\-[^-]')
        }
    )

    $unexpected = @(
        $changedLines |
        Where-Object {
            $line = $_
            $line -notmatch '--agent(?:\s|["''-]|$)' -and
            $line -notmatch 'agent-max-candidates' -and
            $line -notmatch 'research_agent' -and
            $line -notmatch 'model_provider' -and
            $line -notmatch 'agent_candidates' -and
            $line -notmatch 'research_agent\.py' -and
            $line -notmatch 'model_provider\.py'
        }
    )

    if ($unexpected.Count -gt 0) {
        $unexpectedText = $unexpected -join "`n"
        throw @"
scan_pipeline.py 存在无法安全判定为本次 Agent 实验的其他修改，脚本已停止。
未覆盖任何 scan_pipeline.py 内容。

请检查：
$snapshotDiff

疑似其他修改：
$unexpectedText
"@
    }

    git -C $Root checkout -- scripts/pipeline/scan_pipeline.py
    Write-Host "[回滚] scripts/pipeline/scan_pipeline.py -> HEAD" -ForegroundColor Yellow
}

# 删除可能变成空目录的 __pycache__ 不在本次操作范围内，避免扩大影响。

Write-Step "5/6 收口后结构检查"

$mustExist = @(
    (Join-Path $Root 'scripts\asset\ingest_katana.py'),
    (Join-Path $Root 'scripts\asset\normalize_katana.py'),
    (Join-Path $Root 'scripts\asset\download_javascript.py'),
    (Join-Path $Root 'scripts\pipeline\scan_pipeline.py'),
    (Join-Path $Root 'scripts\pipeline\fetch_chunk.py'),
    (Join-Path $Root 'src-tauri\python\src\agent\hypothesis_engine.py')
)

foreach ($path in $mustExist) {
    Assert-Path $path
}

foreach ($path in @($modelProvider, $researchAgent)) {
    if (Test-Path -LiteralPath $path) {
        throw "收口失败：错误实验文件仍存在：$path"
    }
}

$scanAfter = Read-Text $scanPipeline

# 注意：scan_pipeline.py 正常包含 `from agent.risk_engine import RiskEngine`，
# 因此不能用裸 `agent` 关键词判断是否仍残留错误实验代码。
$forbiddenScanMarkers = @(
    '--agent',
    'agent-max-candidates',
    'research_agent',
    'model_provider'
)

$remainingMarkers = @(
    $forbiddenScanMarkers |
    Where-Object { $scanAfter -match [regex]::Escape($_) }
)

if ($remainingMarkers.Count -gt 0) {
    throw "收口失败：scan_pipeline.py 仍包含 Agent 实验接口：$($remainingMarkers -join ', ')"
}

Write-Host "[OK] 目录边界与关键文件检查通过。" -ForegroundColor Green

$agentExperimentalFiles = @($modelProvider, $researchAgent) |
    Where-Object { Test-Path -LiteralPath $_ }

if ($agentExperimentalFiles.Count -gt 0) {
    throw "收口失败：以下实验文件仍存在：$($agentExperimentalFiles -join '; ')"
}

Write-Host "`n当前收口后的 Git 状态："
git -C $Root status --short

Write-Step "6/6 基线验证"

if (-not $SkipTests) {
    Write-Host "[测试] Python pytest" -ForegroundColor Cyan

    & uv run `
        --project "$Root\src-tauri\python" `
        --python 3.11 `
        pytest

    if ($LASTEXITCODE -ne 0) {
        throw "pytest 失败，收口基线未通过。"
    }

    Write-Host "[OK] pytest 通过。" -ForegroundColor Green
} else {
    Write-Host "[跳过] pytest" -ForegroundColor DarkYellow
}

if (-not $SkipBaseline) {
    $rawJs = Join-Path $Root 'tmp\raw_js'
    $baselineReport = Join-Path $Root 'tmp\ikuai8_endpoints_report.json'

    Assert-Path $rawJs

    Write-Host "[基线] 运行静态扫描" -ForegroundColor Cyan

    & uv run `
        --project "$Root\src-tauri\python" `
        --python 3.11 `
        python "$scanPipeline" `
        "$rawJs" `
        -o "$baselineReport"

    if ($LASTEXITCODE -ne 0) {
        throw "静态扫描失败，基线未通过。"
    }

    Assert-Path $baselineReport
    Write-Host "[OK] 静态扫描完成：$baselineReport" -ForegroundColor Green

    try {
        $report = Get-Content -LiteralPath $baselineReport -Raw -Encoding UTF8 | ConvertFrom-Json

        $endpointCount = @($report.endpoints).Count
        $evidenceCount = @($report.evidences).Count

        Write-Host "  endpoints  = $endpointCount"
        Write-Host "  evidences  = $evidenceCount"

        if ($null -ne $report.summary) {
            Write-Host "  summary："
            $report.summary | ConvertTo-Json -Depth 5
        }
    }
    catch {
        Write-Host "[警告] 报告已生成，但无法自动解析 summary：$($_.Exception.Message)" -ForegroundColor DarkYellow
    }
} else {
    Write-Host "[跳过] 静态扫描基线" -ForegroundColor DarkYellow
}

Write-Step "收口完成"

Write-Host "收口前快照：" -ForegroundColor White
Write-Host "  $snapshotDir"

Write-Host "`n最终工作区状态：" -ForegroundColor White
$finalStatus = @(git -C $Root status --short)
if ($finalStatus.Count -eq 0) {
    Write-Host "  [干净]" -ForegroundColor Green
} else {
    $finalStatus | ForEach-Object { Write-Host "  $_" }
}

Write-Host @"

当前阶段规则：
  1. 不再向 Invar 内部加入 Agent/LLM Provider。
  2. 不移动核心 Python/Rust 目录。
  3. 不删除 data/ 与 tmp/ 研究数据。
  4. 下一阶段从 Tool Contract Layer 开始。
"@
