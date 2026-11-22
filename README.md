# WBOX 皮肤库

[WBOX](https://github.com/qinchangsheng123/wbox) 的官方皮肤与制作模板。
关联仓库：[主程序](https://github.com/qinchangsheng123/wbox) · [插件库](https://github.com/qinchangsheng123/wbox-plugins)。

**从 WBOX v2.17.0 起面板只有一套「默认骨架」**：方角直排、行内展开、同窗换页、零动画。
皮肤只能改 **26 个颜色 token** 与行高 / 字号 / 图标 / 标题栏四项尺寸，**不含代码、不含位图、不换结构**。
`engine` / `performance` / `radius` 写进包里只为兼容老工具，渲染时不再读取。

制作规范见主仓 [`docs/SKIN-SPEC.md`](https://github.com/qinchangsheng123/wbox/blob/main/docs/SKIN-SPEC.md) v1.2.0。

## 皮肤清单

每个皮肤一个 Release，标签是 `<id>-v<版本>`，资产里是 `.wbskin` 和 `.sha256`。

| 皮肤 | 版本 | 说明 | 下载 |
|---|---|---|---|
| `kuan-green` 酷安绿 | 1.0.0 | 默认为底，只把强调色换成一档绿；明暗两套都带，对比度见皮肤内 README | [wbskin][r-kg] |

[r-kg]: https://github.com/qinchangsheng123/wbox-skins/releases/tag/kuan-green-v1.0.0

## 安装

1. 下载 `.wbskin`（与 `.sha256` 放同一目录可校验）。
2. 设置面板 →「外观与皮肤」→「从文件安装皮肤…」→ 选这个包。
3. 在「外观」列表里点皮肤名即可切换；卸载或选回「默认」随时可退。

也可以手工放进 `<安装目录>\skins\<id>\`：目录里必须是
`skin.json` / `preview.png` / `README.md`，**根目录直接是文件，不要多套一层文件夹**，
目录名必须与 `skin.json` 的 `id` 一致。

## 制作皮肤

从 [`templates/plain-base/`](templates/plain-base/) 复制一份开始，别从零写 JSON：

```bat
git clone https://github.com/qinchangsheng123/wbox-skins.git
cd wbox-skins
copy templates\plain-base\skin.json skins\my-theme\skin.json
python tools\pack.py skins\my-theme
```

改动范围只有：

- `light` / `dark` 下的 26 个 token（`#RGB`、`#RRGGBB` 或 `#RRGGBBAA`）；
- `metrics.row` / `font` / `icon` / `titlebar`（正整数，`row ≤ 44`）；
- `name` / `description` / `author` 等展示字段。

`radius` 三个值请保持 `0`。包里不能出现 `.py .pyc .dll .exe .bat .ps1 .cmd`，
安装器会直接拒绝。`preview.png` 必须 **256 × 144**。

`tools/pack.py` 是独立实现（不依赖主程序仓库），打完会重新打开产物自检：
缺 token、预览图尺寸错、根目录套壳、可执行文件混入，都会在打包时报错。
产物写到 `dist/<id>-v<版本>.wbskin` 与同名 `.sha256`。

## 目录

```text
skins/<id>/           官方皮肤源码（skin.json + preview.png + README.md）
templates/plain-base/ 默认皮肤底模板：默认配色 + 默认尺寸，直接复制改色
tools/pack.py         打包与校验工具
dist/                 已发布包（每个版本保留，便于追溯）
```

## 兼容

- WBOX **v2.18.0+**，皮肤 API **1**。
- v2.17.0 及更早的皮肤包继续可用；声明 `performance=standard` 的老包会按默认骨架渲染。
- 如要做的是功能插件（守护进程内运行），请去 [wbox-plugins](https://github.com/qinchangsheng123/wbox-plugins)。
