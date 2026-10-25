export const redirects = JSON.parse("{}")

export const routes = Object.fromEntries([
  ["/", { loader: () => import(/* webpackChunkName: "index.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/README.md"), meta: {"title":"股票交易策略生成智能体系统"} }],
  ["/agent-prompts.html", { loader: () => import(/* webpackChunkName: "agent-prompts.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/agent-prompts.md"), meta: {"title":"Agent 系统提示词与工作模式"} }],
  ["/agent-roster.html", { loader: () => import(/* webpackChunkName: "agent-roster.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/agent-roster.md"), meta: {"title":"Agent 清单（13 个运行时 Agent）"} }],
  ["/caliber-contract.html", { loader: () => import(/* webpackChunkName: "caliber-contract.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/caliber-contract.md"), meta: {"title":"数据口径契约 v1（实库校准）"} }],
  ["/eval-dataset.html", { loader: () => import(/* webpackChunkName: "eval-dataset.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/eval-dataset.md"), meta: {"title":"评测集设计（评什么）"} }],
  ["/eval-platform.html", { loader: () => import(/* webpackChunkName: "eval-platform.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/eval-platform.md"), meta: {"title":"评测平台接入与可观测性"} }],
  ["/evaluator.html", { loader: () => import(/* webpackChunkName: "evaluator.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/evaluator.md"), meta: {"title":"评估器设计（过程评估）"} }],
  ["/lifecycle.html", { loader: () => import(/* webpackChunkName: "lifecycle.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/lifecycle.md"), meta: {"title":"决策生命周期"} }],
  ["/models.html", { loader: () => import(/* webpackChunkName: "models.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/models.md"), meta: {"title":"模型选型（DeepSeek + 智谱）"} }],
  ["/observability.html", { loader: () => import(/* webpackChunkName: "observability.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/observability.md"), meta: {"title":"可观测平台设计（借鉴 AI Vision）"} }],
  ["/overview.html", { loader: () => import(/* webpackChunkName: "overview.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/overview.md"), meta: {"title":"总架构"} }],
  ["/protocol.html", { loader: () => import(/* webpackChunkName: "protocol.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/protocol.md"), meta: {"title":"多 Agent 交互协议约定（任务 8）"} }],
  ["/risks.html", { loader: () => import(/* webpackChunkName: "risks.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/risks.md"), meta: {"title":"风险与反模式（来自已踩过的坑）"} }],
  ["/roadmap.html", { loader: () => import(/* webpackChunkName: "roadmap.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/roadmap.md"), meta: {"title":"落地路线（先判决器，后决策面）"} }],
  ["/self-evolution.html", { loader: () => import(/* webpackChunkName: "self-evolution.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/self-evolution.md"), meta: {"title":"自进化设计（借鉴 MemRL）"} }],
  ["/tasks.html", { loader: () => import(/* webpackChunkName: "tasks.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/tasks.md"), meta: {"title":"16 项任务 → Agent 映射"} }],
  ["/404.html", { loader: () => import(/* webpackChunkName: "404.html" */"/Users/zenghui/.dsh/im/plan03-site/docs/.vuepress/.temp/pages/404.html.vue"), meta: {"title":""} }],
]);
