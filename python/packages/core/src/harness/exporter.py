import json
from pathlib import Path
from typing import List, Union
from .models import EndpointIR

class EndpointExporter:
    """
    Invar 标准数据契约序列化导出器
    全面兼容裸列表 JSON 与流水线战报字典 JSON
    """
    @staticmethod
    def to_json_file(endpoints: List[EndpointIR], output_path: Union[str, Path]) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [e.to_dict() for e in endpoints]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    @staticmethod
    def from_json_file(input_path: Union[str, Path]) -> List[EndpointIR]:
        path = Path(input_path)
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 智能解构多态容器外壳
        raw_list = []
        if isinstance(data, dict):
            if "endpoints" in data and isinstance(data["endpoints"], list):
                raw_list = data["endpoints"]
            else:
                raw_list = []
        elif isinstance(data, list):
            raw_list = data

        return [EndpointIR.from_dict(item) for item in raw_list if isinstance(item, dict)]
