#!/bin/bash
# Compatible with the Bash 3.2 shipped with macOS.
set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
BREWFILE="$ROOT_DIR/Brewfile"
OPTIONAL_BREWFILE="$ROOT_DIR/Brewfile.optional"
DRY_RUN=0
ASSUME_YES=0
CHANGE_SHELL=1
INSTALL_PACKAGES=1
OPTIONAL_ONLY=0
SKIP_OPTIONAL=0
FLAMESHOT_CASK=flameshot-org/flameshot/flameshot-org-flameshot
MPV_CASK=capric98/mpv-app/mpv-app
BACKUP_DIR=
WORK_DIR=
BREW_BIN=
BREW_PREFIX=
BASH_BIN=

BLE_VERSION='0.4.0-nightly+d81fd54'
BLE_URL='https://github.com/akinomyoga/ble.sh/releases/download/nightly/ble-nightly-20260908+d81fd54.tar.xz'
BLE_SHA256='7a2445f138e7f099dd5dee749391a8b045646d1b8a605975885be5b34b6b5f7e'
PLUG_URL='https://raw.githubusercontent.com/junegunn/vim-plug/7e5aae5e1187842cb0b1d8def986e48d481c4410/plug.vim'
PLUG_SHA256='4243c1d2a5d9a1012aca536315e69aab8549e60926b3dd80ee1f973954d77f9d'

log() { printf '\n%s\n' "$*"; }
die() { printf '错误：%s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'USAGE'
用法：bash setup.sh [选项]
  --dry-run             只显示安装清单和操作，不联网、不写文件
  --review-packages     只显示 Brewfile
  --yes                 表示已审核 Brewfile，跳过清单确认
  --skip-packages       跳过 Homebrew 软件安装，仍检查配置需要的工具
  --no-change-shell     不修改默认登录 shell，也不写 /etc/shells
  --optional-only       仅询问是否安装 mpv + Flameshot 并导入配置
  --skip-optional       跳过可选软件组的询问和配置
  -h, --help            显示帮助
USAGE
}

parse_args() {
    while (( $# )); do
        case $1 in
            --dry-run) DRY_RUN=1 ;;
            --review-packages) cat "$BREWFILE"; exit 0 ;;
            --yes) ASSUME_YES=1 ;;
            --skip-packages) INSTALL_PACKAGES=0 ;;
            --no-change-shell) CHANGE_SHELL=0 ;;
            --optional-only) OPTIONAL_ONLY=1 ;;
            --skip-optional) SKIP_OPTIONAL=1 ;;
            -h|--help) usage; exit 0 ;;
            *) usage >&2; die "未知参数：$1" ;;
        esac
        shift
    done
    (( ! OPTIONAL_ONLY || ! SKIP_OPTIONAL )) || die '--optional-only 不能与 --skip-optional 同用。'
}

show_plan() {
    if (( OPTIONAL_ONLY )); then
        show_optional_plan
        return 0
    fi
    log '待审核的 Homebrew 安装清单：'
    cat "$BREWFILE"
    log '配置操作：'
    if (( INSTALL_PACKAGES )); then
        printf '%s\n' '  安装 Homebrew（若缺少），brew bundle install --no-upgrade'
    else
        printf '%s\n' '  跳过软件安装，使用现有 Homebrew 和依赖'
    fi
    printf '%s\n' \
        '  备份不同的现有文件到 ~/.local/state/macos-setup/backups/' \
        '  复制 .bash_profile、.bashrc、.blerc、.vimrc 和 Solarized dircolors' \
        "  安装固定版本 ble.sh ($BLE_VERSION)，校验 SHA-256" \
        '  添加 iTerm2 动态配置 Solarized Light (Bash)' \
        '  放入两个 Karabiner 规则文件，供界面中选择启用'
    printf '%s\n' '  安装 vim-plug，运行 vim +"PlugInstall --sync" +qall'
    if (( CHANGE_SHELL )); then
        printf '%s\n' '  注册 Homebrew Bash 并将其设为当前用户的登录 shell'
    fi
    printf '%s\n' '  Git 身份、SSH 密钥和 .local 覆盖文件由使用者在本机配置'
    (( SKIP_OPTIONAL )) || show_optional_plan
    return 0
}

