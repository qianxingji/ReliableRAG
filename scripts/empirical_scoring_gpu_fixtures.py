"""Prospectively fixed invented inputs for native scoring GPU compatibility."""
from scripts.empirical_scoring_fixtures import invented_trace


def semantic_traces():
    traces = [invented_trace(i, "bm25") for i in range(11)]
    for t in traces:
        t.pop("answer_semantic_agreement")
    traces[0]["a0"] = traces[0]["a1"] = ""
    traces[1]["a1"] = traces[1]["a0"]
    traces[2]["a1"] = "invented paper cog " * 800
    return traces


def likelihood_traces():
    short = invented_trace(100, "bm25")
    long = invented_trace(101, "dense")
    long["question"] = "invented paper cog " * 10000 + "What color is the invented cog?"
    return short, long


def gbv_traces():
    short = invented_trace(200, "bm25")
    long = invented_trace(201, "dense")
    long["E0"][0]["text"] = "The invented paper cog is silver. " * 300
    long["E1"][0]["text"] = long["E0"][0]["text"]
    failure = invented_trace(202, "hybrid")
    failure["a1"] = "invented blue paper cog " * 1000
    return short, long, failure
