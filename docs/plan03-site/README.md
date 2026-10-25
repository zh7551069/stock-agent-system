# PLAN-03 交易策略多 Agent 架构 · VuePress 评审站

把《股票交易策略生成智能体系统 · 多 Agent 架构设计》（PLAN-03）做成可运行的 VuePress v2 站点，方便逐页查阅、检索与评审。

## 运行

```bash
# 1. 安装依赖（首次）
npm install

# 2. 安装 D2（架构图离线渲染，一次性）
brew install d2        # 或从 github.com/terrastruct/d2 下载二进制放到 PATH

# 3. 启动本地开发服务器（会先渲染 D2 图，热更新）
npm run docs:dev       # 默认 http://localhost:8080/

# 构建静态站点（渲染 D2 + 构建，输出到 docs/.vuepress/dist）
npm run docs:build
```

> 若本机 `~/.npm` 缓存目录无写权限，可加环境变量重定向：
> `npm_config_cache=/tmp/npm-cache npm_config_userconfig=/tmp/npmrc npm install`

## 图怎么画的（离线，无远程依赖）

- **架构图（总架构 / 评测管线 / 快慢双环）**：用 **D2** 声明式源码写在 `diagrams/*.d2`，构建时由 `scripts/render-d2.sh` 本地渲染成 SVG 到 `docs/.vuepress/public/diagrams/`，页面用 `![](/diagrams/xxx.svg)` 引用。**全程离线**，不依赖任何远程服务器。
- **流程图 / 时序图（决策生命周期 / 溯源图 / 抽象闭环）**：用 **Mermaid**，客户端本地渲染，跟随明暗主题。

## 目录结构

```
plan03-site/
├── package.json          # vuepress + bundler-vite + theme-default + mermaid
├── gen.py                # markdown 生成器（部分页面改为手维护，见下方说明）
├── diagrams/             # D2 架构图源码（.d2）
├── scripts/
│   └── render-d2.sh      # D2 → SVG 离线渲染
└── docs/
    ├── .vuepress/
    │   ├── config.mjs    # 站点配置：导航 / 侧边栏 / 暗色模式 / 搜索 / mermaid
    │   └── public/diagrams/   # 渲染产物 SVG（构建生成）
    ├── README.md         # 首页（设计原则）
    ├── overview.md       # 总架构（D2：上下文图 + 容器图）
    ├── agent-roster.md   # Agent 清单
    ├── tasks.md          # 14 任务映射
    ├── models.md         # 模型选型
    ├── lifecycle.md      # 决策生命周期时序图（Mermaid）
    ├── eval-platform.md  # 评测平台接入 + 可观测管线（D2）
    ├── observability.md  # 可观测平台设计
    ├── self-evolution.md # 自进化设计（D2 快慢双环 + Mermaid 溯源图）
    ├── protocol.md       # 交互协议约定
    ├── roadmap.md        # 落地路线
    └── risks.md          # 风险与反模式
```

## 说明

- 图：架构图用 D2 离线渲染（静态 SVG，白底卡片）；流程图/时序图用 Mermaid（本地渲染、随主题）。
- 主题：VuePress default theme，支持明/暗切换与本地搜索。
- `gen.py` 是历史引导脚本，现已不维护部分手改页（overview / observability / self-evolution / eval-platform 的图请直接改 `.md` 或 `diagrams/*.d2`）。
- 源文档：`docs/PLAN-03-trading-agent-architecture.html`（同目录，PLAN-03 v2）。