show_optional_plan() {
    log '可选软件组：mpv + Flameshot（单独询问，默认跳过；--yes 不代替确认）：'
    cat "$OPTIONAL_BREWFILE"
    if (( INSTALL_PACKAGES )); then
        printf '%s\n' '  确认后添加上述 tap、信任其中两个 cask，再按可选清单安装；不主动升级'
    else
        printf '%s\n' '  --skip-packages：仅为已安装的应用导入配置，不安装软件或添加 tap'
    fi
    printf '%s\n' \
        '  先退出 mpv 和 Flameshot；不同的现有配置会先备份' \
        '  mpv：导入播放配置、快捷键、ModernZ 主题和图标字体；中文字体由 Homebrew 安装' \
        '  Flameshot：保留 Ctrl+Cmd+A、showHelp=false、startupLaunch=true 和工具栏设置' \
        '  截图目录使用当前用户的 ~/Pictures/ScreenShots/'
}

confirm_packages() {
    (( ASSUME_YES )) && return 0
    [[ -t 0 ]] || die '请先审核 Brewfile，然后使用 --yes；交互运行可直接确认。'
    local answer
    read -r -p '已审核上述清单，继续配置？[y/N] ' answer
    case $answer in
        y|Y|yes|YES) ;;
        *) die '已取消，未修改配置。' ;;
    esac
}

