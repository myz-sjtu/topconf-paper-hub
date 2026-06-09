from app.adapters.acm_dl import ACMDLAdapter
from app.adapters.base import RawPaperRecord, SourceAdapter
from app.adapters.cvf import CVFAdapter
from app.adapters.dblp import DBLPAdapter
from app.adapters.openalex import OpenAlexAdapter
from app.adapters.openreview import OpenReviewAdapter
from app.adapters.usenix import USENIXAdapter

ADAPTERS: dict[str, type[SourceAdapter]] = {
    "acm_dl": ACMDLAdapter,
    "cvf": CVFAdapter,
    "dblp": DBLPAdapter,
    "openalex": OpenAlexAdapter,
    "openreview": OpenReviewAdapter,
    "usenix": USENIXAdapter,
}


def get_adapter(source_type: str) -> SourceAdapter | None:
    adapter_cls = ADAPTERS.get(source_type)
    return adapter_cls() if adapter_cls else None


__all__ = ["ADAPTERS", "RawPaperRecord", "SourceAdapter", "get_adapter"]
