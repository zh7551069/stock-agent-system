# 书籍资产台账（Book Asset Ledger）

> 只读调研报告 · 生成时间：本次会话 · 机器：macOS 26.6.2 (25G83) arm64
> 调研范围：`/Volumes/My PSSD/`、`/Users/zenghui/Downloads/`、`/Users/zenghui/Documents/`，以及补充的全 home 扫描
> 所有路径均为绝对路径。凡未找到者明确写「未找到」并说明搜索范围。

---

## 0. 结论速览（TL;DR）

| 问题 | 结论 |
|---|---|
| 外盘上有没有书籍原件？ | **有**。主库：`/Volumes/My PSSD/downlodData/books/` |
| 能不能读？ | **能**，外盘 exfat 已正常挂载、可读（`/dev/disk6s1 on /Volumes/My PSSD (exfat, local, nodev, nosuid, noowners)`） |
| 17 本书是否都有原件？ | **17/17 全部找到原件**，无一本只有 .md |
| 6 本「空壳」书原件是否找得到？ | **6/6 全部找到**，见 §3 |
| 文字层质量 | 9 本优质 / 2 本系统性字形替换（需重 OCR）/ 6 本纯扫描件（需 OCR） |
| 本机有无 OCR 能力 | **有，且已验证可用**：macOS Vision（Swift）+ 已有现成 OCR 全文产物 |
| 最关键发现 | 6 本空壳书的**全文与 85 张卡其实早已挖完并入库**，只有 `书籍/` 下的本书主笔记仍是占位桩 —— 详见 §3.3 |

---

## 1. 全盘搜索书籍原件

### 1.1 搜索命令与规模

```bash
# 外盘（exfat，find 用时 2.6s，无需 maxdepth）
find "/Volumes/My PSSD" -type f \( -iname "*.pdf" -o -iname "*.epub" -o -iname "*.mobi" \
  -o -iname "*.azw3" -o -iname "*.djvu" -o -iname "*.txt" \) -print0
# → 94 条（含 macOS 的 ._ AppleDouble 伴生文件），真实文件 57 条

# 本地
find /Users/zenghui/Downloads /Users/zenghui/Documents -type f \( 同上 \) -print0
# → 741 条

# 补充：全 home 扫描（剪枝 Library/node_modules/.git/venv/site-packages/.Trash/Caches）
find /Users/zenghui ... -type f \( -iname "*.pdf" -o -iname "*.epub" -o -iname "*.mobi" -o -iname "*.azw3" -o -iname "*.djvu" \) -print0
# → 102 条
```

**未找到 `.djvu` 文件（全盘 0 个）。**

### 1.2 主库：`/Volumes/My PSSD/downlodData/books/`

按大小排序（已剔除 `.AppleDouble` 的 `._*` 文件）：

| 大小 | 修改时间 | 绝对路径 |
|---:|---|---|
| 85.54 MB | 2026-08-21 23:09 | `/Volumes/My PSSD/downlodData/books/股市趋势技术分析（第十版）.pdf` |
| 71.50 MB | 2026-09-03 23:57 | `/Volumes/My PSSD/downlodData/books/行为投资学手册 投资者如何避免成为自己最大的敌人(高清).pdf` |
| 70.89 MB | 2026-08-21 06:11 | `/Volumes/My PSSD/downlodData/books/投资大师威科夫经典合集(高清).pdf` |
| 52.67 MB | 2026-10-03 10:16 | `/Volumes/My PSSD/downlodData/books/量化投资策略与技术修订版.pdf` |
| 52.52 MB | 2026-08-21 06:12 | `/Volumes/My PSSD/downlodData/books/理查德·D·威科夫操盘术(高清).pdf` |
| 43.02 MB | 2026-10-03 10:30 | `/Volumes/My PSSD/downlodData/books/Perry Kaufman - Trading Systems and Methods (5th ed) (2013).pdf` |
| 38.56 MB | 2026-08-21 06:42 | `/Volumes/My PSSD/downlodData/books/交易心理分析：用自信、自律和赢家心态掌控市场(高清).pdf` |
| 25.69 MB | 2026-10-03 10:11 | `/Volumes/My PSSD/downlodData/books/主动投资组合管理：创造高收益并控制风险的量化投资方法 原书第2版(高清).pdf` |
| 20.41 MB | 2026-08-21 23:10 | `/Volumes/My PSSD/downlodData/books/笑傲股市(原书第4版).pdf` |
| 17.17 MB | 2026-10-03 10:29 | `/Volumes/My PSSD/downlodData/books/短线交易秘诀-原书第2版-拉里·威廉斯.pdf` |
| 14.05 MB | 2026-10-03 10:18 | `/Volumes/My PSSD/downlodData/books/e-book-EN-Ralph-Vince-The-Mathematics-of-Money-Management-Risk-Analysis-techniques-for-trad.pdf` |
| 12.39 MB | 2026-08-21 21:34 | `/Volumes/My PSSD/downlodData/books/日本蜡烛图技术.pdf` |
| 8.48 MB | 2026-10-03 10:14 | `/Volumes/My PSSD/downlodData/books/Marcos Lopez de Prado - Advances in Financial Machine Learning-Wiley (2018).pdf` |
| 3.14 MB | 2026-08-21 23:02 | `/Volumes/My PSSD/downlodData/books/15c019bc03a78f83fd2c323a.pdf` ← **实为《股票大作手回忆录》丁圣元译修订版** |
| 1.92 MB | 2026-10-03 10:17 | `/Volumes/My PSSD/downlodData/books/Mathematics Of Money Management. Ralph Vince.pdf` |
| 1.75 MB | 2026-08-21 06:27 | `/Volumes/My PSSD/downlodData/books/海龟交易法则.pdf` |
| 1.27 MB | 2026-08-21 23:12 | `/Volumes/My PSSD/downlodData/books/华尔街幽灵.阿瑟·L.辛普森.pdf` |
| 1.01 MB | 2026-08-21 06:19 | `/Volumes/My PSSD/downlodData/books/交易心理分析.pdf` |

**非股票类（`xujiao/` 子目录，运营/商业书，与知识库无关）**：

