# Shared by Bash and zsh. The formula inventory is generated during setup,
# never queried on shell startup. Keep all temporary variables inside a function.
_macos_setup_homebrew_path() {
    local candidate managed= combined remaining
    if [[ ! ${HOMEBREW_PREFIX-} && -x /opt/homebrew/bin/brew ]]; then
        if [[ -n ${ZSH_VERSION-} ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv zsh)"
        else
            eval "$(/opt/homebrew/bin/brew shellenv bash)"
        fi
    fi

    if [[ -r $HOME/.config/macos-setup/homebrew-paths ]]; then
        while IFS= read -r candidate || [[ -n $candidate ]]; do
            [[ -n $candidate && -d $candidate ]] || continue
            case ":$managed:" in
                *":$candidate:"*) ;;
                *) managed="${managed:+$managed:}$candidate" ;;
            esac
        done < "$HOME/.config/macos-setup/homebrew-paths"
    fi
    # Restore Homebrew itself even if the inherited PATH was reset.
    if [[ -n ${HOMEBREW_PREFIX-} ]]; then
        for candidate in "$HOMEBREW_PREFIX/bin" "$HOMEBREW_PREFIX/sbin"; do
            [[ -d $candidate ]] || continue
            case ":$managed:" in
                *":$candidate:"*) ;;
                *) managed="${managed:+$managed:}$candidate" ;;
            esac
        done
    fi
    [[ -n $managed ]] || return 0

    # Keep Brewfile order and remove inherited copies of managed entries, so
    # keg-only tools keep priority even after macOS path_helper or nested shells.
    combined=$managed
    if [[ ${PATH+x} ]]; then
        remaining=$PATH
        while :; do
            candidate=${remaining%%:*}
            case ":$managed:" in
                *":$candidate:"*) ;;
                *) combined="$combined:$candidate" ;;
            esac
            case $remaining in
                *:*) remaining=${remaining#*:} ;;
                *) break ;;
            esac
        done
    fi
    export PATH=$combined
}
_macos_setup_homebrew_path
unset -f _macos_setup_homebrew_path
