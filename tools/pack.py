# -*- coding: utf-8 -*-
"""把 WBOX 皮肤目录打成 `.wbskin` 并生成 `.sha256` 侧车。

用法（本仓库根目录执行）：
    python tools/pack.py                       # 打包 skins\\ 下全部皮肤 -> dist\\
    python tools/pack.py skins\\kuan-green      # 只打一个
    python tools/pack.py --check dist\\x.wbskin # 只校验已有包

格式约定与 WBOX 主程序 `src/skin_package.py` / `src/skins.py` 一一对应：
根目录直接是 skin.json / preview.png / README.md，不允许再套文件夹；
preview.png 必须 256×144；performance=minimal 不许带 assets；包内不许有可执行文件。
这里是**独立实现**，不 import 主程序代码：皮肤仓库要能单独克隆、单独打包。
打完会重新打开产物逐项自检，能打出来的一定装得进去。
"""
import hashlib
import json
import os
import re
import struct
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, 'skins')
OUT_DIR = os.path.join(ROOT, 'dist')

MANIFEST = 'skin.json'
ALLOWED = (MANIFEST, 'preview.png', 'README.md')
API_VERSION = 1
ID_RE = re.compile(r'^[a-z][a-z0-9-]{1,31}$')
VER_RE = re.compile(r'^\d+\.\d+\.\d+$')
COLOR_RE = re.compile(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')
TOKENS = (
    'fg', 't2', 't3', 't4',
    'hair', 'hair_strong',
    'fill', 'fill_2', 'press',
    'inset',
    'glass', 'glass_hi', 'glass_line', 'glass_edge',
    'switch_off', 'knob', 'on', 'on_knob',
    'icon_bg', 'icon_fg',
    'menu_base', 'pop_base',
    'amb0', 'amb1', 'amb2', 'amb3',
)
METRIC_KEYS = ('row', 'font', 'icon', 'titlebar')
RADIUS_KEYS = ('window', 'card', 'row')
REQUIRED = ('id', 'name', 'version', 'api', 'engine', 'performance',
            'chrome', 'metrics', 'radius', 'light')
MAX_MEMBER = 512 * 1024
MAX_TOTAL = 4 * 1024 * 1024
ZIP_DATE = (1980, 1, 1, 0, 0, 0)          # 固定时间戳：同内容出同字节


def fail(msg):
    raise SystemExit('ERROR: ' + msg)


def check_manifest(meta, expect_id=None):
    if not isinstance(meta, dict):
        fail('skin.json 顶层必须是对象')
    for key in REQUIRED:
        if key not in meta:
            fail('skin.json 缺少必填字段 %s' % key)
    sid = meta['id']
    if not isinstance(sid, str) or not ID_RE.match(sid):
        fail('id 不合法：%r' % (sid,))
    if expect_id and sid != expect_id:
        fail('目录名必须等于 id：目录 %s / id %s' % (expect_id, sid))
    if not isinstance(meta['name'], str) or not meta['name'].strip() \
            or len(meta['name']) > 12:
        fail('name 必须是 1~12 字的非空字符串')
    if not isinstance(meta['version'], str) or not VER_RE.match(meta['version']):
        fail('version 必须是三段式 X.Y.Z')
    api = meta['api']
    if isinstance(api, bool) or not isinstance(api, int) or not (0 < api <= API_VERSION):
        fail('api 必须是 1~%d 的整数' % API_VERSION)
    if meta['engine'] not in ('flat', 'bitmap'):
        fail('engine 只能是 flat / bitmap')
    if meta['performance'] not in ('minimal', 'standard'):
        fail('performance 只能是 minimal / standard')
    if meta['chrome'] not in ('system', 'custom'):
        fail('chrome 只能是 system / custom')
    metrics, radius = meta['metrics'], meta['radius']
    if not isinstance(metrics, dict) or not isinstance(radius, dict):
        fail('metrics / radius 必须是对象')
    for key in METRIC_KEYS:
        v = metrics.get(key)
        if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
            fail('metrics.%s 必须是正整数' % key)
    for key in RADIUS_KEYS:
        v = radius.get(key)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            fail('radius.%s 必须是非负整数' % key)
    for block in ('light', 'dark'):
        if block not in meta:
            continue
        colors = meta[block]
        if not isinstance(colors, dict):
            fail('%s 必须是对象' % block)
        missing = [t for t in TOKENS if t not in colors]
        if missing:
            fail('%s 缺少 %d 个 token：%s' % (block, len(missing), ', '.join(missing)))
        for token in TOKENS:
            if not isinstance(colors[token], str) or not COLOR_RE.match(colors[token]):
                fail('%s.%s 颜色格式不对：%r' % (block, token, colors[token]))
    if meta['performance'] == 'minimal':
        if meta.get('assets'):
            fail('performance=minimal 不许带 assets（默认骨架不读位图）')
        if metrics['row'] > 44:
            fail('performance=minimal 行高不得超过 44')
    elif meta['performance'] == 'standard' and metrics['row'] > 56:
        fail('performance=standard 行高不得超过 56')
    return sid


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b'\x89PNG\r\n\x1a\n' or head[12:16] != b'IHDR':
        fail('preview.png 不是有效 PNG：%s' % path)
    return struct.unpack('>II', head[16:24])


def read_meta(path):
    with open(path, 'rb') as f:
        raw = f.read()
    try:
        return json.loads(raw.decode('utf-8-sig'))
    except (UnicodeDecodeError, ValueError) as e:
        fail('skin.json 不是有效 UTF-8 JSON：%r' % (e,))


def zip_info(name, size):
    zi = zipfile.ZipInfo(name, ZIP_DATE)
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.create_system = 0
    zi.external_attr = (0o100644 << 16)
    zi.file_size = size
    return zi


def verify_archive(path):
    if not zipfile.is_zipfile(path):
        fail('不是有效 zip：%s' % path)
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if names[0] != MANIFEST:
            fail('skin.json 必须是包内第一个条目：%r' % names[:3])
        for name in names:
            if name not in ALLOWED:
                fail('包内不允许这个文件：%s（根目录只许 skin.json/preview.png/README.md）' % name)
            info = zf.getinfo(name)
            if info.file_size > MAX_MEMBER:
                fail('单文件超过 512 KB：%s' % name)
            if info.flag_bits & 0x1:
                fail('包内有加密条目：%s' % name)
        if sum(zf.getinfo(n).file_size for n in names) > MAX_TOTAL:
            fail('解压后总量超过 4 MB')
        if MANIFEST not in names or 'preview.png' not in names:
            fail('skin.json 与 preview.png 都必需')
        sid = check_manifest(read_meta_path(zf), None)
        if png_bytes_size(zf.read('preview.png')) != (256, 144):
            fail('preview.png 必须是 256×144')
    return sid


def read_meta_path(zf):
    # 保持与 read_meta 一样的解析口径，但读的是包内条目
    try:
        return json.loads(zf.read(MANIFEST).decode('utf-8-sig'))
    except (UnicodeDecodeError, ValueError) as e:
        fail('包内 skin.json 不是有效 UTF-8 JSON：%r' % (e,))


def png_bytes_size(data):
    if len(data) < 24 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        fail('包内 preview.png 不是有效 PNG')
    return struct.unpack('>II', data[16:24])


def pack_one(src_dir):
    src_dir = os.path.abspath(src_dir)
    sid = os.path.basename(os.path.normpath(src_dir))
    manifest = os.path.join(src_dir, MANIFEST)
    if not os.path.isfile(manifest):
        fail('源目录里没有 skin.json：%s' % src_dir)
    meta = read_meta(manifest)
    check_manifest(meta, expect_id=sid)
    preview = os.path.join(src_dir, 'preview.png')
    if not os.path.isfile(preview):
        fail('缺少 preview.png：%s' % preview)
    if png_size(preview) != (256, 144):
        fail('preview.png 必须是 256×144，实得 %r' % (png_size(preview),))
    names = [n for n in ALLOWED if os.path.isfile(os.path.join(src_dir, n))]
    if MANIFEST not in names or 'preview.png' not in names:
        fail('源目录必须含 skin.json 与 preview.png')
    total = 0
    for name in names:
        size = os.path.getsize(os.path.join(src_dir, name))
        if size > MAX_MEMBER:
            fail('单文件超过 512 KB：%s' % name)
        total += size
    if total > MAX_TOTAL:
        fail('解压后总量超过 4 MB')

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, '%s-v%s.wbskin' % (sid, meta['version']))
    tmp = out + '.tmp'
    try:
        with zipfile.ZipFile(tmp, 'w', compresslevel=9) as zf:
            for name in names:
                with open(os.path.join(src_dir, name), 'rb') as f:
                    data = f.read()
                zf.writestr(zip_info(name, len(data)), data)
        os.replace(tmp, out)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise

    packed_id = verify_archive(out)
    if packed_id != sid:
        fail('产物 id 与目录名不符：%s / %s' % (packed_id, sid))
    digest = hashlib.sha256(open(out, 'rb').read()).hexdigest()
    side = out + '.sha256'
    with open(side, 'w', encoding='ascii', newline='\n') as f:
        f.write('%s  %s\n' % (digest, os.path.basename(out)))
    print('OK  %-34s %8d B  sha256=%s' % (os.path.basename(out),
                                          os.path.getsize(out), digest[:16]))
    return out


def check_one(path):
    path = os.path.abspath(path)
    sid = verify_archive(path)
    side = path + '.sha256'
    if os.path.isfile(side):
        want = open(side, encoding='ascii').read().split()[0]
        got = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        if want != got:
            fail('sha256 侧车与包不符：%s' % path)
        print('OK  %s id=%s sha256=%s' % (os.path.basename(path), sid, got[:16]))
    else:
        print('OK  %s id=%s（没有 .sha256 侧车）' % (os.path.basename(path), sid))


def main(argv):
    if argv and argv[0] == '--check':
        for p in argv[1:]:
            check_one(p)
        return 0
    targets = argv or [os.path.join(SRC_DIR, n) for n in sorted(os.listdir(SRC_DIR))
                       if os.path.isdir(os.path.join(SRC_DIR, n))]
    if not targets:
        fail('没有可打包的皮肤目录')
    for t in targets:
        pack_one(t)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
