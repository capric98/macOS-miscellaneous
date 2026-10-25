# macOS-Miscellaneous

面向 Apple Silicon 新 Mac 的配置仓库。使用一个 Bash 入口安装 Homebrew 软件、部署 Bash / Vim 配置、安装 ble.sh 和 Solarized，并放置 Karabiner 规则。

## 使用

下载或克隆完整仓库后，在原生终端运行。不要用 `sudo bash setup.sh`，也不要仅下载单个脚本；脚本会读取同目录下的配置文件。

```bash
cd macOS-miscellaneous
bash setup.sh --dry-run
# 先编辑并审核 Brewfile，再运行：
bash setup.sh
```

默认交互展示并确认安装清单。已经审核后，可用 `bash setup.sh --yes` 跳过这一次确认。Homebrew 安装、部分 cask、登录 shell 切换仍可能要求管理员密码或系统确认。

首次安装 Homebrew 时，其官方安装器会处理 Command Line Tools；按系统提示完成即可。无需预先安装新版 Bash，脚本可由 macOS 自带的 `/bin/bash` 启动。

清单及需确认的项目见 [Homebrew 审核说明](docs/homebrew-review.md)。`--dry-run` 不联网、不创建备份、不修改文件。

## 自动配置的内容

- 缺少时运行官方 Homebrew 安装器，使用 `/opt/homebrew`；通过 `Brewfile` 安装手动选择的软件，由 Homebrew 解析依赖。
- 安装 Homebrew Bash，注册到 `/etc/shells`，并设为当前用户的登录 shell；可用 `--no-change-shell` 跳过。
- 部署 `~/.bash_profile`、`~/.bashrc` 和当前一致的 `~/.blerc`。保留提示符、`cdf`、zoxide 的 `cd`、Bash 补全和 ble.sh 自动建议，并自动加入 `ffmpeg-full` 路径；交互配置不会影响非交互脚本。
- 安装与当前构建同一提交的 ble.sh `0.4.0-nightly+d81fd54`（本机源码构建标记为 `devel4+d81fd54`），固定下载文件并校验 SHA-256。
- 部署当前的 Solarized Light dircolors，使用 GNU `gls` 显示文件颜色。安装 iTerm2 动态配置 `Solarized Light (Bash)`，包含 Solarized 调色板和 Bash 登录命令。
- 原样部署当前 `~/.vimrc`，安装固定提交的 vim-plug，并用 `vim -N` 关闭批处理时的 vi 兼容模式，再同步执行 `PlugInstall --sync`，随后检查两个插件的文件是否存在。
- 安装 Karabiner 后，将两个规则文件放入 `~/.config/karabiner/assets/complex_modifications/`。不替换 `karabiner.json` 中已有的设备信息和已启用规则。

脚本不会安装旧的 aria2 / Helix / Flameshot 配置。软件清单已按审核决定移除 Flameshot、Shottr 和标准版 `ffmpeg`，仅保留 `ffmpeg-full`。脚本不会卸载当前机器上的软件。

## 安装后完成几步

1. 重新打开终端。iTerm2 的 **Profiles** 中选择 **Solarized Light (Bash)**；若要以后直接使用，在 Settings > Profiles 中将其设为默认。这样 ANSI dircolors 与终端调色板相互匹配。此脚本未配置 Terminal.app 的颜色。
2. 打开 Karabiner，按 macOS 提示授予输入监控、辅助功能及驱动所需权限，在 **Complex Modifications > Add predefined rule** 中按需启用规则。
3. 左 Shift 单击规则发出 Caps Lock，需要在系统输入法设置中开启 Caps Lock 切换输入源。iTerm2 的全局快捷键规则可能触发 macOS 自动化授权。规则文件按当前内容保留了 Shottr 映射，但清单已移除 Shottr，新机上可不启用这一条；以后使用它时，应用内快捷键需要设为 `Shift+Cmd+2`。

规则文件：

| 文件 | 内容 |
| --- | --- |
| `custom_shortcuts.json` | 12 条自定义规则，包含左 Option+E / D / L 和工作区切换；已移除标题和文件名中的个人账号 |
| `windows_shortcuts_on_macos.json` | 31 条 Windows 风格快捷键 |

Windows 风格的三个常用组合键按**键盘位置**使用左 Option（Alt）对应 Win 键，即 Mac 键盘左 Control 旁边的键。标准 PC 键盘上的实体 Win 键通常识别为 Command，两者的键码不同。

| 按键 | 功能 | `custom_shortcuts.json` 中的规则名称 |
| --- | --- | --- |
| `左 Option+E` | 打开 Finder 的个人文件夹 | `Left Option+E => Open Finder (Win+E)` |
| `左 Option+D` | 显示桌面，再按一次恢复窗口 | `Left Option+D => Show Desktop (Win+D)` |
| `左 Option+L` | 锁屏 | `Left Option+L => Lock Screen (Win+L)` |

