from pathlib import Path
from typing import List, Optional, Union
from tree_sitter import Parser, Language
import tree_sitter_javascript
from .models import EndpointIR

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}

class JSEndpointExtractor:
    """
    Invar 确定性脚手架：Tree-sitter AST 接口与参数契约深度提炼引擎
    """
    def __init__(self):
        self.language = Language(tree_sitter_javascript.language())
        self.parser = Parser()
        self.parser.language = self.language

    def parse_code(self, code: str, file_path: str = "inline.js") -> List[EndpointIR]:
        tree = self.parser.parse(bytes(code, "utf-8"))
        endpoints: List[EndpointIR] = []
        self._walk(tree.root_node, file_path, endpoints)
        return endpoints

    def parse_file(self, file_path: Union[str, Path]) -> List[EndpointIR]:
        path = Path(file_path)
        if not path.exists():
            return []
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []
        return self.parse_code(code, str(path))

    def _walk(self, node, file_path: str, endpoints: List[EndpointIR]):
        if node.type == "call_expression":
            endpoint = self._extract_call_signature(node, file_path)
            if endpoint:
                endpoints.append(endpoint)
        for child in node.children:
            self._walk(child, file_path, endpoints)

    def _extract_call_signature(self, node, file_path: str) -> Optional[EndpointIR]:
        func_node = node.child_by_field_name("function")
        args_node = node.child_by_field_name("arguments")
        if not func_node or not args_node:
            return None

        line = node.start_point[0] + 1
        method = "GET"
        path = ""
        call_sig = func_node.text.decode("utf-8")
        params: List[str] = []

        # 1. 普通标识符调用: request(...) 或 fetch(...)
        if func_node.type == "identifier":
            func_name = func_node.text.decode("utf-8")
            if func_name == "request":
                for child in args_node.children:
                    if child.type == "object":
                        for prop in child.children:
                            if prop.type == "pair":
                                key_node = prop.child_by_field_name("key")
                                val_node = prop.child_by_field_name("value")
                                if key_node:
                                    k = key_node.text.decode("utf-8").strip("'\"`")
                                    if k == "url" and val_node:
                                        path = val_node.text.decode("utf-8").strip("'\"`")
                                    elif k == "method" and val_node:
                                        method = val_node.text.decode("utf-8").strip("'\"`").upper()
                                    else:
                                        params.append(k)
                    elif child.type in ["string", "template_string"]:
                        path = child.text.decode("utf-8").strip("'\"`")

            elif func_name == "fetch":
                for child in args_node.children:
                    if child.type in ["string", "template_string"] and not path:
                        path = child.text.decode("utf-8").strip("'\"`")
                    elif child.type == "object":
                        for prop in child.children:
                            if prop.type == "pair":
                                key_node = prop.child_by_field_name("key")
                                val_node = prop.child_by_field_name("value")
                                if key_node:
                                    k = key_node.text.decode("utf-8").strip("'\"`")
                                    if k == "method" and val_node:
                                        method = val_node.text.decode("utf-8").strip("'\"`").upper()
                                    else:
                                        params.append(k)

        # 2. 成员方法调用: axios.get / axios.post / api.delete / client.request
        elif func_node.type == "member_expression":
            prop_node = func_node.child_by_field_name("property")
            if prop_node:
                prop_name = prop_node.text.decode("utf-8").upper()
                if prop_name in HTTP_METHODS:
                    method = prop_name
                elif "POST" in call_sig.upper():
                    method = "POST"
                elif "PUT" in call_sig.upper():
                    method = "PUT"
                elif "DELETE" in call_sig.upper():
                    method = "DELETE"

                for arg in args_node.children:
                    if arg.type in ["string", "template_string"] and not path:
                        path = arg.text.decode("utf-8").strip("'\"`")
                    elif arg.type == "object":
                        for prop in arg.children:
                            if prop.type == "pair":
                                key_node = prop.child_by_field_name("key")
                                val_node = prop.child_by_field_name("value")
                                if key_node:
                                    k = key_node.text.decode("utf-8").strip("'\"`")
                                    if k == "url" and val_node:
                                        path = val_node.text.decode("utf-8").strip("'\"`")
                                    elif k == "method" and val_node:
                                        method = val_node.text.decode("utf-8").strip("'\"`").upper()
                                    else:
                                        params.append(k)

        if path and (path.startswith("/") or "http" in path or "/" in path):
            is_dynamic = "{" in path or "}" in path or "$" in path
            return EndpointIR(
                method=method,
                path=path,
                source_file=file_path,
                line=line,
                is_dynamic=is_dynamic,
                extracted_params=params,
                call_signature=call_sig,
                tags=[]
            )
        return None
