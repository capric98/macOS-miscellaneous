# 配置和下载来源

- Homebrew：[官方安装说明](https://docs.brew.sh/Installation.html)、[Brew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile)、[命令手册](https://docs.brew.sh/Manpage)。安装器从官方 `Homebrew/install/HEAD/install.sh` 下载后执行；安装器随上游更新，未固定提交。
- ble.sh：[上游仓库](https://github.com/akinomyoga/ble.sh)、[官方 Releases](https://github.com/akinomyoga/ble.sh/releases)。使用与当前安装同一提交的 `ble-nightly-20260908+d81fd54.tar.xz`；压缩包版本标记为 `0.4.0-nightly+d81fd54`，当前本机源码构建标记为 `0.4.0-devel4+d81fd54`。SHA-256 写在 `setup.sh` 中；采用官方推荐的 `--attach=none` / `ble-attach` 加载方式。
- vim-plug：[上游仓库](https://github.com/junegunn/vim-plug)。固定提交 `7e5aae5e1187842cb0b1d8def986e48d481c4410`，校验下载的 `plug.vim`。两个 Vim 插件按当前 `.vimrc` 中的上游仓库安装，未固定插件提交。
- Vim 批处理：使用 [`-N` 启动选项](https://vimhelp.org/starting.txt.html#-N) 关闭 vi 兼容模式，确保重跑时可以加载已安装插件的 Vim 脚本语法。
- GNU ls 配色：[seebi/dircolors-solarized](https://github.com/seebi/dircolors-solarized)，从当前本机配置中复制 `dircolors.ansi-light`，本机来源提交 `bd9d473393a78366d5c3658d9cd2db7d8944b447`。MIT 许可证随配置文件保存。
- iTerm2 调色板：[altercation/solarized](https://github.com/altercation/solarized/tree/master/iterm2-colors-solarized)。使用官方 Solarized Light 调色板构建不含个人信息的动态配置，上游许可证保存在 `config/iterm2/LICENSE`。动态配置位置和字段见 [iTerm2 文档](https://iterm2.com/documentation-dynamic-profiles.html)。
- Karabiner：复制当前两个规则文件，将自定义规则标题及文件名中的个人账号改为通用名称；自定义规则按键盘位置使用左 Option+E 打开 Finder、左 Option+D 显示桌面、左 Option+L 发送 Control+Command+Q 锁屏。移除标题为 Ctrl+Tab、实际匹配 Option+Tab 的应用切换规则。放置位置和启用方式见 [官方文件位置说明](https://karabiner-elements.pqrs.org/docs/json/location/)。

后续修改固定下载版本时，须重新下载官方文件、核对版本并更新 SHA-256，不要关闭校验。Homebrew 安装的软件及 Vim 插件未完全锁定版本，因此该仓库复现的是配置和软件选择。
