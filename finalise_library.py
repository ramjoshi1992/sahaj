"""
ZenTune | finalise_library.py
=============================
Two jobs that close out the manifest work:

  --textures     find the 14 soundscapes on R2 and fold them into
                 library.json, so the texture layer has addresses.
                 upload_textures.py was the only thing that ever printed
                 them and it is now in legacy/.

  --verify       HEAD every URL in library.json. The URLs were built from
                 a path convention, not read back from the bucket, so a
                 single wrong segment would 404 at runtime with no warning.

    python finalise_library.py --verify
    python finalise_library.py --textures
    python finalise_library.py --textures --verify
"""

import argparse, json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

LIB = "library.json"
PUBLIC = "https://pub-fefcc3396a88474693cc19e7780eb61f.r2.dev"

TEXTURES = [
    "beach_1", "beach_2", "forest_1", "forest_2", "city_1",
    "suburb_1", "suburb_2", "cafe_1", "rain", "storm_1",
    "storm_2", "fireplace_1", "night_1", "river_1",
]
EXTS = [".mp3", ".ogg", ".wav", ".m4a"]

# how the auto-selector maps context to a texture (see the design notes)
TEXTURE_RULES = {
    "coastal": ["beach_1", "beach_2"],
    "urban": ["city_1"],
    "suburban": ["suburb_1", "suburb_2"],
    "rural": ["forest_1", "forest_2"],
    "river": ["river_1"],
    "rain": ["rain"],
    "storm": ["storm_1", "storm_2"],
    "summerNight": ["night_1"],
    "winter": ["fireplace_1"],
    "manualOnly": ["cafe_1", "fireplace_1"],
}


def head(url, timeout=20):
    req = Request(url, method="HEAD", headers={"User-Agent": "ZenTune/1.0"})
    try:
        with urlopen(req, timeout=timeout) as r:
            return r.status, int(r.headers.get("Content-Length") or 0)
    except HTTPError as e:
        return e.code, 0
    except URLError as e:
        return 0, 0


def find_textures():
    print(f"probing {len(TEXTURES)} textures under textures/ ...\n")
    found, missing = {}, []
    for name in TEXTURES:
        hit = None
        for ext in EXTS:
            url = f"{PUBLIC}/textures/{name}{ext}"
            code, size = head(url)
            if code == 200:
                hit = dict(url=url, bytes=size)
                print(f"  {name:<12} {ext:<5} {size/1048576:6.2f} MB")
                break
        if hit:
            found[name] = hit
        else:
            missing.append(name)
            print(f"  {name:<12} NOT FOUND with any of {', '.join(EXTS)}")
    return found, missing


def add_textures(lib_path):
    lib = json.loads(Path(lib_path).read_text(encoding="utf-8"))
    found, missing = find_textures()
    if not found:
        print("\nNo textures resolved — check the prefix on R2 before writing.")
        return
    lib["_textures"] = dict(files=found, rules=TEXTURE_RULES,
                            missing=missing, gain=0.15)
    Path(lib_path).write_text(json.dumps(lib, indent=1), encoding="utf-8")
    print(f"\nwrote _textures into {lib_path}  "
          f"({len(found)} found, {len(missing)} missing)")


def verify(lib_path):
    lib = json.loads(Path(lib_path).read_text(encoding="utf-8"))
    urls = []
    for key, g in lib.items():
        if key.startswith("_"):
            continue
        for piece, d in g["pieces"].items():
            urls.append((f"{key}/{piece}", d["url"]))
    tex = lib.get("_textures", {}).get("files", {})
    for name, d in tex.items():
        urls.append((f"texture/{name}", d["url"]))

    print(f"checking {len(urls)} URLs ...\n")
    bad, total_bytes = [], 0
    with ThreadPoolExecutor(max_workers=12) as ex:
        results = list(ex.map(lambda u: (u[0], u[1], *head(u[1])), urls))
    for label, url, code, size in results:
        total_bytes += size
        if code != 200:
            bad.append((label, url, code))

    print(f"  {len(urls)-len(bad)}/{len(urls)} OK")
    print(f"  {total_bytes/1048576:.0f} MB addressable")
    if bad:
        print(f"\n  {len(bad)} FAILED:")
        for label, url, code in bad[:25]:
            print(f"    [{code or 'net'}] {label}")
            print(f"           {url}")
        if len(bad) > 25:
            print(f"    ... and {len(bad)-25} more")
        return False
    print("\n  every URL in the library resolves.")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", default=LIB)
    ap.add_argument("--textures", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if not Path(args.lib).exists():
        sys.exit(f"{args.lib} not found — run build_library.py first.")
    if not (args.textures or args.verify):
        ap.error("nothing to do — pass --textures and/or --verify")

    if args.textures:
        add_textures(args.lib)
    if args.verify:
        ok = verify(args.lib)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
