"""
BusinessCallContext —— 业务调用上下文恢复（Phase 1，仅 extractor 侧）。

设计约束（与 Phase 1 范围严格对齐）：
  * 不修改 EndpointIR 契约：BusinessCallContext 是独立数据类，由 extractor 在解析
    call_expression 时**附带**到 endpoint.call_contexts（纯 Python 实例属性，
    不进 asdict()/Rust IPC 契约）。
  * 只处理"第二参量为标识符（如 `n`）"的调用点：恢复其 business_name + 内联对象字段。
  * 不做跨文件/跨作用域数据流、不做 CFG、不做 follow-up GET。
  * minified source_line=1 不影响：一律用 AST 节点的 start_byte 偏移做身份/顺序判定。

本 tree-sitter JS 语法的两个关键事实（已实测，决定实现正确性）：
  1. 对象字面量的键节点类型是 ``property_identifier``，不是 ``identifier``；
     变量声明的 id 才是 ``identifier``。混用会导致全部键解析为 None。
  2. ``variable_declarator`` 的 ``id`` 字段在本版本 tree-sitter 里
     ``child_by_field_name("id")`` 返回 None，必须用 ``named_children[0]`` 取标识符。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# property_identifier（对象键）+ identifier（变量声明 id）
_IDENT_TYPES = ("identifier", "property_identifier")


def _is_ident(node) -> bool:
    return node is not None and node.type in _IDENT_TYPES


def _walk(node):
    """深度优先 yields 节点自身及其全部后代（tree-sitter Node）。"""
    yield node
    for c in node.children:
        yield from _walk(c)


def _ancestors(node):
    """沿 parent 链向上：[node, parent, ..., root]。"""
    chain = []
    cur = node
    while cur is not None:
        chain.append(cur)
        cur = cur.parent
    return chain


def _nearest_function_node(call_node):
    """调用点最近的 function_expression / function_declaration / arrow_function 祖先。

    该节点即"本地变量可见作用域"。JS 中 var 为函数级可见，块级 if/for 不隔离作用域，
    因此作用域 = 该函数节点的整个函数体（含其内部所有 statement_block）。"""
    for anc in _ancestors(call_node):
        if anc.type in ("function_expression", "function_declaration", "arrow_function"):
            return anc
    return None


def _business_name(call_node):
    """沿祖先链向上取最近的 pair / object_property，其首个 named child 为标识符时返回文本。

    minified 里 ``methods:{ giveRouter: function(){...} }`` 的 giveRouter 即业务名；
    它把同一 endpoint 的多个业务入口彼此区分。无法识别时返回 None（不猜测）。"""
    for anc in _ancestors(call_node):
        if anc.type in ("pair", "object_property"):
            kids = anc.named_children
            if kids and _is_ident(kids[0]):
                return kids[0].text.decode("utf-8")
    return None


def _object_pairs(obj_node):
    """从 object 字面量提取 ``(name, value_text, value_byte)``，仅取 property_identifier 键的 pair。

    仅保留 ``property_identifier`` 键，跳过计算键 ``['computed-key']`` 与方法简写，
    避免把非字段内容误当 context-local field。"""
    out = []
    for ch in obj_node.children:
        if ch.type != "pair":
            continue
        kids = ch.named_children
        key = kids[0] if kids else None
        if not _is_ident(key):
            continue
        val = ch.child_by_field_name("value")
        out.append((
            key.text.decode("utf-8"),
            val.text.decode("utf-8") if val is not None else None,
            val.start_byte if val is not None else None,
        ))
    return out


def _resolve_object_literal(call_node, target):
    """在调用点最近函数作用域内，向前线性扫描 var/let/const，返回"最近一次"声明且
    ``start_byte < 调用点 start_byte``、值类型为 object 的声明之 object 节点；否则 None。

    语义（last-writer-wins，覆盖声明与重新赋值两条路径）：
      * 只扫该函数节点的 statement_block（= 本地可见作用域），不跨函数；
      * 同时收集两种绑定：``var/let/const`` 声明（variable_declarator 的 value）与
        重新赋值 ``n = {...}``（assignment_expression 的 right）；取两者中
        ``start_byte < 调用点`` 且字节最大者，即 JS 调用前 n 的最终取值；
      * 绑定值非 object（如重新赋值为函数调用 / 成员访问）直接跳过；
      * ``let/const`` 在本 tree-sitter 中同为 ``variable_declaration`` 节点，天然覆盖。
    """
    scope = _nearest_function_node(call_node)
    if scope is None:
        return None
    call_offset = call_node.start_byte
    best = None  # (byte, node)
    for block in (n for n in _walk(scope) if n.type == "statement_block"):
        for node in _walk(block):
            val = None
            if node.type == "variable_declaration":
                for d in node.named_children:
                    if d.type != "variable_declarator":
                        continue
                    cid = d.named_children[0] if d.named_children else None
                    if not _is_ident(cid) or cid.text.decode("utf-8") != target:
                        continue
                    v = d.child_by_field_name("value")
                    if v is not None and v.type == "object":
                        val = v
            elif node.type == "assignment_expression":
                lhs = node.child_by_field_name("left")
                rhs = node.child_by_field_name("right")
                if (_is_ident(lhs) and lhs.text.decode("utf-8") == target
                        and rhs is not None and rhs.type == "object"):
                    val = rhs
            else:
                continue
            if val is not None and val.start_byte < call_offset and (best is None or val.start_byte > best[0]):
                best = (val.start_byte, val)
    return best[1] if best is not None else None


def _kind_of(text) -> str:
    if text is None:
        return "unknown"
    t = text.strip()
    if not t:
        return "empty"
    if t[0] == "{":
        return "inline_object"
    if t[0] == "[":
        return "array"
    if t[0] in ("'", '"', "`"):
        return "string_literal"
    if t[0].isdigit() or t.startswith("-"):
        return "number_literal"
    return "expression"


@dataclass
class ObjectField:
    """context-local 字段：字段名 + 取值文本（字面量原文）+ 取值节点字节偏移 + 取值种类。"""
    name: str
    value: Optional[str]
    value_byte: Optional[int]
    value_kind: str = "expression"


@dataclass
class BusinessCallContext:
    """一次业务调用点的上下文快照。

    status:
      resolved      —— 成功恢复内联对象字段
      unresolved    —— 第二参量标识符在本地作用域无法解析为 object（不猜测、不丢路径）
    """
    business_name: Optional[str]
    params: List[ObjectField] = field(default_factory=list)
    status: str = "resolved"
    call_offset: Optional[int] = None
    raw_identifier: Optional[str] = None


class CallContextResolver:
    """Phase 1 上下文恢复器：仅处理"第二参量为标识符"的调用点。

    resolve(call_node, target)：
      * target —— 第二参量标识符名（由 extractor 传入，避免"首个 identifier 不一定是 body"的歧义）；
      * 无法解析为 object → status="unresolved"，params 为空，绝不返回伪造字段。
    """

    def resolve(self, call_node, target):
        args = call_node.child_by_field_name("arguments")
        business = _business_name(call_node)
        obj = _resolve_object_literal(call_node, target)
        if obj is None:
            return BusinessCallContext(
                business_name=business,
                params=[],
                status="unresolved",
                call_offset=call_node.start_byte,
                raw_identifier=target,
            )
        fields = [
            ObjectField(name=name, value=val_text, value_byte=val_byte, value_kind=_kind_of(val_text))
            for name, val_text, val_byte in _object_pairs(obj)
        ]
        return BusinessCallContext(
            business_name=business,
            params=fields,
            status="resolved",
            call_offset=call_node.start_byte,
            raw_identifier=target,
        )
