# 内容块操作指南

## 内容块定义

内容块是思源笔记的基本单位，每个块通过全局唯一 ID 标识。

- **ID 格式**：`202008250000-a1b2c3d`（时间戳 + 7位随机字符）
- **唯一性**：整个笔记库中每个块的 ID 都是唯一的
- **层次结构**：块可以嵌套，形成文档树状结构

## 块类型代码

| 代码 | 类型 | 说明 |
|------|------|------|
| `d` | 文档块 | 根节点，代表整个文档 |
| `h` | 标题块 | h1~h6 |
| `p` | 段落块 | 普通文本段落 |
| `l` | 列表块 | 有序/无序/任务列表容器 |
| `i` | 列表项块 | 列表中的单个项目 |
| `b` | 引述块 | 引用块容器 |
| `callout` | 提示块 | 提示/警告/说明框 |
| `s` | 超级块 | 块组容器 |
| `c` | 代码块 | 代码片段 |
| `m` | 公式块 | 数学公式 |
| `t` | 表格块 | 表格 |
| `av` | 数据库块 | 属性视图数据库 |
| `query_embed` | 嵌入块 | SQL 查询嵌入 |

### 子类型

- **列表块/列表项块**：`o`（有序）、`u`（无序）、`t`（任务）
- **标题块**：`h1` ~ `h6`
- **提示块**：`NOTE`、`TIP`、`IMPORTANT`、`WARNING`、`CAUTION`

## 块引用语法

```markdown
((块ID "静态锚文本"))   -- 静态锚文本，不跟随块内容变化
((块ID '动态锚文本'))   -- 动态锚文本，跟随块内容变化
((块ID))                -- 使用块内容作为锚文本
```

### 使用示例

```markdown
# 创建引用
((20210808180117-czj9bvb "这是引用"))
((20210808180117-czj9bvb '这是引用'))
((20210808180117-czj9bvb))
```

## 嵌入块语法

```sql
{{ SELECT * FROM blocks WHERE content LIKE '%关键字%' }}
```

### 常用查询

```sql
-- 查询包含关键字的块
{{ SELECT * FROM blocks WHERE content LIKE '%关键字%' }}

-- 查询特定类型的块
{{ SELECT * FROM blocks WHERE type = 'i' AND content LIKE '%内容块%' }}

-- 查询最近更新的标题
{{ SELECT * FROM blocks WHERE type = 'h' ORDER BY updated DESC LIMIT 5 }}

-- 查询未完成任务
{{ SELECT * FROM blocks WHERE markdown LIKE '%- [ ]%' }}

-- 随机漫游
{{ SELECT * FROM blocks ORDER BY random() LIMIT 1 }}
```

## blocks 表结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT | 内容块 ID（主键） |
| `parent_id` | TEXT | 父块 ID |
| `root_id` | TEXT | 根块 ID（即文档块 ID） |
| `box` | TEXT | 笔记本 ID |
| `path` | TEXT | 文档路径 |
| `hpath` | TEXT | 人类可读路径 |
| `name` | TEXT | 内容块名称 |
| `alias` | TEXT | 内容块别名 |
| `memo` | TEXT | 内容块备注 |
| `content` | TEXT | 去除 Markdown 标记的纯文本 |
| `markdown` | TEXT | 包含完整 Markdown 的文本 |
| `type` | TEXT | 内容块类型 |
| `subtype` | TEXT | 内容块子类型 |
| `created` | INTEGER | 创建时间（格式：YYYYMMDDHHmmss） |
| `updated` | INTEGER | 更新时间 |

## 内容块属性

### 系统属性

| 属性名 | 描述 |
|--------|------|
| `name` | 内容块命名 |
| `alias` | 内容块别名 |
| `memo` | 内容块备注 |
| `bookmark` | 书签标记 |

### 自定义属性

命名规则：仅允许小写字母和数字，必须以字母开头。系统自动添加 `custom-` 前缀。

```markdown
{: custom-priority="1" custom-status="doing"}
```

### 属性查询

```sql
-- 单属性查询
SELECT * FROM blocks WHERE id IN (
    SELECT block_id FROM attributes
    WHERE name = 'custom-priority' AND value = '1'
);
```

## 最佳实践

1. **使用动态锚文本**：需要锚文本跟随引用内容自动更新时
2. **使用静态锚文本**：需要锚文本固定不变时，如文档索引
3. **合理命名**：给重要块设置 `name` 属性，便于引用和管理
4. **避免重复操作**：创建前先检查是否已存在
