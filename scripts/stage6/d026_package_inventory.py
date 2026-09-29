#!/usr/bin/env python
from __future__ import annotations

import importlib.metadata
import json


def collect_package_inventory() -> list[dict[str, str]]:
    records = [
        {
            "name": distribution.metadata["Name"],
            "version": distribution.version,
        }
        for distribution in importlib.metadata.distributions()
    ]
    return sorted(records, key=lambda item: item["name"].lower())


def main() -> int:
    print(json.dumps(collect_package_inventory(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
