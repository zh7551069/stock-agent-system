import { defineClientConfig } from "vuepress/client";
import Mermaid from "/Users/zenghui/.dsh/im/plan03-site/node_modules/@vuepress/plugin-markdown-chart/lib/client/components/Mermaid.js";

export default defineClientConfig({
  enhance: ({ app }) => {
    app.component("Mermaid", Mermaid);
  },
});
