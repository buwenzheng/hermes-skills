---
name: automation-hub
version: 1.2.1
description: >
  家庭 NAS 自动化任务管理中心。管理所有定时脚本、签到、监控、汇总类任务。
  包含命名规范、任务清单、脚本模板。创建 cron job、定时签到、自动脚本、
  监控告警、定期维护前必须加载此 skill。
category: devops
required_environment_variables: []
---

# 自动化任务管理中心

## When to Use

创建或修改定时脚本、签到任务、监控告警、定期维护类 cron job 前必须加载此 skill。也适用于排查已有任务的命名、目录、推送目标等问题时参考。

## 初始化

本 skill 为参考/管理类 skill，无需额外初始化步骤。创建任务前确保 `~/.hermes/scripts/automation/` 目录存在：

```bash
mkdir -p ~/.hermes/scripts/automation/
```

## 目录约定

```
~/.hermes/scripts/automation/     # 所有脚本放这里
~/.hermes/skills/automation-hub/  # 本 skill 目录
```

脚本统一放在 `~/.hermes/scripts/automation/` 下，skill 里通过 `cronjob script` 参数指向。

## 命名规范

格式：`{分类}_{功能名}`，全小写，下划线分隔

| 分类前缀 | 含义 | 示例 |
|----------|------|------|
| `signin_` | 签到类 | `signin_mt`、`signin_ttg` |
| `monitor_` | 监控/告警类 | `monitor_disk`、`monitor_download` |
| `report_` | 汇总报告类 | `report_daily` |
| `maint_` | 定期维护类 | `maint_cache_cleanup` |

## 任务分类

### 纯脚本（no_agent=True）
- 不消耗 token，脚本 stdout 直接推送
- 适合：签到、监控、清理等固定逻辑任务
- 脚本自身要处理好输出：有结果就输出，无事可报则静默

### Agent 驱动（默认）
- 消耗 token，agent 脚本跑完后整理总结
- 适合：需要判断逻辑、多源汇总的任务
- prompt 要自包含，cron 运行无对话上下文

## 创建任务流程

1. 确认任务类型（纯脚本 / Agent 驱动）
2. 编写脚本，放到 `~/.hermes/scripts/automation/`
3. 用 `cronjob` 工具创建，填好 name、schedule、script/prompt
4. 更新本 skill 的任务清单
5. 用 `cronjob run` 手动触发一次验证

## 任务清单

| 名称 | 分类 | 调度 | 方式 | 说明 | 状态 |
|------|------|------|------|------|------|
| clash_update | maint | 0 3 */3 * * | 纯脚本 | Clash 订阅配置更新 | ✅ 运行中 |
| maint_orphan_scraper_cleanup | maint | 0 4 * * 0 | 纯脚本 | 飞牛影视删片后的刮削残留目录回收（.nfo/.jpg 等无视频文件的目录）→ 回收站 7 天后清理 | ✅ 运行中 |

> 新增任务后必须更新此表。删除任务时同步清理。

## 推送目标

不同 cron job 可推送到不同渠道（飞书群、Telegram 等）。
目标列表维护在 `references/chat_targets.md`，创建 job 时查阅此文件确定 deliver 参数。

deliver 格式：`feishu:<chat_id>`、`telegram:<chat_id>`、`origin`（当前对话）等。

## 常见陷阱（Common Pitfalls）

1. **cronjob script 路径必须是相对路径**：相对于 `~/.hermes/scripts/`，不能用绝对路径或 `~` 开头。
   - ✅ `automation/clash_update.sh`
   - ❌ `~/.hermes/scripts/automation/clash_update.sh`
   - ❌ `/home/hermes/.hermes/scripts/automation/clash_update.sh`
2. **no_agent 脚本的 stdout = 推送内容**：脚本输出什么就推什么，无输出则不推送。确保脚本在成功/失败时都有清晰输出。
3. **cron 环境网络可能不同**：脚本直接跑通不代表 cron 环境也能跑通，首次创建后务必用 `cronjob run` 手动验证。
4. **删除/清理类脚本必须先 dry-run 给用户审阅**：任何会删除文件、移动到回收站、清空目录的脚本，第一次跑必须输出"待删除清单"让用户确认，不能直接执行删除。
   - ✅ 先列出"扫描到 N 个目录，路径如下：..."，让用户看清楚再确认
   - ❌ 直接跑 `rm -rf` 或 `mv 到回收站`，事后才告诉用户删了什么
   - 推荐做法：脚本加 `DRY_RUN=1` 环境变量，默认 dry-run，确认后再去掉

## 脚本模板

纯脚本模板见 `references/templates/script_template.sh`。

## 参考资料

- 推送目标列表：`references/chat_targets.md`
- JD 签到脚本独立运行说明：`references/jd-signin-notes.md`