| 大小 | 修改时间 | 绝对路径 |
|---:|---|---|
| 22.52 MB | 2026-08-22 17:44 | `/Volumes/My PSSD/downlodData/books/xujiao/运营之光3.0：我的互联网运营方法论与自白.pdf` |
| 9.90 MB | 2026-08-22 17:45 | `/Volumes/My PSSD/downlodData/books/xujiao/增长黑客_创业公司的用户与收入增长秘籍 - 范冰.pdf` |
| 9.56 MB | 2023-11-30 13:37 | `/Volumes/My PSSD/downlodData/books/xujiao/2534-爆款文案/爆款文案.mobi` |
| 8.87 MB | 2023-11-30 13:37 | `/Volumes/My PSSD/downlodData/books/xujiao/2534-爆款文案/爆款文案.azw3` |
| 8.51 MB | 2026-08-22 18:01 | `/Volumes/My PSSD/downlodData/books/xujiao/《影响力》经典版 罗伯特·B.西奥迪尼(美).pdf` |
| 7.87 MB | 2023-11-30 13:37 | `/Volumes/My PSSD/downlodData/books/xujiao/2534-爆款文案/爆款文案.epub` |
| 3.12 MB | 2026-08-22 17:58 | `/Volumes/My PSSD/downlodData/books/xujiao/定位- 杰克・特劳特、阿尔・里斯.mobi` |
| 2.58 MB | 2026-08-22 18:08 | `/Volumes/My PSSD/downlodData/books/xujiao/《从0到1：开启商业与未来的秘密》彼得·蒂尔(美).pdf` |
| 2.36 MB | 2026-08-22 17:30 | `/Volumes/My PSSD/downlodData/books/xujiao/疯传·传染     +V：shuyou066（补发）.pdf` |
| 2.29 MB | 2026-08-22 18:19 | `/Volumes/My PSSD/downlodData/books/xujiao/《长尾理论》克里斯·安德森(完美版).pdf` |
| 2.15 MB | 2026-08-22 17:54 | `/Volumes/My PSSD/downlodData/books/xujiao/引爆点：如何制造流行[lunarora.com].pdf` |
| 1.20 MB | 2026-08-22 18:15 | `/Volumes/My PSSD/downlodData/books/xujiao/长尾理论     全网电子书，+V：shuyou066（补发）.pdf` |
| 0.97 MB | 2026-08-22 18:20 | `/Volumes/My PSSD/downlodData/books/xujiao/精益创业.mobi` |
| 0.95 MB | 2026-08-22 18:15 | `/Volumes/My PSSD/downlodData/books/xujiao/精益创业     全网电子书，+V：shuyou066（补发）.pdf` |

**其他（非书籍，来自外盘根目录）**：`/Volumes/My PSSD/电子对账单.pdf`（0.20 MB）、`/Volumes/My PSSD/reports/*_深度投研报告_20260817.pdf`（3 个）、`/Volumes/My PSSD/本地数据库_v2版（淘宝购买）/A股分钟数据/A股分时数据目录结构与复权说明.pdf`

外盘 `books/` 目录结构只有三层：
```
/Volumes/My PSSD/downlodData/books
/Volumes/My PSSD/downlodData/books/xujiao
/Volumes/My PSSD/downlodData/books/xujiao/2534-爆款文案
```

### 1.3 `/Users/zenghui/Downloads/`

| 大小 | 修改时间 | 绝对路径 | 备注 |
|---:|---|---|---|
| 52,522,352 B | 2026-10-03 10:16 | `/Users/zenghui/Downloads/量化投资策略与技术修订版.pdf` | 与外盘**逐字节相同** |
| 45,109,714 B | 2026-10-03 10:30 | `/Users/zenghui/Downloads/Perry Kaufman - Trading Systems and Methods (5th ed) (2013).pdf` | 与外盘**逐字节相同** |
| 26,934,099 B | 2026-10-03 10:11 | `/Users/zenghui/Downloads/主动投资组合管理：创造高收益并控制风险的量化投资方法 原书第2版(高清).pdf` | 与外盘**逐字节相同** |
| 10,246,679 B | 2026-10-03 10:10 | `/Users/zenghui/Downloads/主动投资组合管理(中文).pdf` | **外盘没有，独一份**（396 页纯扫描） |
| 2,012,084 B | 2026-10-03 10:17 | `/Users/zenghui/Downloads/Mathematics Of Money Management. Ralph Vince.pdf` | 与外盘**逐字节相同** |
| 1,060,008 B | 2026-08-21 06:19 | `/Users/zenghui/Downloads/交易心理分析.pdf` | 与外盘**逐字节相同** |
| 2,404,689 B | 2026-08-22 18:19 | `/Users/zenghui/Downloads/《长尾理论》克里斯·安德森(完美版).pdf` | 商业书 |

### 1.4 `/Users/zenghui/Documents/` 与知识库

- `/Users/zenghui/Documents/stock/stock/知识库/书籍/` —— **未找到任何 .pdf/.epub/.mobi/.azw3/.djvu**。该目录下只有 `.md` 文件与 6 个 `*图/` 插图目录。
- 全 home 扫描（102 个 PDF/EPUB/MOBI/AZW3）中，除上述外**唯一**的股票书籍原件在隐藏目录中：

```
8,621,072 B  2026-09-03 08:26
/Users/zenghui/.openclaw-autoclaw/workspace/.tencent-im-remote-files/144115458927506148-1788395205-1019805356-【金融炼金术】-77d583574f.pdf
```
> `pdfinfo` → `Title: 金融炼金术`、`Author: WWW.MicroBell.COM`、`Creator: pdfFactory Pro`、`Pages: 362`、`Subject: 动力先锋论坛普通阅览室`。**362 页，纯扫描，全文 0 字符可提取。**

- 与股票知识库无关的 PDF（供排除）：`/Users/zenghui/Documents/stock/2025钱坤大学堂·策马营交易一本通11.11.pdf`、`/Users/zenghui/Documents/stock/量价走势-资料.pdf`、`/Users/zenghui/Documents/stock/集合竞价策略.pdf`、`/Users/zenghui/Documents/FDE_knowledge/Datawhale FDE案例100.pdf` 等报告/讲义类文件。

### 1.5 其他卷宗

`/Volumes/ChatGPT Installer`、`/Volumes/DeepSeek Harness 0.2.0-rc.2-arm64` 下 `-maxdepth 4` 搜索：**未找到任何书籍格式文件**（均为安装镜像，且只读挂载）。

