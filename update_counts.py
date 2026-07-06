#!/usr/bin/env python3
"""件数表記の一括更新スクリプト。

music.html / stickers.html の実カード数（<article class="music-card">,
<article class="sticker-card...">）を tab-group ごとに数えて、以下を書き換える:

  music.html   : meta description ×2 / page-lead「全N本」/ タブボタン「すべて (N)」
                 「歌モノMV (N)」「BGM・癒し系 (N)」/ 各サブタイトル「全N本」
  stickers.html: meta description ×2 / page-lead「全Nパック」/ タブボタン6個の (N)
                 / 各シリーズサブタイトル「全Nパック」
  index.html   : 統計カード .stat-num（N本・Nパック）/ section-lead
                 「全N本公開中」「全Nパック展開中」/ ボタン「全N本の楽曲を見る」
                 「全Nパックを見る」

使い方:
  python3 update_counts.py           # 数えて書き換え
  python3 update_counts.py --dry-run # 変更の有無を確認のみ（書き換えない）
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DRY_RUN = "--dry-run" in sys.argv or "-n" in sys.argv

GROUP_RE = re.compile(r'<div class="tab-group" data-group="([^"]+)"')
TARGET_RE = re.compile(r'data-target="([^"]+)"')


def group_counts(html: str, card_re: re.Pattern) -> dict[str, int]:
    """tab-group（data-group="X"）ごとに、次のグループまでのカード数を返す。"""
    groups = list(GROUP_RE.finditer(html))
    counts: dict[str, int] = {}
    for i, m in enumerate(groups):
        end = groups[i + 1].start() if i + 1 < len(groups) else len(html)
        counts[m.group(1)] = len(card_re.findall(html, m.end(), end))
    total = len(card_re.findall(html))
    if sum(counts.values()) != total:
        sys.exit(f"エラー: {sorted(counts)} の外にカードがある（グループ計{sum(counts.values())} ≠ 全体{total}）。構造を確認を。")
    return counts


def update_list_page(html: str, counts: dict[str, int], unit: str) -> str:
    """一覧ページ（music.html / stickers.html）の件数表記を書き換える。"""
    total = sum(counts.values())
    zen_re = re.compile(rf"全\d+{unit}")
    out = []
    current_group = None
    for line in html.splitlines(keepends=True):
        gm = GROUP_RE.search(line)
        if gm:
            current_group = gm.group(1)
        if "tab-btn" in line:
            tm = TARGET_RE.search(line)
            if tm:
                n = total if tm.group(1) == "all" else counts.get(tm.group(1))
                if n is None:
                    sys.exit(f"エラー: タブボタン data-target=\"{tm.group(1)}\" に対応する tab-group がない。")
                line = re.sub(r"\(\d+\)", f"({n})", line)
        elif 'class="sticker-subtitle"' in line:
            if current_group is None:
                sys.exit("エラー: tab-group の外にサブタイトルがある。構造を確認を。")
            line = zen_re.sub(f"全{counts[current_group]}{unit}", line)
        else:
            line = zen_re.sub(f"全{total}{unit}", line)
        out.append(line)
    return "".join(out)


def rewrite(path: Path, new_text: str) -> bool:
    if path.read_text(encoding="utf-8") == new_text:
        print(f"  {path.name}: 変更なし")
        return False
    if DRY_RUN:
        print(f"  {path.name}: 変更あり（--dry-run のため書き換えせず）")
    else:
        path.write_text(new_text, encoding="utf-8")
        print(f"  {path.name}: 更新しました")
    return True


def main() -> None:
    music_path = ROOT / "music.html"
    stickers_path = ROOT / "stickers.html"
    index_path = ROOT / "index.html"

    music = music_path.read_text(encoding="utf-8")
    stickers = stickers_path.read_text(encoding="utf-8")
    index = index_path.read_text(encoding="utf-8")

    music_counts = group_counts(music, re.compile(r'<article class="music-card"'))
    sticker_counts = group_counts(stickers, re.compile(r'<article class="sticker-card'))
    songs_total = sum(music_counts.values())
    packs_total = sum(sticker_counts.values())

    print(f"実カード数: 楽曲 全{songs_total}本 {music_counts}, スタンプ 全{packs_total}パック {sticker_counts}")

    rewrite(music_path, update_list_page(music, music_counts, "本"))
    rewrite(stickers_path, update_list_page(stickers, sticker_counts, "パック"))

    out = []
    for line in index.splitlines(keepends=True):
        line = re.sub(r'(class="stat-num">)\d+(<small>本)', rf"\g<1>{songs_total}\g<2>", line)
        line = re.sub(r'(class="stat-num">)\d+(<small>パック)', rf"\g<1>{packs_total}\g<2>", line)
        line = re.sub(r"全\d+本", f"全{songs_total}本", line)
        line = re.sub(r"全\d+パック", f"全{packs_total}パック", line)
        out.append(line)
    rewrite(index_path, "".join(out))

    print("完了。" + ("（dry-run）" if DRY_RUN else ""))


if __name__ == "__main__":
    main()
