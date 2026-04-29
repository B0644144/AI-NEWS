from __future__ import annotations

from abc import ABC, abstractmethod


class ExportSkill(ABC):
    name: str

    @abstractmethod
    def enabled(self) -> bool:
        ...

    @abstractmethod
    def run(self, title: str, markdown: str) -> str:
        ...