---

## 2. 书籍清单去重与归类

去重方法：`md5 -q`（外盘 exfat 可读，5 组共 10 个文件逐字节相同）。**去重后股票类书籍原件共 18 个独立文件，对应 16 部作品。**

| 书名 | 作者（据文件名/元数据判断） | 格式 | 路径 | 大小 | 重复情况 |
|---|---|---|---|---|---|
| 股市趋势技术分析（第十版） | Edwards / Magee（W.H.C. Bassetti 修订） | PDF | `/Volumes/My PSSD/downlodData/books/股市趋势技术分析（第十版）.pdf` | 85.54 MB | 唯一 |
| 行为投资学手册 | James Montier | PDF（扫描） | `/Volumes/My PSSD/downlodData/books/行为投资学手册 投资者如何避免成为自己最大的敌人(高清).pdf` | 71.50 MB | 唯一 |
| 投资大师威科夫经典合集 | Richard D. Wyckoff | PDF（扫描） | `/Volumes/My PSSD/downlodData/books/投资大师威科夫经典合集(高清).pdf` | 70.89 MB | 唯一 |
| 量化投资：策略与技术（修订版） | 丁鹏 | PDF（扫描） | `/Volumes/My PSSD/downlodData/books/量化投资策略与技术修订版.pdf` | 52.67 MB | = Downloads 同名文件（md5 `32917bb5…`） |
| 理查德·D·威科夫操盘术 | Richard D. Wyckoff（上海财大版） | PDF（扫描） | `/Volumes/My PSSD/downlodData/books/理查德·D·威科夫操盘术(高清).pdf` | 52.52 MB | 唯一 |
| Trading Systems and Methods (5th ed, 2013) | Perry J. Kaufman | PDF | `/Volumes/My PSSD/downlodData/books/Perry Kaufman - Trading Systems and Methods (5th ed) (2013).pdf` | 43.02 MB | = Downloads（md5 `fc65cb31…`） |
| 交易心理分析（高清中文扫描） | Mark Douglas | PDF（扫描） | `/Volumes/My PSSD/downlodData/books/交易心理分析：用自信、自律和赢家心态掌控市场(高清).pdf` | 38.56 MB | 唯一 |
| 主动投资组合管理 原书第2版（高清） | Grinold & Kahn | PDF（原生文字但字形被替换） | `/Volumes/My PSSD/downlodData/books/主动投资组合管理：创造高收益并控制风险的量化投资方法 原书第2版(高清).pdf` | 25.69 MB | = Downloads（md5 `5f876bc2…`） |
| 笑傲股市（原书第4版） | William J. O'Neil | PDF（扫描） | `/Volumes/My PSSD/downlodData/books/笑傲股市(原书第4版).pdf` | 20.41 MB | 唯一 |
| 短线交易秘诀（原书第2版） | Larry Williams | PDF（原生文字但字形被替换） | `/Volumes/My PSSD/downlodData/books/短线交易秘诀-原书第2版-拉里·威廉斯.pdf` | 17.17 MB | 唯一 |
| The Mathematics of Money Management（英文电子版） | Ralph Vince | PDF | `/Volumes/My PSSD/downlodData/books/e-book-EN-Ralph-Vince-The-Mathematics-of-Money-Management-Risk-Analysis-techniques-for-trad.pdf` | 14.05 MB | 唯一（另有 1.92 MB 版，见下） |
| 日本蜡烛图技术 | Steve Nison | PDF（文字页+扫描页混合） | `/Volumes/My PSSD/downlodData/books/日本蜡烛图技术.pdf` | 12.39 MB | 唯一 |
| Advances in Financial Machine Learning (Wiley 2018) | Marcos López de Prado | PDF | `/Volumes/My PSSD/downlodData/books/Marcos Lopez de Prado - Advances in Financial Machine Learning-Wiley (2018).pdf` | 8.48 MB | 唯一 |
| 股票大作手回忆录（修订版，丁圣元译） | Edwin Lefèvre | PDF | `/Volumes/My PSSD/downlodData/books/15c019bc03a78f83fd2c323a.pdf` | 3.14 MB | 唯一（**文件名是哈希，需改名**） |
| Mathematics Of Money Management | Ralph Vince | PDF | `/Volumes/My PSSD/downlodData/books/Mathematics Of Money Management. Ralph Vince.pdf` | 1.92 MB | = Downloads（md5 `197760c9…`） |
| 海龟交易法则 | Curtis Faith | PDF | `/Volumes/My PSSD/downlodData/books/海龟交易法则.pdf` | 1.75 MB | 唯一 |
| 华尔街幽灵 | Arthur L. Simpson | PDF | `/Volumes/My PSSD/downlodData/books/华尔街幽灵.阿瑟·L.辛普森.pdf` | 1.27 MB | 唯一 |
| 交易心理分析（英文原版+中文对照） | Mark Douglas | PDF | `/Volumes/My PSSD/downlodData/books/交易心理分析.pdf` | 1.01 MB | = Downloads（md5 `610bc3b6…`） |
| 主动投资组合管理（中文，另一版） | Grinold & Kahn | PDF（纯扫描） | `/Users/zenghui/Downloads/主动投资组合管理(中文).pdf` | 9.77 MB | 唯一（外盘无） |
| 金融炼金术 | George Soros | PDF（纯扫描） | `/Users/zenghui/.openclaw-autoclaw/workspace/.tencent-im-remote-files/144115458927506148-1788395205-1019805356-【金融炼金术】-77d583574f.pdf` | 8.22 MB | 唯一（不在 Downloads/Documents） |

**同一本书多版本/多格式（需人工选定母本）**：

| 作品 | 版本数 | 差异 |
|---|---|---|
| The Mathematics of Money Management | 3 | 14.05 MB 英文电子版（原生文字，200 页，最佳）；1.92 MB 版 ×2（外盘+Downloads，同一文件，109 页）；另有 `/tmp/books_extract/Vince-MoMM-ebook.md` 由浏览器电子版提取 |
| 主动投资组合管理 | 3 | 25.69 MB「(高清)」×2（850 页，字形被替换）；9.77 MB「(中文)」仅 Downloads（396 页纯扫描） |
| 交易心理分析 | 2 | 38.56 MB 高清中文扫描（273 页，可 OCR）；1.01 MB 英文原版+中文对照（160 页，原生文字） |

