"""Exclusive durable serialization of frozen D bootstrap multiplicities/receipts."""
import os

import numpy as np

from scripts.empirical_runtime_contract import canonical


class BootstrapWriter:
    def __init__(self, output, *, groups, draws=20000, questions_per_dataset=2000):
        if type(groups) is not int or type(draws) is not int or type(questions_per_dataset) is not int or not (groups > 0 and draws > 0 and 0 < questions_per_dataset <= 2000):
            raise ValueError("Explicit finite bootstrap storage dimensions")
        self.groups, self.draws, self.maximum = groups, draws, questions_per_dataset
        self.completed = 0
        self.weights = (output / "BOOTSTRAP_QUESTION_WEIGHTS.u16le").open("xb")
        try:
            self.receipts = (output / "BOOTSTRAP_DRAWS.jsonl").open("xb")
        except Exception:
            self.weights.close()
            raise

    def append(self, weights, receipt):
        values = np.asarray(weights)
        if self.completed >= self.draws or values.shape != (self.groups,) or values.dtype.kind not in "iu" or np.any(values < 0) or np.any(values > self.maximum):
            raise ValueError("Exact checked bootstrap row before unsigned storage")
        if type(receipt) is not dict or type(receipt.get("draw")) is not int or receipt["draw"] != self.completed:
            raise ValueError("Exact next bootstrap receipt index")
        encoded = canonical(receipt)
        self.weights.write(values.astype("<u2", copy=False).tobytes(order="C"))
        self.weights.flush()
        os.fsync(self.weights.fileno())
        self.receipts.write(encoded + b"\n")
        self.receipts.flush()
        os.fsync(self.receipts.fileno())
        self.completed += 1

    def summary(self):
        return dict(dtype="little-endian uint16", shape=[self.draws, self.groups], completed_draws=self.completed,
            completed_weight_bytes=self.completed*self.groups*2, expected_complete_weight_bytes=self.draws*self.groups*2,
            maximum_count=self.maximum, arithmetic_dtype="int64", no_header=True)

    def close(self):
        for stream in (self.weights, self.receipts):
            if not stream.closed:
                stream.close()
