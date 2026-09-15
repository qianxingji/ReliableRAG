"""Independent witness primitives; no native scoring/execution imports."""
import hashlib
import json
import math


def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def object_sha(value):
    return hashlib.sha256(packed(value)).hexdigest()


def text_sha(value):
    if type(value) is not str:
        raise ValueError("Witness binding requires an original string")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def key(row):
    return row["dataset"], row["retriever"], row["sample_id"]


class Checks:
    def __init__(self):
        self.count = 0

    def require(self, condition, message):
        self.count += 1
        if not condition:
            raise ValueError("Independent witness: " + message)

    def exact(self, actual, expected, message):
        self.require(packed(actual) == packed(expected), message)

    def schema(self, actual, fields, message):
        self.require(type(actual) is dict and set(actual) == set(fields), message)

    def finite(self, value, message):
        self.require(type(value) in (int, float) and math.isfinite(value), message)


def token_fields(encoded):
    return {name: value.tolist() for name, value in encoded.items()}
