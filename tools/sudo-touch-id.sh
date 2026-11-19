#!/bin/bash
# Sourced for read-only checks, then run as root to write the system config.

pam_auth_rules() {
    LC_ALL=C /usr/bin/awk '
        {
            sub(/#.*/, "")
            line = line $0
            continued = sub(/\\$/, "", line)
            if (continued) next
            $0 = line
            line = ""
        }
        $1 == "auth" { $1 = $1; print }
        END { if (continued) exit 1 }
    ' "$1"
}

sudo_pam_status() {
    local pam_dir=$1 module_pattern=$2 sudo_rules local_rules target="$1/sudo_local"
    local rule_pattern="^auth (required|requisite|sufficient|binding|optional) ([^ ]*/)?${module_pattern}( |$)"
    local stock_rules=$'auth include sudo_local\nauth sufficient pam_smartcard.so\nauth required pam_opendirectory.so'

    [[ -f $pam_dir/sudo && -r $pam_dir/sudo ]] || { printf 'unsafe\n'; return 0; }
    sudo_rules=$(pam_auth_rules "$pam_dir/sudo") || return 1
    if /usr/bin/grep -Eq "$rule_pattern" <<< "$sudo_rules"; then
        printf 'configured\n'
    elif ! /usr/bin/grep -Fxq 'auth include sudo_local' <<< "$sudo_rules"; then
        printf 'unsupported\n'
    elif [[ -L $target || ( -e $target && ( ! -f $target || ! -r $target ) ) ]]; then
        printf 'unsafe\n'
    else
        local_rules=
        if [[ -f $target ]]; then
            local_rules=$(pam_auth_rules "$target") || return 1
        fi
        if /usr/bin/grep -Eq "$rule_pattern" <<< "$local_rules"; then
            printf 'configured\n'
        elif [[ $sudo_rules != "$stock_rules" ]]; then
            # Adding a sufficient module could bypass custom rules after the include.
            printf 'custom\n'
        else
            printf 'missing\n'
        fi
    fi
}

sudo_touch_id_status() {
    sudo_pam_status "$1" 'pam_tid\.so(\.[0-9]+)?'
}

touch_id_available() {
    local available
    available=$(/usr/bin/osascript -l JavaScript 2>/dev/null <<'JXA'
ObjC.import('LocalAuthentication');
$.LAContext.alloc.init.canEvaluatePolicyError($.LAPolicyDeviceOwnerAuthenticationWithBiometrics, null);
JXA
    ) && [[ $available == true ]]
}

install_sudo_pam_rule() (
    set -eu
    umask 077
    local pam_dir=$1 target="$1/sudo_local" module=$2 module_pattern=$3
    local rule="auth       sufficient     $module" status backup= mode uid

    # Keep this in subshell scope for the EXIT trap on Bash 3.2.
    lock="$pam_dir/.sudo_local.macos-setup.lock"
    if ! /bin/mkdir "$lock"; then
        printf '无法锁定 sudo_local，可能已有配置正在进行。\n' >&2
        exit 1
    fi
    trap '/bin/rm -f "$lock/new" "$lock/original"; /bin/rmdir "$lock"' EXIT
    trap 'exit 1' HUP INT TERM

    status=$(sudo_pam_status "$pam_dir" "$module_pattern")
    case $status in
        configured) printf '已存在 sudo 认证规则（%s）。\n' "$module"; exit 0 ;;
        missing) ;;
        *) printf 'sudo 的 PAM 配置已变动，请检查后重试。\n' >&2; exit 1 ;;
    esac
    if [[ -f $target ]]; then
        uid=$(/usr/bin/stat -f %u "$target")
        mode=$(/usr/bin/stat -f %OLp "$target")
        if [[ $uid != "$EUID" ]] || (( 8#$mode & 022 )); then
            printf 'sudo_local 的所有者或写权限异常。\n' >&2
            exit 1
        fi
        /bin/cp -p "$target" "$lock/original"
        /bin/cp -p "$lock/original" "$lock/new"
        # Append after existing auth rules so earlier requirements still apply.
        printf '\n%s\n' "$rule" >> "$lock/new"
    else
        printf '# Local sudo PAM configuration\n%s\n' "$rule" > "$lock/new"
        /bin/chmod 644 "$lock/new"
    fi

    if [[ -f $lock/original ]]; then
        [[ ! -L $target ]] && /usr/bin/cmp -s "$lock/original" "$target" || exit 1
        backup=$(/usr/bin/mktemp -d "$pam_dir/.sudo_local.backup.XXXXXX")
        /bin/mv "$lock/original" "$backup/sudo_local"
    else
        [[ ! -e $target && ! -L $target ]] || exit 1
    fi
    /bin/mv -fh "$lock/new" "$target"
    [[ -z $backup ]] || printf '原 sudo_local 备份：%s/sudo_local\n' "$backup"
    if [[ $(sudo_pam_status "$pam_dir" "$module_pattern") != configured ]]; then
        printf '无法在 sudo 的 PAM 配置中确认规则，请检查 sudo_local。\n' >&2
        exit 1
    fi
    printf '已为 sudo 配置 %s。\n' "$module"
)

install_sudo_touch_id() {
    install_sudo_pam_rule "$1" pam_tid.so 'pam_tid\.so(\.[0-9]+)?'
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    (( EUID == 0 )) || exit 1
    install_sudo_touch_id /etc/pam.d
fi
