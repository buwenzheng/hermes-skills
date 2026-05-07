# chsrc 换源工具

自动测速换源工具，为编程语言、系统、软件切换到国内最快镜像源。

## 使用方法

```bash
# 查看所有支持的目标
chsrc list targets

# 全自动换源（测速后选最快）
chsrc set <target>

# 手动指定镜像站
chsrc set <target> <code>

# 查看当前使用的源
chsrc get <target>

# 测速所有可用源
chsrc measure <target>
```

## 常用目标

- `pip` / `npm` / `yarn` / `pnpm` — Node.js 和 Python 包管理器
- `go` / `cargo` — Go 模块和 Rust crates
- `docker` / `brew` / `conda` — 容器和开发环境
- `ubuntu` / `debian` / `arch` — 操作系统

## 代理备选

chsrc 不支持的目标（如 git/github），可开启代理：
```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
# 用完后 unset http_proxy https_proxy
```

## 参考

- 项目地址：https://github.com/RubyMetric/chsrc
