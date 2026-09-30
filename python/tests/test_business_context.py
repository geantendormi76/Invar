"""
Phase 1 业务调用上下文恢复测试（business_context.py + extractor 集成）。

覆盖：
  ① 真实 minified chunk 中 giveRouter / giveRouterBatch / addAccount 三个入口的完整恢复；
  ② addAccount 同名 `n`（调用点之后的 moment 赋值）不被错误绑定；
  ③ minified source_line=1 下仍用字节偏移正确解析（不依赖 line）；
  ④ 重新赋值 last-writer-wins；
  ⑤ 跨函数作用域隔离（外层 n 不泄漏到内层回调）；
  ⑥ 非 object 取值 / 未声明标识符 → unresolved，不猜测、不崩溃；
  ⑦ property_identifier vs identifier 区分（对象键 / 声明 id）；
  ⑧ extractor 集成：endpoint.call_contexts 附带正确且不改变 EndpointIR 字段。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "python" / "packages" / "core" / "src"
sys.path.insert(0, str(SRC))

from tree_sitter import Parser, Language  # noqa: E402
import tree_sitter_javascript  # noqa: E402

from harness.business_context import CallContextResolver, _business_name, _resolve_object_literal, _nearest_function_node, _object_pairs  # noqa: E402
from harness.extractor import JSEndpointExtractor  # noqa: E402

CHUNK = ROOT / "tmp" / "raw_js" / "cloud.ikuai8.com" / "07a7ade6ba70ea6ecb4e_chunk-71e3ab88.af00cba6.js"


def _parse(code):
    lang = Language(tree_sitter_javascript.language())
    p = Parser()
    p.language = lang
    return p.parse(bytes(code, "utf-8"))


def _grant_calls_from_chunk():
    code = CHUNK.read_text(encoding="utf-8", errors="ignore")
    tree = _parse(code)
    out = []
    for c in _walk(tree.root_node):
        if c.type != "call_expression":
            continue
        args = c.child_by_field_name("arguments")
        if args is None:
            continue
        strs = [a.text.decode() for a in args.children if a.type in ("string", "template_string")]
        idfs = [a.text.decode() for a in args.children if a.type == "identifier"]
        if any("grant" in s for s in strs) and "n" in idfs:
            out.append((c, "n"))
    return code, out


def _walk(node):
    yield node
    for c in node.children:
        yield from _walk(c)


def _ctx_by_business(code, business):
    tree = _parse(code)
    for c in _walk(tree.root_node):
        if c.type != "call_expression":
            continue
        if _business_name(c) != business:
            continue
        args = c.child_by_field_name("arguments")
        idfs = [a for a in args.children if a.type == "identifier"]
        if not idfs:
            continue
        return CallContextResolver().resolve(c, idfs[0].text.decode("utf-8"))
    raise AssertionError(f"no grant call with business_name={business!r}")


def test_1_real_chunk_giveRouter_full_context():
    code, calls = _grant_calls_from_chunk()
    assert len(calls) == 3, f"expected 3 grant calls, got {len(calls)}"
    ctx = _ctx_by_business(code, "giveRouter")
    assert ctx.status == "resolved"
    assert ctx.business_name == "giveRouter"
    assert ctx.call_offset == 33650
    got = {f.name: f.value for f in ctx.params}
    assert got == {
        "account_code": "e.grantData.account_code",
        "gwids": "[e.grantData.gwid]",
        "perms": "e.grantData.selectedPerm",
        "remark": "e.grantData.remark",
    }, got


def test_2_real_chunk_giveRouterBatch():
    code, calls = _grant_calls_from_chunk()
    ctx = _ctx_by_business(code, "giveRouterBatch")
    assert ctx.status == "resolved"
    assert ctx.business_name == "giveRouterBatch"
    got = {f.name: f.value for f in ctx.params}
    assert got["account_code"] == "e.batchGrantData.account_code"
    assert got["gwids"] == "e.batchGrantData.gwids"
    assert got["perms"] == "e.batchGrantData.selectedPerm"


def test_3_real_chunk_addAccount_perms_empty_array():
    code, calls = _grant_calls_from_chunk()
    ctx = _ctx_by_business(code, "addAccount")
    assert ctx.status == "resolved"
    assert ctx.business_name == "addAccount"
    got = {f.name: f.value for f in ctx.params}
    assert got["perms"] == "[]", got
    # 取值种类必须标记为 array，而非被误判为 expression
    perms = next(f for f in ctx.params if f.name == "perms")
    assert perms.value_kind == "array"
    assert perms.value_byte == 34473


def test_4_addAccount_second_n_not_misbound():
    """addAccount 中调用点之后还有一次同名 `var n`（moment 赋值）；
    解析必须取调用点之前的 grant object，而非之后的 moment 对象。"""
    code, calls = _grant_calls_from_chunk()
    tree = _parse(code)
    target = None
    for c in _walk(tree.root_node):
        if c.type == "call_expression" and _business_name(c) == "addAccount":
            args = c.child_by_field_name("arguments")
            idfs = [a for a in args.children if a.type == "identifier"]
            if not idfs:
                continue
            target = (c, idfs[0].text.decode())
            break
    call_node, ident = target
    obj = _resolve_object_literal(call_node, ident)
    assert obj is not None and obj.type == "object"
    # grant object 的字段名含 account_code，且 gwids 取 e.editData.gwid（moment 对象不含这些）
    names = [k for k, _, _ in _object_pairs(obj)]
    assert "account_code" in names, names
    vals = {k: v for k, v, _ in _object_pairs(obj)}
    assert vals["gwids"] == "[e.editData.gwid]", vals


def test_5_minified_source_line_1_uses_byte_offset():
    """真实 chunk 的 endpoint.line==1（minified），但上下文按字节偏移恢复。"""
    ext = JSEndpointExtractor()
    endpoints = ext.parse_code(CHUNK.read_text(encoding="utf-8", errors="ignore"), "chunk.js")
    grant_eps = [e for e in endpoints if e.path == "/api/v3/delegate/grant"]
    assert grant_eps, "grant endpoint not extracted"
    for e in grant_eps:
        assert e.line == 1  # minified，line 恒为 1
        assert getattr(e, "call_contexts", None), "extractor must attach call_contexts"
        assert len(e.call_contexts) == 1
        assert e.call_contexts[0].status == "resolved"


def test_6_reassignment_last_writer_wins():
    """同一作用域内 `var n` 被多次赋值，取调用点前最后一次 object 赋值。"""
    code = (
        "var target = 1;\n"
        "obj.init({\n"
        "  handler: function() {\n"
        "    var n = {a: 1, b: 2};\n"
        "    n = {a: 9, b: 2};\n"
        "    e.$http.post('/api/x', n);\n"
        "  }\n"
        "});"
    )
    tree = _parse(code)
    call = None
    for c in _walk(tree.root_node):
        if c.type == "call_expression":
            args = c.child_by_field_name("arguments")
            idfs = [a for a in args.children if a.type == "identifier"]
            if idfs and idfs[0].text.decode() == "n":
                call = c
                break
    assert call is not None
    obj = _resolve_object_literal(call, "n")
    vals = {k: v for k, v, _ in _object_pairs(obj)}
    assert vals == {"a": "9", "b": "2"}, vals  # 最后一次赋值 {a:9,b:2}，不是 {a:1,b:2}


def test_7_cross_function_scope_isolation():
    """外层函数的 `var n` 不能泄漏进内层回调的调用点；内层用内层 n。"""
    code = (
        "function outer() {\n"
        "  var n = {outer: true};\n"
        "  return function inner() {\n"
        "    var n = {inner: true};\n"
        "    e.$http.post('/api/y', n);\n"
        "  };\n"
        "}"
    )
    tree = _parse(code)
    call = None
    for c in _walk(tree.root_node):
        if c.type == "call_expression":
            args = c.child_by_field_name("arguments")
            idfs = [a for a in args.children if a.type == "identifier"]
            if idfs and idfs[0].text.decode() == "n":
                call = c
                break
    assert call is not None
    scope = _nearest_function_node(call)
    assert scope.type == "function_expression"  # 内层回调，不是 outer
    obj = _resolve_object_literal(call, "n")
    vals = {k: v for k, v, _ in _object_pairs(obj)}
    assert vals == {"inner": "true"}, vals


def test_8_unresolved_when_identifier_not_declared_as_object():
    """标识符未声明 / 声明为非 object → unresolved，params 空，不崩溃、不猜测。"""
    # (a) 未声明
    code_a = "obj.init({ h: function() { e.$http.post('/api/a', n); } });"
    tree_a = _parse(code_a)
    call_a = next(c for c in _walk(tree_a.root_node)
                  if c.type == "call_expression"
                  and any(a.text.decode() == "n" for a in
                          (c.child_by_field_name("arguments") or []).children
                          if a.type == "identifier"))
    ctx_a = CallContextResolver().resolve(call_a, "n")
    assert ctx_a.status == "unresolved"
    assert ctx_a.params == []
    assert ctx_a.business_name == "h"

    # (b) 声明为非 object（函数调用）
    code_b = (
        "function f() {\n"
        "  var n = compute();\n"
        "  e.$http.post('/api/b', n);\n"
        "}"
    )
    tree_b = _parse(code_b)
    call_b = next(c for c in _walk(tree_b.root_node)
                  if c.type == "call_expression"
                  and any(a.text.decode() == "n" for a in
                          (c.child_by_field_name("arguments") or []).children
                          if a.type == "identifier"))
    ctx_b = CallContextResolver().resolve(call_b, "n")
    assert ctx_b.status == "unresolved"


def test_9_property_identifier_vs_identifier_distinct():
    """对象键是 property_identifier，声明 id 是 identifier；两者不能互换。"""
    code = "obj.m({ k: function() { var n = {p: 1}; e.$http.post('/api/z', n); } });"
    tree = _parse(code)
    # 取 INNER 的 post 调用（DFS 首个 call_expression 是外层 obj.m(...)，需跳过）
    call = None
    for c in _walk(tree.root_node):
        if c.type != "call_expression":
            continue
        args = c.child_by_field_name("arguments")
        strs = [a.text.decode() for a in args.children if a.type in ("string", "template_string")]
        idfs = [a.text.decode() for a in args.children if a.type == "identifier"]
        if any("/api/z" in s for s in strs) and "n" in idfs:
            call = c
            break
    assert call is not None
    # 业务名来自最近的 pair 键（property_identifier）；调用点在 k 函数体内，最近 pair 即 k
    assert _business_name(call) == "k"
    ctx = CallContextResolver().resolve(call, "n")
    assert ctx.status == "resolved"
    assert [f.name for f in ctx.params] == ["p"]


def test_10_extractor_integration_does_not_mutate_endpointir_fields():
    """集成：call_contexts 挂在实例属性上；EndpointIR 数据类字段集合不变。"""
    import dataclasses
    ext = JSEndpointExtractor()
    endpoints = ext.parse_code(CHUNK.read_text(encoding="utf-8", errors="ignore"), "chunk.js")
    grant_eps = [e for e in endpoints if e.path == "/api/v3/delegate/grant"]
    # 提取器层不做去重（去重在 ast_worker），同一 grant endpoint 有三个调用点 → 3 个原始 endpoint
    assert len(grant_eps) == 3, len(grant_eps)
    field_names = {f.name for f in dataclasses.fields(type(grant_eps[0]))}
    assert "call_contexts" not in field_names, "Phase 1 must NOT add field to EndpointIR"
    for e in grant_eps:
        assert getattr(e, "call_contexts", None) and e.call_contexts[0].status == "resolved"