**外盘 `books/` 下另有 11 个非股票类电子书**（`xujiao/`：运营之光、增长黑客、爆款文案 epub/azw3/mobi、影响力、定位、从0到1、疯传、长尾理论、引爆点、精益创业）——与股票知识库无关，去重时已单列。

**未找到的书籍格式**：`.djvu`（全盘 0 个）。

---

## 3. 与知识库书目的对照

### 3.1 知识库现有构成

`/Users/zenghui/Documents/stock/stock/知识库/书籍/`：

- **18 个主 `.md`**：17 本书笔记 + 1 个非书籍文档《日内做T操作SOP.md》
- **16 个 `-挖掘要点.md`**
- **6 个插图目录**：`交易心理分析图/`、`威科夫操盘术图/`、`威科夫经典合集图/`、`日本蜡烛图技术图/`（304 项）、`海龟交易法则图/`、`行为投资学手册图/`
- **`知识点-*.md` 总数 = 2238**（在 `/Users/zenghui/Documents/stock/stock/知识库/知识地图/`，与委托人口径一致）

缺口：**《威科夫经典合集》没有 `-挖掘要点.md`**。

### 3.2 原件 vs 仅有 .md

**17 本书全部找到原件（PDF）。没有任何一本书是「只有 .md 文本」。**

各 .md 文件头部本身已标注开采时所用原件路径，与实测文件一一对应：

| 知识库 .md | 头部声明的原件路径 | 实测是否存在 | 备注 |
|---|---|---|---|
| `交易心理分析.md` | `/Volumes/My PSSD/downlodData/books/交易心理分析：…(高清).pdf` | ✅ | 路径一致 |
| `威科夫经典合集.md` | `/Volumes/My PSSD/downlodData/books/投资大师威科夫经典合集(高清).pdf` | ✅ | 路径一致 |
| `海龟交易法则.md` | `/Volumes/My PSSD/downlodData/books/海龟交易法则.pdf` | ✅ | 路径一致 |
| `行为投资学手册.md` | `/Volumes/My PSSD/downlodData/books/行为投资学手册 …(高清).pdf` | ✅ | 路径一致 |
| `日本蜡烛图技术.md` | `/Volumes/My PSSD/downlodData/books/日本蜡烛图技术.pdf` | ✅ | 路径一致 |
| `股票大作手回忆录.md` | `/Volumes/My PSSD/downlodData/books/15c019bc03a78f83fd2c323a.pdf` | ✅ | 与实测哈希文件名吻合 |
| `华尔街幽灵.md` | `/Volumes/My PSSD/downlodData/华尔街幽灵.阿瑟·L.辛普森.pdf` | ⚠️ 已移动 | 实际在 `.../downlodData/books/` 下（`books/` 子目录是后来才建的） |
| `笑傲股市.md` | `/Volumes/My PSSD/downlodData/笑傲股市(原书第4版).pdf` | ⚠️ 已移动 | 实际在 `.../downlodData/books/` 下 |
| `股市趋势技术分析.md` | `/Volumes/My PSSD/downlodData/股市趋势技术分析（第十版）.pdf` | ⚠️ 已移动 | 实际在 `.../downlodData/books/` 下 |
| `金融炼金术.md` | 「PDF OCR 全文」，未写路径 | ✅ 已定位 | 见 §1.4 |

> 结论：`/Volumes/My PSSD/downlodData/books/` 是后来成立的归档目录，早期挖矿时文件直接在 `downlodData/` 下。凡 .md 头部写 `downlodData/xxx.pdf` 的，现在应去 `downlodData/books/xxx.pdf` 找。

### 3.3 6 本「空壳占位」逐本核对

| # | 书名 | 原件是否找到 | 原件绝对路径 | 页数 | 文字层状态 |
|---|---|---|---|---|---|
| 1 | Advances in Financial Machine Learning | ✅ 找到 | `/Volumes/My PSSD/downlodData/books/Marcos Lopez de Prado - Advances in Financial Machine Learning-Wiley (2018).pdf` | 393 | **原生文字层极佳**，英文，无需 OCR |
| 2 | The Mathematics of Money Management | ✅ 找到（3 版） | `/Volumes/My PSSD/downlodData/books/e-book-EN-Ralph-Vince-The-Mathematics-of-Money-Management-Risk-Analysis-techniques-for-trad.pdf`（最佳）／`/Volumes/My PSSD/downlodData/books/Mathematics Of Money Management. Ralph Vince.pdf`／`/Users/zenghui/Downloads/Mathematics Of Money Management. Ralph Vince.pdf` | 200 / 109 | **原生文字层极佳**，英文，无需 OCR |
| 3 | Trading Systems and Methods | ✅ 找到 | `/Volumes/My PSSD/downlodData/books/Perry Kaufman - Trading Systems and Methods (5th ed) (2013).pdf`（= `/Users/zenghui/Downloads/Perry Kaufman - Trading Systems and Methods (5th ed) (2013).pdf`） | 1232 | **原生文字层极佳**，英文，无需 OCR |
| 4 | 主动投资组合管理 | ✅ 找到（2 版） | `/Volumes/My PSSD/downlodData/books/主动投资组合管理：创造高收益并控制风险的量化投资方法 原书第2版(高清).pdf`（850 页）／`/Users/zenghui/Downloads/主动投资组合管理(中文).pdf`（396 页纯扫描） | 850 / 396 | ⚠️ **字形系统性替换**，直接抽取为乱码；须渲染 + OCR |
| 5 | 短线交易秘诀 | ✅ 找到 | `/Volumes/My PSSD/downlodData/books/短线交易秘诀-原书第2版-拉里·威廉斯.pdf` | 487 | ⚠️ **字形系统性替换**，同上；须渲染 + OCR |
| 6 | 量化投资-策略与技术 | ✅ 找到 | `/Volumes/My PSSD/downlodData/books/量化投资策略与技术修订版.pdf`（= `/Users/zenghui/Downloads/量化投资策略与技术修订版.pdf`） | 572 | ⚠️ **纯扫描件**（每页 1 张 image），须 OCR |

