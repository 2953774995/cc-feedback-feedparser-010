"""多 feed 合并与去重。

`feedparser.parse()` 一次只解析一个 feed；本模块在其之上提供
`merge_feeds()`，把多个 feed（XML 字符串或已解析对象）合并成一个
条目列表，并按统一口径去重、记录每条目的来源。

去重口径：优先使用条目的 ``guid``，缺失时回退到 ``link``；两者都
没有的条目不参与去重，照常保留。重复条目只保留最先出现的一个。
"""

from .api import parse
from .util import FeedParserDict

__all__ = ["merge_feeds", "MergeResult"]


class MergeResult:
    """`merge_feeds()` 的返回值。

    属性：
      entries     合并后的条目列表，按输入 feed 顺序与条目原顺序
      duplicates  被去重掉的条目数量
      sources     每条 entry 对应的源 feed 标题（与 entries 等长）
      invalid     解析失败的 feed 序号列表
    """

    def __init__(self, entries, duplicates, sources, invalid):
        self.entries = entries
        self.duplicates = duplicates
        self.sources = sources
        self.invalid = invalid

    def __repr__(self):
        return (
            f"MergeResult(entries={len(self.entries)}, "
            f"duplicates={self.duplicates}, invalid={self.invalid})"
        )


def _as_parsed(feed):
    """把输入统一成解析结果对象；无法识别的类型返回 None。"""
    if isinstance(feed, FeedParserDict):
        return feed
    if isinstance(feed, (str, bytes)):
        return parse(feed)
    return None


def _dedup_key(entry):
    """返回条目的去重键；无 guid 且无 link 时返回 None（不参与去重）。"""
    guid = entry.get("guid") or entry.get("id")
    if guid:
        return ("guid", guid)
    link = entry.get("link")
    if link:
        return ("link", link)
    return None


def merge_feeds(feeds):
    """合并多个 feed 并去重。

    `feeds` 中的元素可以是 XML 字符串/字节串，也可以是
    `feedparser.parse()` 的返回对象。单个 feed 解析失败只记入
    `invalid`，不影响其它 feed 的合并。
    """
    entries = []
    sources = []
    invalid = []
    duplicates = 0
    seen = set()

    for index, feed in enumerate(feeds):
        parsed = _as_parsed(feed)
        if parsed is None or getattr(parsed, "bozo", False):
            invalid.append(index)
            continue

        title = parsed.get("feed", {}).get("title", "")
        for entry in parsed.get("entries", []):
            key = _dedup_key(entry)
            if key is not None:
                if key in seen:
                    duplicates += 1
                    continue
                seen.add(key)
            entries.append(entry)
            sources.append(title)

    return MergeResult(entries, duplicates, sources, invalid)
