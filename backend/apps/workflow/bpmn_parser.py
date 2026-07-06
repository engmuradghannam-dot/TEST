"""BPMN 2.0 XML parser.

Parses .bpmn files (OMG BPMN 2.0 XML) into the internal workflow spec
consumed by the state machine: start/end events, user/service tasks,
exclusive & parallel gateways, sequence flows with condition expressions.
"""
import xml.etree.ElementTree as ET

BPMN_NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}

NODE_TAGS = {
    "startEvent": "start",
    "endEvent": "end",
    "userTask": "user_task",
    "serviceTask": "service_task",
    "task": "task",
    "exclusiveGateway": "exclusive_gateway",
    "parallelGateway": "parallel_gateway",
}


class BPMNParseError(ValueError):
    pass


def parse_bpmn(xml_content: str) -> dict:
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        raise BPMNParseError(f"Invalid XML: {exc}") from exc

    process = root.find(".//bpmn:process", BPMN_NS)
    if process is None:
        raise BPMNParseError("No <process> element found")

    nodes, flows = {}, []
    for tag, node_type in NODE_TAGS.items():
        for el in process.findall(f"bpmn:{tag}", BPMN_NS):
            nodes[el.get("id")] = {
                "id": el.get("id"),
                "name": el.get("name", el.get("id")),
                "type": node_type,
            }

    for el in process.findall("bpmn:sequenceFlow", BPMN_NS):
        cond_el = el.find("bpmn:conditionExpression", BPMN_NS)
        flows.append({
            "id": el.get("id"),
            "source": el.get("sourceRef"),
            "target": el.get("targetRef"),
            "condition": (cond_el.text or "").strip() if cond_el is not None else None,
        })

    _validate(nodes, flows)
    return {
        "process_id": process.get("id"),
        "name": process.get("name", process.get("id")),
        "nodes": list(nodes.values()),
        "flows": flows,
    }


def _validate(nodes: dict, flows: list):
    starts = [n for n in nodes.values() if n["type"] == "start"]
    ends = [n for n in nodes.values() if n["type"] == "end"]
    if len(starts) != 1:
        raise BPMNParseError(f"Expected exactly 1 startEvent, found {len(starts)}")
    if not ends:
        raise BPMNParseError("No endEvent found")
    ids = set(nodes)
    for f in flows:
        if f["source"] not in ids or f["target"] not in ids:
            raise BPMNParseError(f"sequenceFlow {f['id']} references unknown node")
    # reachability from start
    adj = {}
    for f in flows:
        adj.setdefault(f["source"], []).append(f["target"])
    seen, stack = set(), [starts[0]["id"]]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(adj.get(cur, []))
    unreachable = ids - seen
    if unreachable:
        raise BPMNParseError(f"Unreachable nodes: {sorted(unreachable)}")