### 3.4 ★最关键发现：6 本空壳书的正文与卡片其实早已挖完

`/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/books_extract/`（2026-10-03 11:04–11:32 产出）里躺着**完整成品**：

| 文件 | 大小 | 对应书 |
|---|---:|---|
| `AFML.md` | 754,997 B | Advances in Financial Machine Learning 全文 |
| `AFML-挖掘要点.md` | 24,106 B | 同上挖掘要点 |
| `cards-AFML.md` | 30,195 B | 16 张卡草稿 |
| `Kaufman-TSM.md` | 2,716,396 B | Trading Systems and Methods 全文 |
| `Kaufman-TSM-挖掘要点.md` | 29,706 B | |
| `cards-Kaufman.md` | 30,251 B | 15 张卡 |
| `Vince-MoMM.md` / `Vince-MoMM-ebook.md` | 765,504 / 741,743 B | The Mathematics of Money Management 全文（两来源） |
| `Vince-MoMM-挖掘要点.md` | 26,118 B | |
| `cards-Vince.md` | 20,553 B | 12 张卡 |
| `Grinold-Kahn.md` / `Grinold-Kahn.txt` | 1,102,050 / 962,085 B | 主动投资组合管理 全文（OCR） |
| `Grinold-Kahn-挖掘要点.md` | 31,230 B | |
| `cards-Grinold-Kahn.md` | 42,642 B | 14 张卡 |
| `LarryWilliams.md` / `LarryWilliams.txt` | 521,246 / 596,289 B | 短线交易秘诀 全文（OCR） |
| `LarryWilliams-挖掘要点.md` | 32,823 B | |
| `cards-LarryWilliams.md` | 37,478 B | 14 张卡 |
| `Quant-Dingpeng.txt` | 1,024,974 B | 量化投资：策略与技术 全文（OCR，页 9–572） |
| `Quant-Dingpeng-挖掘要点.md` | 36,505 B | |
| `cards-Quant-Dingpeng.md` | 34,792 B | 14 张卡 |
| `books-mining-summary.html` | 20,535 B | 总览：「6 本 / 85 张卡 … **状态：草稿，未入库**」 |

**核对结果（实测）**：85 张卡的标题**全部 85/85 已作为独立文件存在于** `/Users/zenghui/Documents/stock/stock/知识库/知识地图/`（如 `知识点-主动管理基本定律…`、`知识点-波动性突破（开盘价参考点）.md`）。也就是说**卡片已经入库了**。

**真正没入库的是 6 本书在 `书籍/` 下的「本书主笔记 + 挖掘要点」**——它们停留在 364–600 字节的占位桩：

| 书 | books_extract 里的富内容 | 知识库 `书籍/` 里的现状 |
|---|---|---|
| Advances in Financial Machine Learning | 全文 754,997 B ／ 要点 24,106 B | `Advances in Financial Machine Learning.md` = **583 B** ／ 要点 = **444 B** |
| Trading Systems and Methods | 2,716,396 B ／ 29,706 B | 540 B ／ 400 B |
| The Mathematics of Money Management | 765,504 B ／ 26,118 B | 511 B ／ 432 B |
| 主动投资组合管理 | 1,102,050 B ／ 31,230 B | 523 B ／ 388 B |
| 短线交易秘诀 | 521,246 B ／ 32,823 B | 487 B ／ 364 B |
| 量化投资-策略与技术 | 1,024,974 B ／ 36,505 B | 502 B ／ 404 B |

> **可执行结论**：这 6 本「空壳」不是「没挖」，而是「挖完的成品没回填到 `书籍/` 目录」。修复动作＝把 `books_extract/*-挖掘要点.md` 复制/改写进 `/Users/zenghui/Documents/stock/stock/知识库/书籍/<书名>-挖掘要点.md`，并据 `AFML.md` 等全文补全主笔记。**无需重新 OCR。**
> 附带证据：`/Users/zenghui/Documents/stock/stock/知识库/OCR存疑点核对清单-2026-09-27.md` 明确指出《主动投资组合管理》《短线交易秘诀》《量化投资》等当时尚在「待核」；而 `books-mining-summary.html` 显示 2026-10-03 已把它们挖完。

### 3.5 已有 OCR 全文产物（可直接复用，无需重跑）

| 位置 | 内容 |
|---|---|
| `/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/books_extract/` | 6 本书全文 + 要点 + 85 张卡（见上表） |
| `/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/jinrong_ocr/full_combined.txt`（601,177 B）+ `combined_*.txt`（7 个分批） | 《金融炼金术》362 页全量 OCR |
| `/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/xa_ocr/1-55 … 441-470/`（9 个批次，各含 `combined.txt`） | 《笑傲股市》470 页全量 OCR |
| `/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/jp_ocr/ocr_log.txt` | 《日本蜡烛图技术》扫描页（422 页）OCR 日志 |
| `/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/wk_ocr/ocr_log.txt`（56,593 B） | 《威科夫经典合集》9 批 OCR 日志 |
| `/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/pdf-ocr/<uuid>/combined.txt`（40+ 个任务目录） | 逐批 OCR 原始产物 |

已有 OCR 的驱动脚本（可复用）：`run_wk_ocr.sh`、`run_jp_ocr.sh`、`run_xa_ocr2.sh`、`ocr_batch.sh`、`ocr_chunked.py`、`append_ocr.py`，均在 `/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/`。

---

## 4. 文字层质量抽检（抽检 22 个文件 / 覆盖 16 部作品）

### 4.1 方法与命令

```bash
# 页数
pdfinfo "$f" | awk -F': *' '/^Pages/{print $2}'
# 全文抽取 + 逐页命中率
pdftotext "$f" out.txt
# 逐页统计（\f 分页）：非空白字符数、≥50 字符的页数
python3 -c "... split('\f') ..."
# 判定扫描件 vs 原生：页内图像数 + 字体
pdfimages -list -f P -l P "$f"
pdffonts -f P -l P "$f"
# 渲染 + OCR 复核
pdftoppm -f P -l P -r 200 -png "$f" page
./ocr_test page-P.png          # macOS Vision
```

> 注：`pdftoppm` 会打印 `Fontconfig error: No writable cache directories` 警告，属无害，图像照常生成。

### 4.2 逐本结果

