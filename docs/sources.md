# 配置和下载来源

- Homebrew：[官方安装说明](https://docs.brew.sh/Installation.html)、[Brew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile)、[命令手册](https://docs.brew.sh/Manpage)。安装器从官方 `Homebrew/install/HEAD/install.sh` 下载后执行；安装器随上游更新，未固定提交。
- ble.sh：[上游仓库](https://github.com/akinomyoga/ble.sh)、[官方 Releases](https://github.com/akinomyoga/ble.sh/releases)。使用与当前安装同一提交的 `ble-nightly-20260908+d81fd54.tar.xz`；压缩包版本标记为 `0.4.0-nightly+d81fd54`，当前本机源码构建标记为 `0.4.0-devel4+d81fd54`。SHA-256 写在 `setup.sh` 中；采用官方推荐的 `--attach=none` / `ble-attach` 加载方式。
- vim-plug：[上游仓库](https://github.com/junegunn/vim-plug)。固定提交 `7e5aae5e1187842cb0b1d8def986e48d481c4410`，校验下载的 `plug.vim`。两个 Vim 插件按当前 `.vimrc` 中的上游仓库安装，未固定插件提交。
- Vim 批处理：使用 [`-N` 启动选项](https://vimhelp.org/starting.txt.html#-N) 关闭 vi 兼容模式，确保重跑时可以加载已安装插件的 Vim 脚本语法。
- GNU ls 配色：[seebi/dircolors-solarized](https://github.com/seebi/dircolors-solarized)，从当前本机配置中复制 `dircolors.ansi-light`，本机来源提交 `bd9d473393a78366d5c3658d9cd2db7d8944b447`。MIT 许可证随配置文件保存。
- iTerm2 调色板：[altercation/solarized](https://github.com/altercation/solarized/tree/master/iterm2-colors-solarized)。使用官方 Solarized Light 调色板构建不含个人信息的动态配置，上游许可证保存在 `config/iterm2/LICENSE`。动态配置位置和字段见 [iTerm2 文档](https://iterm2.com/documentation-dynamic-profiles.html)。
- Karabiner：复制当前两个规则文件，将自定义规则标题及文件名中的个人账号改为通用名称；自定义规则按键盘位置使用左 Option+E 打开 Finder、左 Option+D 显示桌面、左 Option+L 发送 Control+Command+Q 锁屏。新增 Control+左 Option+左右方向键到原生 Control+左右方向键的工作区切换映射。移除标题为 Ctrl+Tab、实际匹配 Option+Tab 的应用切换规则。放置位置和启用方式见 [官方文件位置说明](https://karabiner-elements.pqrs.org/docs/json/location/)。
- 标签页操作：Ctrl+T 映射覆盖 Chrome（含 Beta、Dev、Canary）、系统 Terminal 和 iTerm2，Ctrl+Shift+T 恢复标签页仅覆盖 Chrome；Ctrl 点击映射限定在 Chrome 和 Finder 中。Chrome 标签页及点击规则保留可选的 Shift，终端新建标签页不匹配 Shift；修饰键行为见 [Karabiner 官方说明](https://karabiner-elements.pqrs.org/docs/json/complex-modifications-manipulator-definition/from/modifiers/)。Chrome 的恢复标签页、后台／前台打开链接组合见 [Google 官方快捷键说明](https://support.google.com/chrome/answer/157179?hl=zh-Hans)。鼠标默认不参与映射，需按 [Karabiner 鼠标说明](https://karabiner-elements.pqrs.org/docs/help/how-to/mouse-button/) 为所用设备开启 Modify events。
- Finder 按键：Windows 规则移除 Finder 中 Return 打开、Delete 移到废纸篓和 Backspace 返回上一级三条映射，避免重命名输入时被改写；新增 Shift+Delete 发送 Command+Delete 移到废纸篓。必选修饰键不会带入输出按键，见上述 Karabiner 修饰键说明；Finder 原生组合见 [Apple 快捷键说明](https://support.apple.com/zh-cn/102650)。
- Finder 剪切移动：Finder 中 Ctrl+X 发送 Command+C 并设置变量，Ctrl+V 在变量为 1 时发送原生的 Command+Option+V 移动项目；Finder 中的 Ctrl+C 及任意应用中的 Command+C / Command+X 清除变量。变量用法见 [Karabiner set_variable 说明](https://karabiner-elements.pqrs.org/docs/json/complex-modifications-manipulator-definition/to/set-variable/)，规则须排在全局 Ctrl+C / V / X 规则之前，见 [规则优先级说明](https://karabiner-elements.pqrs.org/docs/json/complex-modifications-manipulator-evaluation-priority/)。

- Flameshot：2026-11-07 从本机 `~/.config/flameshot/flameshot.ini` 保存配置，包含关闭截图帮助列表；仅将个人截图路径替换为导入时生成的目录。可选安装使用上游 [macOS Homebrew 说明](https://github.com/flameshot-org/flameshot#macos) 中的官方 tap 与完整 cask token，不放入默认 `Brewfile`。
- mpv app：[capric98/homebrew-mpv-app](https://github.com/capric98/homebrew-mpv-app)，沿用本机安装的 `capric98/mpv-app/mpv-app`。该个人 tap 使用 [mpv 项目稳定版发布包](https://github.com/mpv-player/mpv/releases)，不会自动移除 quarantine。mpv 配置、快捷键和脚本选项从本机 `~/.config/mpv/` 原样保存。
- ModernZ OSC：[Samillion/ModernZ v0.3.3](https://github.com/Samillion/ModernZ/tree/v0.3.3)，保存本机 `scripts/modernz.lua` 和 `fonts/modernz-icons.ttf`，不会在安装时下载更新版主题。脚本的 LGPL-2.1 许可证保存在 `config/mpv/licenses/`。
- 中文及等宽字体：[Adobe Source Han Sans](https://github.com/adobe-fonts/source-han-sans) 的可变字体和 FiraCode Nerd Font 通过可选清单中的 `font-source-han-sans-vf`、`font-fira-code-nerd-font` 安装。ModernZ 和统计面板统一使用 `Source Han Sans SC VF Medium`，仓库仅保存主题专用的 `modernz-icons.ttf`，不打包思源黑体 OTF。

后续修改固定下载版本时，须重新下载官方文件、核对版本并更新 SHA-256，不要关闭校验。Homebrew 安装的软件及 Vim 插件未完全锁定版本，因此该仓库复现的是配置和软件选择。
