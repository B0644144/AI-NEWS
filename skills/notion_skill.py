import os
import time
from typing import Optional

import requests

from .base import ExportSkill


class NotionSkill(ExportSkill):
    name = "notion"

    def enabled(self) -> bool:
        return bool(os.getenv("NOTION_TOKEN") and os.getenv("NOTION_DATABASE_ID"))

    def _headers(self):
        return {
            "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def _request_with_retry(self, method: str, url: str, **kwargs):
        retries = 3
        backoffs = [1, 2, 4]
        last_resp = None
        for i in range(retries):
            try:
                resp = requests.request(method, url, timeout=20, **kwargs)
                last_resp = resp
                if resp.status_code == 429 or resp.status_code >= 500:
                    if i < retries - 1:
                        time.sleep(backoffs[i])
                        continue
                return resp
            except requests.RequestException:
                if i < retries - 1:
                    time.sleep(backoffs[i])
                    continue
                raise
        return last_resp

    def _detect_title_property(self) -> Optional[str]:
        db_id = os.environ["NOTION_DATABASE_ID"]
        resp = self._request_with_retry("GET", f"https://api.notion.com/v1/databases/{db_id}", headers=self._headers())
        if not resp or resp.status_code >= 300:
            return None
        props = resp.json().get("properties", {})
        for name, meta in props.items():
            if meta.get("type") == "title":
                return name
        return None

    def run(self, title: str, markdown: str) -> str:
        if not self.enabled():
            return "Notion：未設定 NOTION_TOKEN / NOTION_DATABASE_ID，已略過"

        title_prop = self._detect_title_property()
        if not title_prop:
            return "Notion：找不到 title 欄位，請確認 database 設定"

        paragraphs = []
        for line in markdown.splitlines()[:80]:
            if line.strip():
                paragraphs.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": line[:1900]}}]},
                })

        payload = {
            "parent": {"database_id": os.environ["NOTION_DATABASE_ID"]},
            "properties": {title_prop: {"title": [{"text": {"content": title[:100]}}]}},
            "children": paragraphs[:100],
        }

        resp = self._request_with_retry("POST", "https://api.notion.com/v1/pages", headers=self._headers(), json=payload)
        if not resp:
            return "Notion：匯出失敗 unknown-response"
        if resp.status_code >= 300:
            msg = ""
            try:
                payload = resp.json()
                msg = payload.get("message", "")
            except ValueError:
                msg = resp.text[:120]
            return f"Notion：匯出失敗 {resp.status_code} {msg}".strip()
        return f"Notion：已建立頁面 {resp.json().get('url', '')}"