图例：**可用** = 可直接抽取、中文排版正常；**须重 OCR** = 原生文字但字形被替换，抽取即乱码；**须 OCR** = 纯扫描图，无文字层。

| 书名 | 页数 | 可抽取字符 | 有字符页数 | 字符/页 | 判定 | 观察 |
|---|---:|---:|---:|---:|---|---|
| 股市趋势技术分析（第十版） | 750 | 453,918 | 749/750 | 605 | **可用**（优） | 中文排版正常；每页夹 1 行盗版水印 |
| 行为投资学手册(高清) | 213 | 24,495 | 213/213 | 115 | **须 OCR** | 每页仅 1 张 image；所谓「文字」**只有盗版水印**，正文 0 字符 |
| 投资大师威科夫经典合集(高清) | 493 | 56,695 | 493/493 | 115 | **须 OCR** | 同上一模一样，正文 0 字符 |
| 量化投资策略与技术修订版 | 572 | 204 | 1/572 | 0.4 | **须 OCR** | 每页 1 张 image（150 dpi），全文 204 字符 |
| 理查德·D·威科夫操盘术(高清) | 243 | 345 | 0/243 | 1.4 | **须 OCR** | 纯图，仅水印残留 345 字符 |
| Perry Kaufman - TSM (5th) | 1232 | 2,187,378 | 1209/1232 | 1775 | **可用**（优） | 英文原生，字形嵌入完整 |
| 交易心理分析：(高清) | 273 | 345 | 0/273 | 1.3 | **须 OCR** | 纯扫描，仅水印 |
| 主动投资组合管理 原书第2版(高清) | 850 | 328,022 | 850/850 | 373 | **须重 OCR** | 原生矢量（`pdfimages` = 0 张图），但字形被系统性替换 |
| 笑傲股市(原书第4版) | 470 | 0 | 0/470 | 0.0 | **须 OCR** | 每页 1 张 image，**全文 0 字符** |
| 短线交易秘诀-原书第2版 | 487 | 147,083 | 446/487 | 302 | **须重 OCR** | 原生矢量，字形被系统性替换 |
| Mathematics of Money Management（14.05 MB 英文） | 200 | 607,855 | 200/200 | 3039 | **可用**（优） | 英文原生 |
| 日本蜡烛图技术 | 751 | 163,940 | 328/751 | 218 | **可用（部分）** | 文字页中文正常；其余为图表页（≥200 字符页 276 页）；知识库 .md 头部已注明「文本页用原文，扫描页用 OCR」 |
| Advances in Financial Machine Learning | 393 | 615,222 | 370/393 | 1566 | **可用**（优） | 英文原生，字体 `TimesLTStd` 全嵌入 |
| 股票大作手回忆录（`15c019bc….pdf`） | 174 | 228,212 | 172/174 | 1312 | **可用**（优） | 中文正常，含完整目录 |
| Mathematics Of Money Management（1.92 MB） | 109 | 629,267 | 108/109 | 5773 | **可用**（优） | 英文原生，版面极密 |
| 海龟交易法则 | 241 | 129,476 | 233/241 | 537 | **可用**（优） | 中文正常 |
| 华尔街幽灵 | 207 | 136,050 | 201/207 | 657 | **可用**（优） | 中文正常 |
| 交易心理分析（1.01 MB，160 页） | 160 | 232,449 | 156/160 | 1453 | **可用** | 中英对照（CJK 47,748 / 拉丁 173,389，即 **78% 英文**）；首 2 页为盗版书友广告 |
| 金融炼金术 | 362 | 0 | 0/362 | 0.0 | **须 OCR** | `pdfFactory Pro` 生成，纯扫描，**全文 0 字符** |
| 主动投资组合管理(中文)（Downloads） | 396 | 0 | 0/396 | 0.0 | **须 OCR** | `FreePic2Pdf_Lib v2.18` + CCITT stencil，纯扫描 |
| 量化投资策略与技术修订版（Downloads） | 572 | 204 | 1/572 | 0.4 | **须 OCR** | 与外盘 md5 `32917bb5…` 完全相同 |
| Perry Kaufman（Downloads） | 1232 | 2,187,378 | 1209/1232 | 1775 | **可用**（优） | 与外盘 md5 `fc65cb31…` 完全相同 |

### 4.3 三类问题的实证

**(a) 纯扫描件——正文只有盗版水印，抽出的是广告**

```bash
pdftotext -f 100 -l 100 ".../行为投资学手册 …(高清).pdf" -
```
```
全国最低交易手续费免费办理国内正规商品股指原油期货开户 零佣金 不限资金量和交易量直接申请交易所手续费
任何地方费用比我们低 10倍赔偿差价 客服QQ/微信：958218088 期货开户和书籍下载请进:http://www.7help.net
```
该页**只有这两行**。统计显示 213 页中，每页水印恰好贡献 13 + 102 = 115 字符 —— 即 `行为投资学手册` 与 `威科夫经典合集` 的「115 字符/页」**全部是水印，正文可抽取字符为 0**。
`pdftotext -f 200 -l 200 ".../笑傲股市(原书第4版).pdf" -` → **输出完全为空**。`pdftotext -f 300 -l 300 ".../量化投资策略与技术修订版.pdf" -` → 仅 204 字符。

**(b) 原生矢量但字形被系统性替换（不是扫描，也不是 ToUnicode 简单缺失）**

```bash
pdftotext -f 400 -l 400 ".../主动投资组合管理…(高清).pdf" -
```
```
10.7
现 子 动 我 将 虑几 比 实际、㔃ᶴ化䖳低的ֻ 子，׍䎆于“波 动⦷·IC·标准分值”这њ㓿傼法则ᶕ产⭏䎵ᑨ᭦益⦷的㋮⛬亴测。
```
`pymupdf` 逐字形验证同一结果：
```python
'子' '现' '൘' '我' 'Ԝ' '将' '㘳' '虑' '几' 'њ' '比' '䖳' '实' '际' '、' '㔃'
```
即：印在纸面上的字是对的，但 PDF 字体的 **glyph→Unicode 映射被替换成了形近异码位**（交→`Ӕ`、我→`Ԝ`、来→`ᶕ`、很→`ᶸ`、的→`\u0590`…）。`pdffonts` 显示正文字体为 `SimSun CID TrueType Identity-H emb=yes sub=no uni=yes` —— 这就是根因。`pdfimages -list -f 400 -l 400` 返回 **0 张图**，证明页面是矢量文本而非位图。

