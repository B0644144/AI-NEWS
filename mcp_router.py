import asyncio
from typing import Iterable, List

from skills import MailSkill, NotionSkill, ObsidianSkill


def get_skills(targets: Iterable[str]):
    all_skills = {
        "mail": MailSkill(),
        "notion": NotionSkill(),
        "obsidian": ObsidianSkill(),
    }
    selected = []
    for t in targets:
        if t in all_skills:
            selected.append(all_skills[t])
    return selected


async def run_skills_concurrently(targets: List[str], title: str, markdown: str) -> List[str]:
    skills = get_skills(targets)
    if not skills:
        return ["未指定可用 skill，請使用: mail, notion, obsidian"]

    async def run_one(skill):
        return await asyncio.to_thread(skill.run, title, markdown)

    raw = await asyncio.gather(*(run_one(skill) for skill in skills), return_exceptions=True)
    results = []
    for skill, result in zip(skills, raw):
        if isinstance(result, Exception):
            results.append(f"{skill.name}：失敗 {type(result).__name__} - {result}")
        else:
            results.append(result)
    return results
