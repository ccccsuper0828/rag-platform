import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // 将缺失的包重定向到虚拟模块
      "@radix-ui/react-slot": "/src/mock-ui.tsx",
      "class-variance-authority": "/src/mock-ui.tsx",
      "@radix-ui/react-dialog": "/src/mock-ui.tsx",
      "@radix-ui/react-dropdown-menu": "/src/mock-ui.tsx",
      "@radix-ui/react-popover": "/src/mock-ui.tsx",
      "lucide-react": "/src/mock-ui.tsx",
    },
  },
  optimizeDeps: {
    exclude: ["@radix-ui"], // 排除有问题的包
  },
});
