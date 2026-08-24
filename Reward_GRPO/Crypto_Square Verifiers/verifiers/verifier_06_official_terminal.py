from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, execute

from _contract import CONTRACT
from _helpers import strict_official_checks


POLICY_ID = "CSF-C06"


def checks(ctx: Context) -> list[KernelReceipt]:
    return strict_official_checks(ctx, POLICY_ID)


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
