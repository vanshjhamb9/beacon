from time import perf_counter

from lead_enrichment import EnrichmentPipeline
from lead_enrichment.connectors.dns_mx import DnsMxConnector
from lead_enrichment.connectors.website import WebsiteConnector
from tests.lead_enrichment.test_enrichment_pipeline import make_input


def test_enrichment_pipeline_processes_batch_quickly() -> None:
    pipeline = EnrichmentPipeline(
        website=WebsiteConnector(enabled=False),
        dns=DnsMxConnector(enabled=False),
    )
    inputs = [make_input() for _ in range(50)]

    started = perf_counter()
    results = [pipeline.process(item) for item in inputs]
    elapsed_ms = (perf_counter() - started) * 1000

    assert len(results) == 50
    assert elapsed_ms < 1000
    assert all(result.enrichment_confidence.overall_enrichment_confidence >= 0 for result in results)
