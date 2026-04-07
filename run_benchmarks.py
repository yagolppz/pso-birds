"""Punto de entrada principal para benchmarks de PSO-BIRDS."""

from __future__ import annotations

import sys

from experiments.benchmark_suite import main_compare_cli, main_suite_cli


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in {"run", "compare"}:
        main_compare_cli()
        return
    main_suite_cli()


if __name__ == "__main__":
    main()
