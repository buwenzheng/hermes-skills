---
name: chsrc
description: chsrc 换源工具，通过自动测速为各种编程语言/OS/软件切换到国内最快镜像源
version: 1.0.1
category: productivity
---

# chsrc 换源工具

## 简介

`chsrc`（Change Source）是一个自动测速换源工具，支持编程语言、系统、软件的镜像源切换。通过测速自动挑选最快源，也支持手动指定。

## 基础命令

| 命令 | 作用 |
|---|---|
| `chsrc list targets` | 查看所有支持换源的目标 |
| `chsrc list <target>` | 查看某目标的所有可用源 |
| `chsrc measure <target>` | 对目标所有源测速 |
| `chsrc get <target>` | 查看当前使用的源 |
| `chsrc set <target>` | 全自动换源（测速后选最快） |
| `chsrc set <target> first` | 使用维护团队测速第一的源 |
| `chsrc set <target> <code>` | 指定镜像站（通过 `list <target>` 查看 code） |
| `chsrc set <target> <URL>` | 使用自定义 URL |
| `chsrc reset <target>` | 重置回上游默认源 |

## 常用选项

| 选项 | 作用 |
|---|---|
| `-dry` | 模拟换源，不实际执行 |
| `-scope=project\|user\|system` | 项目级/用户级/系统级换源 |
| `-ipv6` | 使用 IPv6 测速 |
| `-en` | 英文输出 |
| `-no-color` | 无颜色输出 |

## 支持的目标（部分）

### 编程语言/工具
`pip` `python` `npm` `yarn` `pnpm` `node` `go` `cargo` `maven` `gem` `flutter` `dart` `bun` `pnpm` `uv` `rye` `poetry` 等

### 操作系统
`ubuntu` `debian` `arch` `archlinuxcn` `manjaro` `fedora` `alpine` `deepin` `termux` 等

### 软件
`brew` `docker` `conda` `flatpak` `winget` `cocoapods` 等

## 使用场景

### 1. npm / npx 下载慢
```bash
chsrc set npm          # 全自动测速换源
chsrc set npm npmmirror  # 手动指定阿里 npmmirror
```

### 2. pip 安装慢
```bash
chsrc set pip
```

### 3. Docker 镜像拉取慢
```bash
chsrc set docker
```

### 4. Go 模块拉取慢
```bash
chsrc set go
```

### 5. Rust crates 拉取慢
```bash
chsrc set cargo
```

### 6. 查某个目标有哪些镜像可用
```bash
chsrc list npm    # 查看 npm 所有可用源和代码
chsrc list pip    # 查看 pip 所有可用源
chsrc list conda  # 查看 conda 所有可用源
```

## 常用镜像站代码（通过 `chsrc list mirror` 查看完整列表）

| code | 镜像站 |
|---|---|
| `npmmirror` | 阿里云 npmmirror |
| `tuna` | 清华 TUNA |
| `ustc` | 中科大 |
| `ali` | 阿里云 |
| `tencent` | 腾讯软件源 |
| `huawei` | 华为开源镜像站 |
| `rsproxycn` | 字节跳动 RsProxy |

## 何时使用

- 用户说"XX 下载慢"、"XX 换源"、"切换到国内源"
- npm / pip / go / cargo 等包管理器下载卡顿
- Docker 镜像拉取超时
- 查某个目标有哪些镜像可用

## 初始化

无。chsrc 为命令行工具，直接安装即可：

```bash
# macOS / Linux 一键安装
curl -fsSL https://chsrc.top/chsrc.sh | sh

# 或用 npm 安装
npm install -g chsrc
```

## 避坑

- chsrc **不支持 git/github 直接换源**，但可以通过 `chsrc set npm` 改善 `npx skills add` 等依赖 npm 的工具的下载速度
- `npx skills add` 失败时，可先 `chsrc set npm` 换源再重试
- 换源前可先用 `chsrc measure <target>` 测速看看各源速度
- 系统级换源（`-scope=system`）需要 root 权限
- chsrc 不支持的目标（git/github）需用代理

## 参考

- 项目地址：https://github.com/RubyMetric/chsrc
- 版本：v0.2.5.1
