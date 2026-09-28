$bin = "C:\dev\bin\llama\llama-server.exe"
$modelBase = "C:\Users\52484\.pi\agent\models\Ornith-1.5-9B-Abliterated-IQ3_M"

if (Test-Path "$modelBase.gguf") {
    $model = "$modelBase.gguf"
} elseif (Test-Path $modelBase) {
    $model = $modelBase
} else {
    Write-Error "❌ 未找到 GGUF 模型文件: $modelBase"
    exit 1
}

if (-not (Test-Path $bin)) {
    Write-Error "❌ 未找到 llama-server 执行文件: $bin"
    exit 1
}

$argsList = @(
    "-m", $model,
    "--alias", "Ornith-1.5-9B-Abliterated-IQ3_M",
    "-ngl", "99",
    "-c", "81920",
    "-fa", "on",
    "--jinja",
    "--cache-type-k", "q4_0",
    "--cache-type-v", "q4_0",
    "-t", "6",
    "-tb", "6",
    "-b", "2048",
    "-ub", "512",
    "--parallel", "1",
    "--host", "127.0.0.1", 
    "--port", "8080",

    "--temp", "0.3",
    "--top-p", "0.90",
    "--top-k", "40",
    "--min-p", "0.05",
    "--repeat-penalty", "1.02"
)

& $bin @argsList