preflight() {
    [[ $(uname -s) == Darwin ]] || die '本脚本只支持 macOS。'
    (( EUID != 0 )) || die '请用普通用户运行；需要权限时脚本会调用 sudo。'
    [[ ${HOME-} == /* && $HOME != / && -d $HOME ]] || die 'HOME 必须是已有的用户目录。'
    if [[ $(sysctl -in sysctl.proc_translated 2>/dev/null || true) == 1 ]]; then
        die '请在原生 Apple Silicon 终端中运行，避免安装 Intel Homebrew。'
    fi
    [[ $(uname -m) == arm64 ]] || die '本脚本只支持 Apple Silicon，请使用原生终端。'
    [[ ! ${XDG_CONFIG_HOME-} || $XDG_CONFIG_HOME == "$HOME/.config" ]] || \
        die '此配置集使用 ~/.config；请先取消自定义 XDG_CONFIG_HOME 后运行。'
}

cleanup() {
    if [[ -n $WORK_DIR && -d $WORK_DIR ]]; then
        rm -rf -- "$WORK_DIR"
    fi
}

on_error() {
    local status=$1 line=$2
    printf '\n配置在第 %s 行失败（退出码 %s）。修复后可重新运行。\n' "$line" "$status" >&2
    [[ ! $BACKUP_DIR ]] || printf '原配置备份：%s\n' "$BACKUP_DIR" >&2
    exit "$status"
}

backup_existing() {
    local target=$1 relative
    [[ -e $target || -L $target ]] || return 0
    case $target in
        "$HOME"/*) relative=${target#"$HOME"/} ;;
        *) die '备份目标必须位于 HOME 内。' ;;
    esac
    if [[ ! $BACKUP_DIR ]]; then
        BACKUP_DIR="$HOME/.local/state/macos-setup/backups/$(date +%Y%m%d-%H%M%S)-$$"
        mkdir -p "$BACKUP_DIR"
        chmod 700 "$BACKUP_DIR"
    fi
    # Preserve the first version if the same target is touched again this run.
    if [[ ! -e $BACKUP_DIR/$relative && ! -L $BACKUP_DIR/$relative ]]; then
        mkdir -p "$(dirname -- "$BACKUP_DIR/$relative")"
        cp -pPR "$target" "$BACKUP_DIR/$relative"
        printf '已备份：%s\n' "~/$relative"
    fi
}

install_file() {
    local source=$1 target=$2 temporary
    [[ -f $source ]] || die "缺少源文件：$source"
    [[ ! -d $target ]] || die "配置目标是目录：$target"
    if [[ -f $target ]] && cmp -s "$source" "$target"; then
        return 0
    fi
    backup_existing "$target"
    mkdir -p "$(dirname -- "$target")"
    temporary=$(mktemp "${target}.macos-setup.XXXXXX")
    cp "$source" "$temporary"
    chmod 644 "$temporary"
    mv -f "$temporary" "$target"
    printf '已配置：%s\n' "${target/#$HOME/~}"
}

download() {
    curl --proto '=https' --tlsv1.2 -fL --retry 3 --connect-timeout 15 --max-time 300 "$1" -o "$2"
}

check_sha256() {
    printf '%s  %s\n' "$2" "$1" | shasum -a 256 -c -
}

find_brew() {
    BREW_BIN=/opt/homebrew/bin/brew
    [[ -x $BREW_BIN ]]
}

setup_homebrew() {
    if ! find_brew; then
        (( INSTALL_PACKAGES )) || die '未找到 Homebrew，不能使用 --skip-packages。'
        log '安装 Homebrew（可能要求管理员密码和 Command Line Tools）'
        download 'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh' "$WORK_DIR/homebrew-install.sh"
        /bin/bash "$WORK_DIR/homebrew-install.sh"
        find_brew || die 'Homebrew 安装后仍未找到 brew。'
    fi
    local brew_environment
    brew_environment=$("$BREW_BIN" shellenv bash)
    eval "$brew_environment"
    BREW_PREFIX=$("$BREW_BIN" --prefix)
    export HOMEBREW_NO_ENV_HINTS=1
    if (( INSTALL_PACKAGES )); then
        log '按 Brewfile 安装软件'
        HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_BUNDLE_NO_UPGRADE=1 \
            "$BREW_BIN" bundle install --no-upgrade --file "$BREWFILE"
    fi
    BASH_BIN="$BREW_PREFIX/bin/bash"
    [[ -x $BASH_BIN ]] || die '缺少 Homebrew Bash；请在 Brewfile 中保留 bash。'
    "$BASH_BIN" -c '(( BASH_VERSINFO[0] >= 4 ))' || die 'ble.sh 自动补全需要 Bash 4 以上版本。'
    local executable
    for executable in gls gdircolors gawk zoxide; do
        command -v "$executable" >/dev/null 2>&1 || die "缺少 $executable，请保留核心依赖。"
    done
    [[ -r $BREW_PREFIX/etc/profile.d/bash_completion.sh ]] || die '缺少 bash-completion@2。'
}

install_blesh() {
    local installed_version=
    if [[ -f $HOME/.local/share/blesh/ble.sh ]]; then
        installed_version=$("$BASH_BIN" "$HOME/.local/share/blesh/ble.sh" --version)
    fi
    [[ $installed_version != "ble.sh (Bash Line Editor), version $BLE_VERSION" ]] || return 0
    log '安装 ble.sh'
    download "$BLE_URL" "$WORK_DIR/blesh.tar.xz"
    check_sha256 "$WORK_DIR/blesh.tar.xz" "$BLE_SHA256"
    mkdir -p "$WORK_DIR/ble-build"
    tar -xJf "$WORK_DIR/blesh.tar.xz" --strip-components=1 -C "$WORK_DIR/ble-build"
    backup_existing "$HOME/.local/share/blesh"
    "$BASH_BIN" "$WORK_DIR/ble-build/ble.sh" --install "$HOME/.local/share"
}

install_configs() {
    log '复制配置文件'
    install_file "$ROOT_DIR/config/bash/bash_profile" "$HOME/.bash_profile"
    install_file "$ROOT_DIR/config/bash/bashrc" "$HOME/.bashrc"
    install_file "$ROOT_DIR/config/bash/blerc" "$HOME/.blerc"
    install_file "$ROOT_DIR/config/vim/vimrc" "$HOME/.vimrc"
    install_file "$ROOT_DIR/config/dircolors-solarized/dircolors.ansi-light" "$HOME/.config/dircolors-solarized/dircolors.ansi-light"
    install_file "$ROOT_DIR/config/dircolors-solarized/LICENSE" "$HOME/.config/dircolors-solarized/LICENSE"
    local rule
    for rule in "$ROOT_DIR"/config/karabiner/complex_modifications/*.json; do
        install_file "$rule" "$HOME/.config/karabiner/assets/complex_modifications/$(basename -- "$rule")"
    done
    sed "s|__BASH_PATH__|$BASH_BIN|g" "$ROOT_DIR/config/iterm2/solarized-light.plist" > "$WORK_DIR/iterm2-profile.plist"
    plutil -lint "$WORK_DIR/iterm2-profile.plist" >/dev/null
    install_file "$WORK_DIR/iterm2-profile.plist" "$HOME/Library/Application Support/iTerm2/DynamicProfiles/macos-setup.plist"
}

confirm_optional() {
    [[ -t 0 ]] || { log '非交互运行：跳过可选软件组；需要时运行 bash setup.sh --optional-only。'; return 1; }
    local answer
    read -r -p '安装可选软件组 mpv + Flameshot 并导入两者配置？[y/N] ' answer || return 1
    case $answer in
        y|Y|yes|YES) return 0 ;;
        *) log '已跳过可选软件组。'; return 1 ;;
    esac
}

flameshot_installed() {
    [[ -x /Applications/Flameshot.app/Contents/MacOS/flameshot ||
       -x $HOME/Applications/Flameshot.app/Contents/MacOS/flameshot ]] ||
        command -v flameshot >/dev/null 2>&1
}

mpv_installed() {
    [[ -x /Applications/mpv.app/Contents/MacOS/mpv ||
       -x $HOME/Applications/mpv.app/Contents/MacOS/mpv ]] ||
        command -v mpv >/dev/null 2>&1
}

setup_optional() {
    (( ! SKIP_OPTIONAL )) || return 0
    confirm_optional || return 0
    local app
    for app in flameshot mpv; do
        if pgrep -ix -u "$(id -u)" "$app" >/dev/null; then
            die "请先退出 ${app}，再运行 bash setup.sh --optional-only，以免应用覆盖配置。"
        fi
    done
    if (( INSTALL_PACKAGES )); then
        find_brew || die '未找到 Homebrew；请先安装 Homebrew，再运行 bash setup.sh --optional-only。'
        log '安装可选软件组 mpv + Flameshot'
        "$BREW_BIN" tap flameshot-org/flameshot
        "$BREW_BIN" tap capric98/mpv-app
        # Homebrew 7+ requires explicit trust for third-party casks.
        if "$BREW_BIN" help trust >/dev/null 2>&1; then
            "$BREW_BIN" trust --cask "$FLAMESHOT_CASK" "$MPV_CASK"
        fi
        HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_BUNDLE_NO_UPGRADE=1 \
            "$BREW_BIN" bundle install --no-upgrade --file "$OPTIONAL_BREWFILE"
        # Bundle must finish before either application's configuration is changed.
        install_mpv_config
        install_flameshot_config
    else
        if mpv_installed; then
            install_mpv_config
        else
            log '未安装 mpv；--skip-packages 下跳过其配置。'
        fi
        if flameshot_installed; then
            install_flameshot_config
        else
            log '未安装 Flameshot；--skip-packages 下跳过其配置。'
        fi
    fi
}

install_mpv_config() {
    local source relative
    while IFS= read -r -d '' source; do
        relative=${source#"$ROOT_DIR/config/mpv/"}
        install_file "$source" "$HOME/.config/mpv/$relative"
    done < <(find "$ROOT_DIR/config/mpv" -type f -print0)
    log 'mpv 配置和 ModernZ 主题已导入，重新打开 mpv 后生效。'
}

install_flameshot_config() {
    local screenshots="$HOME/Pictures/ScreenShots" ini_path line
    # Quote the QSettings string so spaces, commas and semicolons stay literal.
    ini_path=${screenshots//\\/\\\\}
    ini_path=${ini_path//\"/\\\"}
    while IFS= read -r line || [[ -n $line ]]; do
        if [[ $line == 'savePath=__SCREENSHOT_DIR__' ]]; then
            printf 'savePath="%s/"\n' "$ini_path"
        else
            printf '%s\n' "$line"
        fi
    done < "$ROOT_DIR/config/flameshot/flameshot.ini" > "$WORK_DIR/flameshot.ini"
    mkdir -p "$screenshots"
    install_file "$WORK_DIR/flameshot.ini" "$HOME/.config/flameshot/flameshot.ini"
    log 'Flameshot 配置已导入。请手动打开应用，并按 macOS 提示授予屏幕录制权限。'
}

install_vim_plugins() {
    log '安装 Vim 插件'
    local plug="$HOME/.vim/autoload/plug.vim"
    if [[ ! -f $plug ]] || ! check_sha256 "$plug" "$PLUG_SHA256" >/dev/null 2>&1; then
        download "$PLUG_URL" "$WORK_DIR/plug.vim"
        check_sha256 "$WORK_DIR/plug.vim" "$PLUG_SHA256"
        install_file "$WORK_DIR/plug.vim" "$plug"
    fi
    local vim_log="$WORK_DIR/vim-plug.log" vim_output="$WORK_DIR/vim-plug.output"
    local failure_reason= failure_log
    : > "$vim_log"
    # Ex batch mode otherwise enables vi compatibility, which breaks existing
    # plugins using Vim syntax (including vim-autoformat line continuations).
    if vim -N -n -es -i NONE -V1"$vim_log" -u "$HOME/.vimrc" '+PlugInstall --sync' '+qall' > "$vim_output" 2>&1; then
        # vim-plug can finish with status 0 after a failed clone.
        if [[ ! -f $HOME/.vim/plugged/vim-colors-solarized/colors/solarized.vim ]]; then
            failure_reason='Solarized Vim 插件未完整安装'
        elif [[ ! -f $HOME/.vim/plugged/vim-autoformat/plugin/autoformat.vim ]]; then
            failure_reason='vim-autoformat 插件未完整安装'
        fi
    else
        failure_reason="Vim 退出码为 $?"
    fi
    if [[ -n $failure_reason ]]; then
        failure_log="$HOME/.local/state/macos-setup/logs/vim-$(date +%Y%m%d-%H%M%S)-$$.log"
        mkdir -p "$(dirname -- "$failure_log")"
        chmod 700 "$(dirname -- "$failure_log")"
        (umask 077; cat "$vim_log" "$vim_output" > "$failure_log")
        die "Vim 插件安装失败：${failure_reason}。详细日志：$failure_log"
    fi
}

setup_login_shell() {
    (( CHANGE_SHELL )) || return 0
    if ! grep -Fxq "$BASH_BIN" /etc/shells; then
        log '将 Homebrew Bash 注册到 /etc/shells'
        printf '%s\n' "$BASH_BIN" | sudo tee -a /etc/shells >/dev/null
    fi
    local current_shell
    current_shell=$(dscl . -read "/Users/$(id -un)" UserShell | awk '{print $2}')
    if [[ $current_shell != "$BASH_BIN" ]]; then
        log '将当前用户的登录 shell 设置为 Homebrew Bash'
        chsh -s "$BASH_BIN"
    fi
}

main() {
    parse_args "$@"
    show_plan
    (( ! DRY_RUN )) || return 0
    preflight
    (( OPTIONAL_ONLY )) || confirm_packages
    WORK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/macos-setup.XXXXXX")
    trap cleanup EXIT
    trap 'on_error "$?" "$LINENO"' ERR
    set -E
    if (( OPTIONAL_ONLY )); then
        setup_optional
        [[ ! $BACKUP_DIR ]] || printf '原配置备份：%s\n' "$BACKUP_DIR"
        return 0
    fi
    setup_homebrew
    install_blesh
    install_configs
    install_vim_plugins
    setup_login_shell
    setup_optional
    log '配置完成。重新打开终端后使用 Bash 配置。'
    printf '%s\n' \
        'iTerm2：在 Profiles 中选择 Solarized Light (Bash)，可设为默认配置。' \
        'Karabiner：完成系统权限授权，在 Complex Modifications > Add predefined rule 中启用规则。' \
        'Caps Lock 输入法切换等规则依赖本机设置，详见 README。'
    [[ ! $BACKUP_DIR ]] || printf '原配置备份：%s\n' "$BACKUP_DIR"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    main "$@"
fi
