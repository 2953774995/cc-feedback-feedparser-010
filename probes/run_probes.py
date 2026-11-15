#!/usr/bin/env python3
"""多 feed 合并去重验收探针。

契约：
  from feedparser.merge import merge_feeds
  res = merge_feeds([xml1, xml2, ...])
  res.entries     合并后的条目列表，按输入 feed 顺序与条目原顺序
  res.duplicates  被去重掉的条目数量
  res.sources     每条 entry 对应的源 feed 标题（列表，与 entries 等长）
  res.invalid     解析失败的 feed 序号列表，不抛异常
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FAILED = 0
PASSED = 0


def check(code, desc, fn):
    global FAILED, PASSED
    try:
        fn()
        print(f"[PASS] {code} {desc}")
        PASSED += 1
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {code} {desc}")
        print(f"        {type(exc).__name__}: {exc}")
        FAILED += 1


def feed(title, items):
    entries = "".join(
        f"<item><title>{t}</title><link>{u}</link>"
        + (f"<guid>{g}</guid>" if g else "")
        + "</item>"
        for t, u, g in items
    )
    return (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        f"<title>{title}</title>{entries}</channel></rss>"
    )


def main():
    try:
        from feedparser.merge import merge_feeds  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] P0 导入 feedparser.merge 失败：{type(exc).__name__}: {exc}")
        print("-" * 60)
        print("探针汇总：0/7 通过")
        return 1

    A = feed("A", [("a1", "https://x/1", "g1"), ("a2", "https://x/2", "g2")])
    B = feed("B", [("a1 dup", "https://x/1", "g1"), ("b1", "https://x/3", "g3")])

    def p1():
        r = merge_feeds([A, B])
        assert len(r.entries) == 3, len(r.entries)
        assert r.duplicates == 1, r.duplicates

    def p2():
        r = merge_feeds([A])
        assert [e.title for e in r.entries] == ["a1", "a2"], [e.title for e in r.entries]
        assert r.duplicates == 0

    def p3():
        r = merge_feeds([A, B])
        assert r.sources == ["A", "A", "B"], r.sources

    def p4():
        no_guid = feed("C", [("c1", "https://x/4", None)])
        dup_link = feed("D", [("c1 again", "https://x/4", None)])
        r = merge_feeds([no_guid, dup_link])
        assert len(r.entries) == 1, len(r.entries)
        assert r.duplicates == 1

    def p5():
        r = merge_feeds([feed("E", []), feed("F", [("f1", "https://x/5", "g5")])])
        assert len(r.entries) == 1

    def p6():
        r = merge_feeds([A, "<rss><channel><title>broken"])
        assert 1 in r.invalid, r.invalid
        assert len(r.entries) == 2, len(r.entries)

    def p7():
        import feedparser
        parsed = feedparser.parse(A)
        assert len(parsed.entries) == 2
        r = merge_feeds([parsed, feedparser.parse(B)])
        assert len(r.entries) == 3

    check("P1", "相同 guid 去重", p1)
    check("P2", "单 feed 原样返回", p2)
    check("P3", "记录每条来源", p3)
    check("P4", "无 guid 时按 link 去重", p4)
    check("P5", "空 feed 不影响合并", p5)
    check("P6", "非法 feed 进 invalid 不中断", p6)
    check("P7", "也接受已解析对象", p7)

    print("-" * 60)
    print(f"探针汇总：{PASSED}/{PASSED + FAILED} 通过")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
