import os
from datetime import datetime, timezone
from pathlib import Path

from .base import ExportSkill


class ObsidianSkill(ExportSkill):
    name = "obsidian"

    def enabled(self) -> bool:
        return bool(os.getenv("OBSIDIAN_VAULT_PATH"))

    def run(self, title: str, markdown: str) -> str:
        if not self.enabled():
            return "Obsidian：未設定 OBSIDIAN_VAULT_PATH，已略過"

        out_dir = Path(os.environ["OBSIDIAN_VAULT_PATH"]) / "AI-Trends"
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = datetime.now(timezone.utc).strftime("ai-trends-%Y%m%d-%H%M.md")
        out_path = out_dir / filename
        out_path.write_text(markdown, encoding="utf-8")
        return f"Obsidian：已輸出到 {out_path}"
