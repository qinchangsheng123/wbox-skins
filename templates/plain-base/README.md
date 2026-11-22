# 默认模板 · plain-base

这不是一个供用户安装的皮肤，而是**做皮肤的起点**：内容逐项复制自 WBOX 内置
「默认」皮肤（`src/skins.py` 的 `BUILTIN[0]`），26 个 token 与四项尺寸全部原样。

## 怎么用

1. 复制整个目录到 `skins/<你的 id>/`，目录名必须等于 `skin.json` 里的 `id`。
2. 改 `skin.json`：
   - `id` 小写字母开头、只含小写字母数字连字符（2~32 字），装过之后不要改；
   - `name` ≤ 12 字；`version` 三段式；`api` 保持 `1`；
   - `engine` 写 `flat`、`performance` 写 `minimal`、`chrome` 写 `custom`；
   - `metrics.row ≤ 44`；`radius` 三项保持 `0`；
   - `light` / `dark` 的 26 个 token 一个都不能少，可以按需删掉 `dark`（缺省时复用浅色）。
3. 用 256×144 的 `preview.png` 换掉模板预览图。
4. 在仓库根目录跑 `python tools\pack.py skins\<你的 id>`，产物落在 `dist/`。

## 能改什么、不能改什么

能改：颜色、字号、行高、图标尺寸、标题栏高度、展示文案。

不能改：骨架（方角直排 + 行内展开 + 同窗换页 + 零动画）、交互、布局逻辑，
也不能往包里塞代码或位图。WBOX v2.17.0 起没有第二条渲染路径，
所以「换骨架」这件事在机制上就不成立——这是好事，主题不会再因为内核升级而散架。

## token 对照

`glass` / `glass_hi` / `glass_line` / `glass_edge` 是历史名字，现在分别表示
窗口底色、窗口底高光、描边、外缘；改名会让所有已分发皮肤包失效，所以继续沿用。
`menu_base` / `pop_base` 是皮肤面板与插件设置框两个浮层的底色。
`amb0`~`amb3` 只给设计稿用，面板落地时忽略。

完整说明见 [SKIN-SPEC.md](https://github.com/qinchangsheng123/wbox/blob/main/docs/SKIN-SPEC.md)。
