# Homebrew 安装清单审核

清单保存在根目录 `Brewfile`，根据 2026-10-24 本机的 Homebrew 安装记录整理，并已按使用者审核结果移除标准版 `ffmpeg`、Flameshot 和 Shottr。最终保留 12 个 formula、17 个 cask。脚本不会重新导出并覆盖审核决定。

Formula 候选使用 `brew list --formula --installed-on-request`，原始共 13 项。没有使用单独的 `brew leaves`：例如 Bash、Python 虽然被其他软件依赖，也有手动安装标记，应当保留。其他纯依赖交给 Homebrew 自动解析。

| Formula | 用途 / 审核说明 |
| --- | --- |
| `bash` | 本配置需要：新版 Bash、ble.sh 自动补全 |
| `bash-completion@2` | 本配置需要：Bash 补全 |
| `cloc` | 代码行数统计 |
| `coreutils` | 本配置需要：GNU `gls`、`gdircolors` |
| `ffmpeg-full` | 按审核决定仅保留 full；Bash 配置自动加入其 keg-only 路径 |
| `gawk` | 本配置保留：ble.sh 使用的 GNU awk |
| `mactop` | 系统监控 |
| `python@3.15` | 当前手动安装的 Python 版本，同时被 `yt-dlp` 依赖 |
| `ripgrep` | 文本搜索 |
| `uv` | Python 环境和包管理 |
| `yt-dlp` | 媒体下载 |
| `zoxide` | 本配置需要：增强 `cd` |

17 项 Cask：

| 分类 | Cask |
| --- | --- |
| 终端和开发 | `iterm2`、`visual-studio-code`、`codex`、`claude-code@latest` |
| 系统和输入 | `appcleaner`、`betterdisplay`、`input-source-pro`、`karabiner-elements`、`onyx`、`stats` |
| 网络和远程 | `clash-verge-rev`、`rustdesk` |
| 笔记和密码 | `obsidian`、`keepassxc` |
| 字体 | `font-fira-code`、`font-fira-code-nerd-font`、`font-source-sans-3` |

已确认的选择：

1. 只安装 `ffmpeg-full`，不安装标准版 `ffmpeg`；不使用强制链接，直接配置 PATH。
2. 不安装 Flameshot 和 Shottr，也不迁移 Flameshot 配置。
3. `claude-code@latest` 保留当前安装的通道名。

最终清单没有第三方 tap。Flameshot 移除后不再需要其 tap；本机的另一个 tap 没有对应已安装软件，也不迁移。脚本不会卸载当前机器已有的软件或 tap。

审核命令：

```bash
bash setup.sh --review-packages
bash setup.sh --dry-run
```

以后更新清单时，先查看 `brew list --formula --installed-on-request`、`brew list --cask` 和 `brew tap`。第三方软件应使用完整 token，可从 `brew info --json=v2 --installed` 的 `full_name` / `full_token` 核对；不要把原始 JSON 导出提交到仓库。

`brew bundle install --no-upgrade` 不主动升级已满足的项目，但 Homebrew 为满足新安装软件的依赖仍可能更新相关依赖。清单没有锁死 Homebrew 软件版本。
