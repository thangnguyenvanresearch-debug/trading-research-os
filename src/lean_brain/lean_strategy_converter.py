from __future__ import annotations


def convert_to_lean_skeleton(spec: dict) -> str:
    return f'''from AlgorithmImports import *


class {spec["strategy_name"].title().replace("_", "")}(QCAlgorithm):
    """Generated skeleton from Trading Research OS YAML spec.

    Research only. No leverage or futures by default.
    """

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetCash(100000)
        self.symbols = [self.AddEquity(ticker).Symbol for ticker in {spec.get("pairs", [])!r}]

    def OnData(self, data):
        pass
'''