将更新后的 `custom_shortcuts.json` 复制到 `~/.config/karabiner/assets/complex_modifications/`，在 Karabiner 的 **Complex Modifications > Add predefined rule** 中单独启用这三条。已启用的规则不会随仓库文件自动更新；先移除旧的 `Option + E to open Finder`，再添加新的 E / D / L 规则。无需为此重跑整个安装脚本。

三条规则允许 Caps Lock 开启；带 Shift、Command 或 Control 的组合不匹配，右 Option 不受影响。沿用 Windows 规则中的远程桌面和虚拟机排除列表，让这些应用自行处理快捷键。显示桌面使用 macOS 的 Command–Mission Control，锁屏使用 `Ctrl+Cmd+Q`，见 [Apple 快捷键说明](https://support.apple.com/zh-cn/102650)。

工作区切换：启用 `Ctrl+Left Option+Left/Right => Switch Desktop (Ctrl+Win+Left/Right)`，使用 **Control+左 Option+← / →** 切换上一个／下一个桌面。规则发送 macOS 原生的 `Control+← / →`；需在系统设置 > 键盘 > 键盘快捷键 > 调度中心中启用“向左移动一个空间”和“向右移动一个空间”，并保持其快捷键为 Control+左右方向键。先在调度中心创建多个桌面，或使用全屏应用形成的空间。

工作区规则支持左右 Control、允许 Caps Lock，沿用远程桌面和虚拟机排除列表。已有 Control+左右按词移动规则保持不变；Karabiner 输出的按键不会再次经过这些规则。

已移除标题为 `Ctrl+Tab => Cmd+Tab (Switch application)` 的旧规则；该规则实际匹配 Option+Tab / Option+Shift+Tab，删除后由应用自行处理。

Windows 规则文件中仍保留旧的 `Cmd+L => Logout (CGSession -suspend)`，它与左 Option+L 不同；建议禁用旧规则，避免占用应用原本的 Command+L（如浏览器地址栏）。

## 备份、重跑与个人信息

不同内容的现有配置会先备份到 `~/.local/state/macos-setup/backups/<时间>-<进程号>/`，按原相对路径保存。内容相同的文件会跳过；重复运行不会追加重复的 shell 配置或规则。安装失败可修复后重跑，已经安装的软件不需要重新安装。备份仅在本机，不放入仓库。

旧 Bash 文件会被备份后替换；需要保留的额外配置请从备份中挑选到 `~/.bashrc.local` / `~/.bash_profile.local`，它们在公共配置之后自动读取。不要直接加载整份旧 `.bashrc`，以免重复初始化 ble.sh。

Vim 安装失败时，详细诊断日志保存在 `~/.local/state/macos-setup/logs/`，权限为仅当前用户可读写。日志不会进入仓库；修复问题后可以重新运行脚本。

Git 和 SSH 的可选公共模板放在 `templates/`，脚本不会覆盖现有 Git / SSH 配置。Git 身份、SSH 密钥、服务器地址、代理认证和令牌只在本机设置：

```bash
git config --global user.name '你的名字'
git config --global user.email '你的邮箱'
git config --global credential.helper osxkeychain
```

有私有路径或代理设置时放入 `~/.bashrc.local`。需要临时在项目中保存私有内容时使用已忽略的 `local/`；`.gitignore` 也忽略原始 `.config/`、`.ssh/`、`.local` 配置及日志。忽略规则不能阻止 `git add -f`，提交前仍要检查 `git diff --cached`。本次整理不会重写旧 Git 历史。

其他选项：

```bash
bash setup.sh --review-packages
bash setup.sh --yes --skip-packages  # 已有 Homebrew 及核心工具时只配置
bash setup.sh --no-change-shell
bash setup.sh --help
```

## 目录

```text
setup.sh                     单一安装入口
Brewfile                     可人工审核的软件清单
config/
  bash/                      Bash 启动文件和 blerc
  vim/                       当前 vimrc
  karabiner/complex_modifications/
  dircolors-solarized/        当前 ANSI Light 文件及上游许可证
  iterm2/                    Solarized Light 动态配置及上游许可证
templates/                   无个人身份的 Git、SSH 示例
docs/homebrew-review.md       清单来源和审核重点
docs/sources.md               上游来源、固定版本
tests/                       在临时 HOME 中验证脚本行为
tools/resize-picture/         原图片处理工具，独立于初始化流程
tools/legacy/                原自定义 aria2 formula，仅归档，不自动安装
```

## 验证与建议

```bash
python3 -m unittest discover -s tests -v
for file in setup.sh config/bash/bash_profile config/bash/bashrc config/bash/blerc; do
    /bin/bash -n "$file" || break
done
```

建议将新机流程保持为“软件清单 + 公共配置 + 本机私有覆盖”。密码和 SSH 私钥通过密码管理器或其他可信方式迁移；截图、输入法和 Karabiner 系统权限保留为明确的安装后步骤。额外的 `defaults write` 系统偏好、Touch ID sudo、开机启动项可以后按需加入，避免每次 shell 启动都修改系统文件。
