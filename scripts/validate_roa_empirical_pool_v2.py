"""Unchanged independent C1 validator, directed to the Windows metadata retry."""
import sys
from scripts import validate_roa_empirical_pool as validator

if __name__ == "__main__":
    sys.dont_write_bytecode = True
    validator.OUT = validator.REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
    raise SystemExit(validator.main())