**这不是「文件损坏」，而是「抽取通路不可用」。修复路径已被我实测验证可行**（见下）。

**(c) 修复验证：渲染 + macOS Vision OCR 完美还原**

```bash
pdftoppm -f 400 -l 400 -r 200 -png ".../主动投资组合管理…(高清).pdf" ./apo_p400
./ocr_test ./apo_p400-400.png
```
输出（节选，**中文完全正确**）：
```
10.7 例子
现在我们将考虑几个比较实际、结构化较低的例子，依赖于“波
动率•IC•标准分值”这个经验法则来产生超常收益率的精炼预测。
我么假设已知残差波动率的估计值。在没有充足的历史信息来确定原
始预测的IC时，我们使用不太精确但已被检验过的先验估计：良好的
预测变量具有IC=0.05，优秀的预测变量具有IC=0.10，世界级的预测
变量具有IC=0.15。高于0.20的IC通常预示着逆推测试（backtest）的
错误或者内幕交易。
```
> 注意：OCR 也会把页面上的盗版水印一起读出来，**后处理需过滤水印行**。
> 另：由于替换映射是**一致的双射**（`短线交易秘诀` 全文只有 1341 个不同汉字，远低于真实书籍的 ~3000+），理论上也可用 OCR 当 oracle 建替换表；但直接渲染+OCR 更省事，且已在 `books_extract/` 完成过。

### 4.4 本机 OCR 能力（已实测）

**✅ 可用方案 1 — macOS Vision（推荐，免费、本机、离线）**

- 驱动脚本：`/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/ocr.swift`（932 B）
- 关键实现：`VNRecognizeTextRequest()`，`recognitionLevel = .accurate`，`usesLanguageCorrection = true`，`recognitionLanguages = ["zh-Hans","zh-Hant","en-US"]`
- 编译与运行（我已实测通过）：
  ```bash
  swiftc -O ocr.swift -o ocr_test && ./ocr_test page.png
  ```
- 环境：Swift 6.3.3（`/usr/bin/swiftc`）、`Vision.framework` 存在、macOS 26.6.2
- 实测结果：中文正确率优秀（见 §4.3(c)）

**✅ 可用方案 2 — AutoClaw 远程 OCR（2026-08/10 挖矿时实际使用的）**

- Skill：`/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/pdfocr_SKILL.md`（skill 名 `autoclaw-pdf-ocr`）
- 客户端：`$OPENCLAW_STATE_DIR/skills/autoclaw-pdf-ocr/scripts/pdf-ocr.mjs`
- 用法：`node pdf-ocr.mjs run --pdf "<绝对路径>" --pages "1-40" --json`
- 依赖环境变量（**未验证是否仍有效，需凭据**）：`AUTOCLAW_OCR_PROXY_URL`、`AUTOCLAW_OCR_PROXY_TOKEN`、`AUTOCLAW_CLAWPDF_MODULE_PATH`
- 限制：单次 ≤60 页（日志里见过 `{"ok":false,"error":"At most 60 pages can be processed."}`）
- 附带 skill：`glmocr_skill.md`

**❌ 不可用**

- `tesseract`、`ocrmypdf`、`gocr`、`cuneiform`：**均未安装**（`which` 全部 NOT_FOUND；全 home `find` 也找不到任何 `tesseract`/`ocrmypdf` 可执行文件；`brew list` 中无 tesseract）
- python `pytesseract` / `easyocr` / `paddleocr` / `rapidocr_onnxruntime` / `cnocr`：**全部 MISSING**（在 `/opt/homebrew/bin/python3` 3.14.7 与 `/Users/zenghui/ComfyUI/venv/bin/python3` 中均未安装）
- 快捷指令：`/usr/bin/shortcuts` 存在，但 `shortcuts list` **返回空**（未安装任何 OCR 快捷指令）
- 旁证（非 CLI）：`/Users/zenghui/Library/Application Support/Google/Chrome/screen_ai/153.3/gocr/` 下有 Google OCR 模型（Chrome 内置读屏 OCR），但**无命令行入口**，不可脚本化调用

> **结论：本机完全具备离线中文 OCR 能力（macOS Vision + Swift），且历史上已用另一条通路（AutoClaw 远程 OCR）把这 6 本书全部 OCR 完毕；`tesseract` 类工具缺失不影响任务。**

---

## 5. 工具可用性清单

