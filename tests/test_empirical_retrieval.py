"""Invented corpus and numeric fixtures only; no neural model load or fit."""
from pathlib import Path
import unittest
import numpy as np

from scripts.empirical_retrieval_io import native_retrieval, independent_arithmetic


class EmpiricalRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper, cls.native, _ = native_retrieval(Path("E:/paper/ReliableRAG"))
        cls.independent = independent_arithmetic(Path("E:/paper/ReliableRAG"))

    def fixture(self):
        docs = [self.native.IndexedDocument.from_document("hotpotqa", self.native.Document(title, tuple(sentences)))
                for title, sentences in [("Toy A", ["blue blue cog"]), ("Toy B", ["blue wheel"]), ("Toy C", ["paper moon"])] ]
        corpus = self.native.Corpus.from_documents(docs)
        rows = [dict(id=d.id, dataset=d.dataset, title=d.title, sentences=list(d.sentences), content_hash=d.content_hash) for d in docs]
        return corpus, rows

    def test_bm25_structure_and_all_scores(self):
        corpus, rows = self.fixture()
        index = self.native.FastBM25Index(corpus, self.native.BM25Config(k1=1.5, b=.75, lowercase=True, token_pattern=r"(?u)\b\w+\b"))
        structure = self.independent.independent_structure(rows)
        self.assertEqual(self.wrapper.bm25_payload(index), structure)
        class Backend:
            dimension = 2
            def encode_queries(self, texts): return np.array([[1, 0]], dtype=np.float32)
        router = self.wrapper.bind_router(self.native, "hotpotqa", corpus, Backend(), np.array([[1,0],[0,1],[.5,.5]], dtype=np.float32), index,
            dict(hybrid=dict(rrf_k=60, component_depth=100)))
        for query in ("blue", "missing", "blue blue"):
            ranked = router.rank(query, "bm25", 3)
            actual = [dict(document_id=r.document_id, rank=r.rank, score=float(r.score)) for r in ranked]
            expected = self.independent.ordered_entries(self.independent.bm_scores(query, structure, {x["term"]:x for x in structure["terms"]}), [r["id"] for r in rows], 3)
            self.assertEqual(actual, expected)
        with self.assertRaises(ValueError): router.rank("", "bm25", 3)
        dense = [dict(document_id=r.document_id, rank=r.rank, score=float(r.score)) for r in router.rank("blue", "dense", 3)]
        bm = [dict(document_id=r.document_id, rank=r.rank, score=float(r.score)) for r in router.rank("blue", "bm25", 3)]
        hybrid = [dict(document_id=r.document_id, rank=r.rank, score=float(r.score)) for r in router.rank("blue", "hybrid", 3)]
        self.assertEqual(hybrid, self.independent.independent_rrf(bm, dense, depth=3))

    def test_dense_ties_follow_pool_order(self):
        scores = np.array([.5, .8, .8, 0], dtype=np.float32)
        ranked = self.independent.ordered_entries(scores, ["z", "b", "a", "x"], 4)
        self.assertEqual([r["document_id"] for r in ranked], ["b", "a", "z", "x"])

    def test_rrf_first_seen_order_and_top_binding(self):
        first = [dict(document_id="z", rank=1, score=1.0), dict(document_id="a", rank=2, score=.5)]
        second = [dict(document_id="a", rank=1, score=1.0), dict(document_id="z", rank=2, score=.5)]
        ranked = self.independent.independent_rrf(first, second, depth=2)
        self.assertEqual([r["document_id"] for r in ranked], ["z", "a"])
        self.assertEqual(ranked[0]["score"], ranked[1]["score"])

    def test_malformed_array_and_foreign_rank_rejected(self):
        with self.assertRaises(RuntimeError): self.independent.validate_array(np.zeros((1,768), dtype=np.float32), 1)
        value = dict(dataset="hotpotqa", sample_id="toy", retriever="dense", ranking=[dict(document_id="foreign", rank=1, score=1.0)])
        with self.assertRaises(RuntimeError): self.independent.validate_rank(value, "hotpotqa", "toy", "dense", {"present"}, depth=1)


if __name__ == "__main__":
    unittest.main()
