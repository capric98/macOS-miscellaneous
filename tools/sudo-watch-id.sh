#!/bin/bash
# Opt-in installer for Apple Watch authentication in sudo.
set -euo pipefail

watch_script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$watch_script_dir/sudo-touch-id.sh"

WATCH_REV=ce04b062ccb70ac781a68c832f9d84bb42816718
WATCH_SHA256=25517b885e476bee7168b5f29491c46070f65ec2f189ffed62bef9b1f9a1c77f
WATCH_SOURCE="https://raw.githubusercontent.com/mostpinkest/pam-watchid/$WATCH_REV/Sources/pam-watchid/pam_watchid.swift"
WATCH_LIBRARY=/usr/local/lib/pam/macos-setup/pam_watchid.so.2
WATCH_PATTERN='pam_watchid\.so(\.[0-9]+)?'

watch_die() { printf '错误：%s\n' "$*" >&2; exit 1; }

watch_policy_needs_install() {
    local status
    status=$(sudo_pam_status /etc/pam.d "$WATCH_PATTERN") || status=unsafe
    case $status in
        missing) return 0 ;;
        configured) printf 'sudo 的 PAM 配置已包含 pam-watchid 规则。\n'; return 1 ;;
        *) watch_die 'sudo 的系统认证栈不是预期配置，请先检查 /etc/pam.d/sudo 和 sudo_local。' ;;
    esac
}

apply_watch_id() {
    local artifact=$1 library_dir=${WATCH_LIBRARY%/*} directory owner mode
    watch_policy_needs_install || return 0

    for directory in /usr/local /usr/local/lib /usr/local/lib/pam "$library_dir"; do
        if [[ ! -e $directory && ! -L $directory ]]; then
            /bin/mkdir -m 755 "$directory"
        fi
        [[ -d $directory && ! -L $directory ]] || watch_die "模块目录异常：$directory"
        read -r owner mode < <(/usr/bin/stat -f '%u %OLp' "$directory")
        if [[ $owner != 0 ]] || (( 8#$mode & 022 )); then
            watch_die "模块目录必须由 root 拥有并限制写权限：$directory"
        fi
    done

    [[ ! -L $WATCH_LIBRARY && ( ! -e $WATCH_LIBRARY || -f $WATCH_LIBRARY ) ]] || \
        watch_die "模块目标异常：$WATCH_LIBRARY"
    watch_temp_file=$(/usr/bin/mktemp "$library_dir/.pam_watchid.XXXXXX")
    trap '/bin/rm -f "$watch_temp_file"' EXIT
    /usr/bin/install -o root -g wheel -m 444 "$artifact" "$watch_temp_file"
    /usr/bin/codesign --verify "$watch_temp_file"
    /bin/mv -fh "$watch_temp_file" "$WATCH_LIBRARY"
    install_sudo_pam_rule /etc/pam.d "$WATCH_LIBRARY" "$WATCH_PATTERN"
}

if [[ $# == 1 && $1 == --dry-run ]]; then
    printf '构建 pam-watchid %s，并将模块安装到 %s。\n' "$WATCH_REV" "$WATCH_LIBRARY"
    printf '通过 /etc/pam.d/sudo_local 添加 sufficient 认证，保留系统密码回退。\n'
    exit 0
fi
if (( EUID == 0 )); then
    [[ $# == 2 && $1 == --apply ]] || watch_die '请以普通用户运行此脚本。'
    apply_watch_id "$2"
    exit 0
fi
[[ $# == 0 ]] || watch_die '用法：bash tools/sudo-watch-id.sh [--dry-run]'

[[ $(/usr/bin/uname -s) == Darwin && $(/usr/bin/uname -m) == arm64 ]] || \
    watch_die '请在 Apple Silicon Mac 的原生终端中运行。'
watch_policy_needs_install || exit 0
/usr/bin/xcode-select -p >/dev/null || watch_die '需要 Xcode 或 Command Line Tools 来编译 pam-watchid。'

watch_work_dir=$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/macos-setup-watchid.XXXXXX")
trap '/bin/rm -rf -- "$watch_work_dir"' EXIT
trap 'exit 1' HUP INT TERM
/usr/bin/curl --proto '=https' --tlsv1.2 -fsSL --retry 3 --connect-timeout 15 --max-time 60 \
    "$WATCH_SOURCE" -o "$watch_work_dir/pam_watchid.swift"
printf '%s  %s\n' "$WATCH_SHA256" "$watch_work_dir/pam_watchid.swift" | /usr/bin/shasum -a 256 -c -
/usr/bin/xcrun swiftc -target arm64-apple-macos14.0 -O -emit-library \
    -Xlinker -install_name -Xlinker "$WATCH_LIBRARY" \
    -module-cache-path "$watch_work_dir/swift-cache" "$watch_work_dir/pam_watchid.swift" \
    -o "$watch_work_dir/pam_watchid.so.2"
printf '安装 pam-watchid 需要现有的 sudo 授权。\n'
/usr/bin/sudo -- /bin/bash "$watch_script_dir/sudo-watch-id.sh" --apply "$watch_work_dir/pam_watchid.so.2"
