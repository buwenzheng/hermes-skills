# 思源笔记模板开发指南

## 概述

模板文件存储在 `data/templates/` 目录下，使用 `.md` 后缀，基于 Go 模板语法。

**重要**：思源笔记模板使用 `.action{}` 语法而非 `{{}}`，避免与 Markdown 语法冲突。

## 基本语法

```template
.action{ 变量或表达式 }
```

示例：
```template
当前文档标题：.action{ .title }
当前时间：.action{ now | date "2006-01-02" }
```

## 变量赋值

```template
.action{ $today := now | date "2006-01-02" }
今天的日子是 .action{ $today }
```

## 条件判断

```template
.action{ if eq (now | WeekdayCN) "日" }
今天是周日
.action{ else }
今天是工作日
.action{ end }
```

## 循环

```template
.action{ range $blocks }
- ((.action{ .id }))
.action{ end }
```

## 日期格式化

Go 日期格式化使用固定时间 `2006-01-02 15:04:05`：

| 格式 | 说明 | 示例值 |
|------|------|--------|
| 2006 | 四位年份 | 2026 |
| 01 | 两位月份 | 01-12 |
| 02 | 两位日期 | 01-31 |
| 15 | 24小时制 | 00-23 |

```template
.action{ now | date "2006-01-02" }           # 2026-01-25
.action{ now | date "2006年01月02日" }        # 2026年01月25日
.action{ now | date "2006-01-02 15:04" }      # 2026-01-25 12:30
```

## 内置变量

| 变量 | 说明 | 示例 |
|------|------|------|
| title | 当前文档名 | 我的文档 |
| id | 当前文档 ID | 20250101120000-abc123 |
| name | 当前文档命名 | My Document |
| alias | 当前文档别名 | my-document |

## 内置函数

### 数据库查询

```template
.action{ $blocks := queryBlocks "SELECT * FROM blocks WHERE content LIKE '?' LIMIT ?" "%关键词%" "3" }
.action{ range $blocks }
- ((.action{ .id )) .action{ .content }
.action{ end }
```

### 块统计

```template
.action{ $stats := statBlock .id }
- 字符数：.action{ $stats.RuneCount }
- 字数：.action{ $stats.WordCount }
```

### 时间函数

```template
.action{ now | WeekdayCN }     # 日、一、二、三、四、五、六
.action{ now | ISOWeek }       # 当前周数
.action{ now | ISOWeekDate 3 | date "2006-01-02" }   # 本周三
```

## Sprig 函数库

支持字符串、日期、数学等函数：

```template
.action{ "  Hello  " | trim }     # "Hello"
.action{ "hello" | upper }         # "HELLO"
.action{ add 1 2 }                  # 3
```

## 完整示例

### 日期计算模板

```template
.action{ $before := (div (now.Sub (toDate "2006-01-02" "2020-02-19")).Hours 24) }

# 日期统计

今天是 .action{ now | date "2006-01-02" }。

距离 2020-02-19 已经过去 .action{ $before } 天
当前是第 .action{ now | ISOWeek } 周
今天是 .action{ now | WeekdayCN }
```

### 周报模板

```template
.action{ $today := now }
.action{ $monday := $today | ISOWeekDate 1 }
.action{ $sunday := $today | ISOWeekDate 0 }

# 周报 (.action{ $monday | date "2006-01-02" } ~ .action{ $sunday | date "2006-01-02" })

## 工作内容
### 本周完成
-

### 下周计划
-

## 问题与风险
-

## 总结
本周第 .action{ $today | ISOWeek } 周。
```

## 调用模板

在思源笔记编辑器中：

1. 输入 `/`
2. 选择"插入模板"
3. 从模板列表中选择需要的模板

## 注意事项

1. **语法差异**：始终使用 `.action{}` 而非 `{{}}`
2. **日期格式**：牢记 `2006-01-02 15:04:05` 这个特殊时间格式
3. **SQL 注入**：使用 `?` 占位符来防止 SQL 注入
4. **性能**：复杂查询建议限制结果数量
