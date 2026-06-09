from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import settings
from app.schemas import ConferenceSeed

DEFAULT_KEYWORD_RULES: dict[str, dict[str, list[str]]] = {
    "network": {
        "datacenter": ["datacenter", "data center", "rdma", "congestion", "traffic control"],
        "wireless": ["wireless", "cellular", "wifi", "wi-fi", "5g", "6g"],
        "measurement": ["measurement", "trace", "telemetry", "internet measurement"],
        "routing": ["routing", "bgp", "traffic engineering"],
    },
    "architecture": {
        "cpu": ["cpu", "processor", "pipeline", "branch prediction"],
        "memory": ["memory", "cache", "dram", "coherence"],
        "accelerator": ["accelerator", "gpu", "tpu", "fpga", "asic"],
        "storage": ["storage", "ssd", "filesystem", "file system", "nvme"],
        "systems": ["kernel", "virtualization", "serverless", "scheduler"],
    },
    "ai": {
        "machine_learning": ["machine learning", "optimization", "foundation model"],
        "deep_learning": ["deep learning", "neural network", "transformer"],
        "computer_vision": ["vision", "image", "video", "segmentation", "diffusion"],
        "natural_language_processing": ["language", "translation", "summarization", "llm"],
        "reinforcement_learning": ["reinforcement learning", "policy", "reward", "agent"],
        "graph_ml": ["graph neural network", "gnn", "graph learning"],
        "multimodal": ["multimodal", "vision-language", "audio-language"],
    },
}


@lru_cache
def load_keyword_rules() -> dict[str, dict[str, list[str]]]:
    path = Path(settings.taxonomy_config_path)
    if not path.exists():
        return DEFAULT_KEYWORD_RULES
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload.get("tags") or DEFAULT_KEYWORD_RULES


def classify_domain_by_conference(conference: ConferenceSeed) -> str:
    return conference.domain


def infer_subtopics(domain: str, texts: Iterable[str | None]) -> list[tuple[str, float, str]]:
    haystack = " ".join(text or "" for text in texts).lower()
    results: list[tuple[str, float, str]] = []
    for subtopic, keywords in load_keyword_rules().get(domain, {}).items():
        matched = [keyword for keyword in keywords if keyword.lower() in haystack]
        if matched:
            score = min(1.0, 0.35 + 0.15 * len(matched))
            results.append((subtopic, score, "keyword_rule"))
    return sorted(results, key=lambda item: item[1], reverse=True)

