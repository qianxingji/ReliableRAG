"""Durable C4 observations; no changed neural/scientific return values."""
import os

from scripts.empirical_runtime_contract import canonical


class Ledger:
    def __init__(self, path):
        self.stream = path.open("xb")
        self.rows = 0

    def append(self, row):
        self.stream.write(canonical(row) + b"\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.rows += 1

    def close(self):
        if not self.stream.closed:
            self.stream.close()


def binding(phase):
    return {name: phase[name] for name in ("dataset", "retriever", "sample_id", "position")}


class ForwardCounter:
    """Count attempted top-level calls before compute, including failed calls."""
    def __init__(self, model):
        self.calls = self.rows = self.input_tokens_with_padding = 0
        self.devices = set()
        self.hook = model.register_forward_pre_hook(self.before, with_kwargs=True)

    def before(self, model, args, kwargs):
        import torch
        if not torch.is_inference_mode_enabled() or torch.is_grad_enabled() or model.training:
            raise RuntimeError("Native scoring inference context")
        ids = kwargs["input_ids"]
        self.calls += 1
        self.rows += int(ids.shape[0])
        self.input_tokens_with_padding += int(ids.numel())
        self.devices.add(str(ids.device))

    def summary(self):
        return dict(attempted_forward_calls=self.calls, attempted_input_rows=self.rows,
            attempted_input_tokens_including_padding=self.input_tokens_with_padding, devices=sorted(self.devices))

    def close(self):
        self.hook.remove()


class ForwardJournal:
    """Register after the native observer: flush each completed witness once."""
    def __init__(self, model, observer, ledger, phase, *, nli=False):
        self.observer, self.ledger, self.phase = observer, ledger, phase
        self.nli, self.last = nli, 0
        self.hook = model.register_forward_hook(self.after, with_kwargs=True)

    def after(self, model, args, kwargs, output):
        if not self.observer.records:
            raise RuntimeError("Missing native forward observation before journaling")
        observed = self.observer.records[-1]
        if observed["forward_ordinal"] != self.last + 1:
            raise RuntimeError("Noncontiguous durable forward witness")
        row = dict(**binding(self.phase), witness=observed)
        if self.nli:
            row["state"] = self.phase["state"]
        self.ledger.append(row)
        self.last += 1
        return None

    def close(self):
        self.hook.remove()


def compact_base(record):
    return {**record, "forward_witnesses": [w["forward_ordinal"] for w in record["forward_witnesses"]]}


def compact_header(witness):
    return {**witness, "batches": [b["forward_ordinal"] for b in witness["batches"]]}


def compact_gbv(record):
    return {**record, "completed_branches": [dict(**{k: v for k, v in branch.items() if k != "witness"},
        witness=compact_header(branch["witness"])) for branch in record["completed_branches"]]}


class DurableGbV:
    """Preserve each completed branch before native paired scoring attempts next."""
    def __init__(self, observer, branches, phase):
        self.observer, self.branches, self.phase = observer, branches, phase
        self.position = 0

    @property
    def forward_count(self):
        return self.observer.forward_count

    def begin(self, trace, position):
        self.phase.update({k: trace[k] for k in ("dataset", "retriever", "sample_id")})
        self.phase["position"] = position
        self.position = 0

    def score_branch(self, question, answer, evidence):
        if self.position >= 2:
            raise RuntimeError("Unexpected third NLI branch")
        state = "F0" if self.position == 0 else "F1"
        self.position += 1
        self.phase["state"] = state
        result, witness = self.observer.score_branch(question, answer, evidence)
        from dataclasses import asdict
        self.branches.append(dict(**binding(self.phase), state=state, result=asdict(result), witness=compact_header(witness)))
        return result, witness
