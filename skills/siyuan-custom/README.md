# 思源笔记（SiYuan）

思源笔记是基于内容块的隐私优先知识管理工具，本 skill 提供核心操作指南。

## 功能

- 内容块操作（插入、更新、删除、移动、块引用）
- 文档/笔记本管理（创建、搜索、重命名、导出）
- 模板渲染（标准模板 + Sprig 函数）
- 闪卡系统查询
- 工作区文件读写

## 使用

```
当用户询问思源笔记的概念、API、块操作、模板开发或配置时
```

## 初始化

```bash
python3 scripts/siyuan_api.py init <API URL> <Token>
# 例如：
python3 scripts/siyuan_api.py init http://127.0.0.1:6806 your_token_here
```

## 目录结构

```
siyuan/
├── SKILL.md                    # 主文件
├── README.md                   # 本文件
├── scripts/
│   ├── siyuan_api.py          # API 封装脚本
│   └── siyuan_config.json.template  # 配置模板
└── references/                 # 参考文档
    ├── block.md
    ├── template.md
    ├── api.md
    └── flashcard.md
```
