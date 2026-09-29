$bin = "C:\dev\bin\llama\llama-server.exe"
$model = "C:\Users\52484\.pi\agent\models\Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE.gguf"

$optimizedArgs = @(
    "-m", $model,

    # 1. 🚀 关键：唤醒模型内置的 MTPv2 原生投机头 (速度翻倍至 50+ 的核心)
    "--spec-type", "draft-mtp",     # 使用 GGUF 内置的 MTP 预测头
    "--spec-draft-n-max", "2",      # 每次向前投机推测 2 个 Token (MoE 下的最佳命中甜点位)
    "--spec-draft-p-min", "0.80",   # 投机置信度阈值，防止瞎猜降低质量

    # 2. MoE 专家感知卸载与 FlashAttention
    "-ngl", "99",
    "--n-cpu-moe", "24",            # 24 层专家进 32G 内存，注意力全在 12G 显存
    "-fa", "on",

    # 3. 上下文与批处理
    "-c", "160000",                  # 先以 170K 起步，为 MTP 投机头预留 ~2GB 动态演算显存
    "--cache-type-k", "q8_0",
    "--cache-type-v", "q8_0",
    "-b", "2048",
    "-ub", "1024",
    "--parallel", "1",

    # 4. CPU 线程调度 (针对 13600KF 锁定 8 个大核线程，防止小核拖慢)
    "-t", "8",

    # 5. Pi Agent 模版与思维链
    "--jinja",
    "--reasoning", "on",

    # 6. 网络契约
    "--host", "127.0.0.1",
    "--port", "8080",

    # 7. 代码与安全挖掘采样器
    "--temp", "0.6",
    "--top-p", "0.95",
    "--top-k", "20",
    "--min-p", "0.01",
    "--repeat-penalty", "1.0"
)

& $bin @optimizedArgs