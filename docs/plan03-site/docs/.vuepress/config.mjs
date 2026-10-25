import { viteBundler } from '@vuepress/bundler-vite'
import { defaultTheme } from '@vuepress/theme-default'
import { markdownChartPlugin } from '@vuepress/plugin-markdown-chart'

export default {
  lang: 'zh-CN',
  title: 'PLAN-03 · 交易策略多 Agent 架构',
  description: '股票交易策略生成智能体系统 · 多 Agent 架构设计',
  head: [
    ['meta', { name: 'color-scheme', content: 'light dark' }],
  ],
  bundler: viteBundler(),
  plugins: [
    markdownChartPlugin({ mermaid: true }),
  ],
  theme: defaultTheme({
    colorMode: 'auto',
    colorModeSwitch: true,
    navbar: [
      { text: '总架构', link: '/overview.html' },
      { text: 'Agent 清单', link: '/agent-roster.html' },
      { text: '提示词与模式', link: '/agent-prompts.html' },
      { text: '任务映射', link: '/tasks.html' },
      { text: '模型选型', link: '/models.html' },
      { text: '数据口径契约', link: '/caliber-contract.html' },
      { text: '生命周期', link: '/lifecycle.html' },
      { text: '评测与可观测', link: '/eval-platform.html' },
      { text: '可观测平台设计', link: '/observability.html' },
      { text: '评估器设计', link: '/evaluator.html' },
      { text: '评测集设计', link: '/eval-dataset.html' },
      { text: '自进化设计', link: '/self-evolution.html' },
      { text: '协议', link: '/protocol.html' },
      { text: '落地路线', link: '/roadmap.html' },
      { text: '风险与反模式', link: '/risks.html' },
    ],
    sidebar: [
      { text: '导读', children: ['/README.md', '/overview.md'] },
      { text: '组织', children: ['/agent-roster.md', '/agent-prompts.md', '/tasks.md', '/models.md'] },
      { text: '运行', children: ['/lifecycle.md', '/eval-platform.md', '/observability.md', '/protocol.md', '/caliber-contract.md', '/p0-spec.md', '/deterministic-core.md'] },
      { text: '演进', children: ['/evaluator.md', '/eval-dataset.md', '/self-evolution.md', '/roadmap.md', '/risks.md'] },
    ],
    sidebarDepth: 1,
  }),
}