| 工具 | 是否存在 | 版本 / 路径 | 备注 |
|---|---|---|---|
| `pdftotext` | ✅ | **26.09.0** ／ `/opt/homebrew/bin/pdftotext` | brew `poppler` |
| `pdfinfo` | ✅ | **26.09.0** ／ `/opt/homebrew/bin/pdfinfo` | |
| `pdftoppm` | ✅ | 26.09.0 ／ `/opt/homebrew/bin/pdftoppm` | 渲染给 OCR 用，实测可用 |
| `pdffonts` | ✅ | 26.09.0 ／ `/opt/homebrew/bin/pdffonts` | 诊断字形映射的关键 |
| `pdfimages` | ✅ | 26.09.0 ／ `/opt/homebrew/bin/pdfimages` | 判定扫描件 vs 原生 |
| 其他 poppler 工具 | ✅ | `pdfattach` `pdfdetach` `pdfseparate` `pdfsig` `pdftocairo` `pdftohtml` `pdftops` `pdfunite` | 均在 `/opt/homebrew/bin/` |
| `mutool` | ❌ **未找到** | — | `/opt/homebrew/Cellar` 无 `mupdf`；`which mutool` NOT_FOUND |
| `qpdf` | ❌ **未找到** | — | `which qpdf` NOT_FOUND；brew 无 `qpdf` |
| python `pymupdf`（`fitz`） | ✅ | **1.28.2** ／ `/opt/homebrew/bin/python3`（**3.14.7**） | `import fitz` 会打印弃用警告，建议 `import pymupdf` |
| python `pypdf` | ✅ | **6.16.1** ／ 同上 | |
| python `PyPDF2` | ❌ 未找到 | — | `ModuleNotFoundError` |
| python `pdfplumber` | ❌ 未找到 | — | `ModuleNotFoundError` |
| python `pdfminer` | ❌ 未找到 | — | `ModuleNotFoundError` |
| python `PIL`(Pillow) | ✅ | 仅 `/Users/zenghui/ComfyUI/venv/bin/python3` | 系统 python3 无 |
| python `ebooklib` | ✅ | 同上 | |
| `tesseract` | ❌ **未找到** | — | `which` NOT_FOUND；brew 无 |
| `ocrmypdf` | ❌ **未找到** | — | `which` NOT_FOUND；python 包也 MISSING |
| `libreoffice` / `soffice` | ❌ **未找到** | — | `/Applications` 无 `LibreOffice*.app`/`*Office*.app`；`find / -maxdepth 4 -name soffice` 无结果；`/opt/homebrew` 无 |
| `ebook-convert`（Calibre） | ⚠️ **存在但默认启动崩溃** | **calibre 9.15.0** ／ `/Applications/calibre.app/Contents/MacOS/ebook-convert`，同 `/opt/homebrew/bin/ebook-convert` | 裸跑 `--version` 抛 `calibre/utils/config_base.py` Traceback。**加 `CALIBRE_CONFIG_DIRECTORY=<可写目录>` 后正常**：`export CALIBRE_CONFIG_DIRECTORY=/tmp/calibre_cfg` → `ebook-convert (calibre 9.15.0)`。EPUB/MOBI/AZW3 互转可用 |
| macOS Vision OCR | ✅ | `Vision.framework` + Swift **6.3.3**（`/usr/bin/swiftc`） | 驱动脚本 `/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/ocr.swift`，我已编译并实测通过 |
| `/usr/bin/shortcuts` | ✅（无 OCR 指令） | macOS 26.6.2 | `shortcuts list` 返回空 |
| AutoClaw PDF-OCR skill | ✅（需凭据） | `pdfocr_SKILL.md` + `pdf-ocr.mjs` | 依赖 3 个环境变量，单次 ≤60 页 |

**python / 环境**：`/opt/homebrew/bin/python3` = Python 3.14.7（含 pymupdf 1.28.2、pypdf 6.16.1）；`python3`（PATH 解析到同一解释器）= 3.14.7；另有 `/Users/zenghui/ComfyUI/venv/bin/python3`（Python 3.11，含 Pillow/ebooklib，无 pymupdf）。
**brew 已装且相关**：`poppler`、`python@3.11`、`python@3.14`、`ffmpeg`、`libtiff`、`openjpeg`、`webp`、`llama.cpp`。**未装**：`mupdf`、`qpdf`、`tesseract`、`libreoffice`、`imagemagick`。

---

## 6. 未找到项（明确声明）

| 项 | 搜索范围 | 结果 |
|---|---|---|
| `.djvu` 格式书籍 | `/Volumes/My PSSD` 全递归、`/Users/zenghui/Downloads`、`/Users/zenghui/Documents`、全 `/Users/zenghui`（剪枝 Library/node_modules/.git/venv/site-packages/.Trash/Caches） | **未找到（0 个）** |
| 外盘 `books/` 之外的其他书籍目录 | `find "/Volumes/My PSSD" -type d \( -iname "*book*" -o -iname "*书籍*" -o -iname "*电子书*" -o -iname "*ebook*" \)` | 仅 `/Volumes/My PSSD/downlodData/books` 一个 |
| 其他卷宗中的书籍 | `/Volumes/ChatGPT Installer`、`/Volumes/DeepSeek Harness 0.2.0-rc.2-arm64`（`-maxdepth 4`） | **未找到** |
| 知识库 `书籍/` 目录下的原件 | 全目录递归 | **未找到任何 .pdf/.epub/.mobi/.azw3/.djvu**（只有 .md 与 `*图/`） |
| 缺 `-挖掘要点.md` 的书 | `ls *-挖掘要点.md` | **《威科夫经典合集》没有 `-挖掘要点.md`**（16 个要点文件对应 17 本书） |

**搜索方法说明**：报告开头提到的「全盘」为字面意义的全 home 扫描（`/Users/zenghui`，剪枝 `Library`、`node_modules`、`.git`、`venv`、`.venv`、`site-packages`、`.Trash`、`Caches`），命中 102 个 PDF/EPUB/MOBI/AZW3；系统级路径（`/System`、`/usr`、`/opt/homebrew` 的程序自带 PDF）未纳入书籍统计。外盘 `find` 全递归实测仅耗时 **2.586 s**，未做 `-maxdepth` 截断，结果完整。

---

## 7. 建议下一步（供委托方决策）

1. **不必重新 OCR**：6 本空壳书的全文与 85 张卡已在 `/Users/zenghui/.openclaw-autoclaw/workspace/.openclaw/tmp/books_extract/`，只需把 `*-挖掘要点.md` 回填到 `/Users/zenghui/Documents/stock/stock/知识库/书籍/`。
2. **临时目录有被清理的风险**（`/tmp` 语义的 `.openclaw/tmp`，且已有 2307 个子项）：建议优先把 `books_extract/` 归档到 `知识库/` 或外盘。
3. **需要真 OCR 的只剩 4 本**：笑傲股市（470p）、金融炼金术（362p）、理查德·D·威科夫操盘术（243p）、主动投资组合管理(中文)（396p）—— 其中笑傲股市、金融炼金术、威科夫合集**历史上已 OCR 完成**（见 §3.5），真正可能缺的只有 `主动投资组合管理(中文)`。
4. **改名**：`/Volumes/My PSSD/downlodData/books/15c019bc03a78f83fd2c323a.pdf` → 建议改为 `股票大作手回忆录(修订版-丁圣元译).pdf`。
5. **修复移动导致的路径失效**：知识库 3 个 .md 头部声明的 `downlodData/xxx.pdf` 现位于 `downlodData/books/xxx.pdf`（华尔街幽灵、笑傲股市、股市趋势技术分析）。
6. **2 本须「渲染+OCR」而非直接抽取**：主动投资组合管理(高清)、短线交易秘诀。工具就用现成的 `ocr.swift` + `pdftoppm`，OCR 后需过滤 `7help.net`/`shuyou066`/`fy10.com` 等水印行。
