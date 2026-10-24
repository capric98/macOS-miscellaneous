#!/bin/bash
# Compatible with the Bash 3.2 shipped with macOS.
set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
BREWFILE="$ROOT_DIR/Brewfile"
DRY_RUN=0
ASSUME_YES=0
CHANGE_SHELL=1
INSTALL_PACKAGES=1
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
            -h|--help) usage; exit 0 ;;
            *) usage >&2; die "未知参数：$1" ;;
        esac
        shift
    done
}

show_plan() {
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
    confirm_packages
    WORK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/macos-setup.XXXXXX")
    trap cleanup EXIT
    trap 'on_error "$?" "$LINENO"' ERR
    set -E
    setup_homebrew
    install_blesh
    install_configs
    install_vim_plugins
    setup_login_shell
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
