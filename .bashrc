# ~/.bashrc: executed by bash(1) for non-login shells.

# Note: PS1 and umask are already set in /etc/profile. You should not
# need this unless you want different defaults for root.
# PS1='${debian_chroot:+($debian_chroot)}\h:\w\$ '
# umask 022
PS1='╭${debian_chroot:+()}\[\e[1;31m\]\u\[\e[1;33m\]@\[\e[1;36m\]\h \[\e[1;33m\]\w \[\e[1;35m\]\n╰\$ \[\e[0m\]'

# Some more alias to avoid making mistakes:
# alias rm='rm -i'
# alias cp='cp -i'
# alias mv='mv -i'

export CLICOLOR=1
export LSCOLORS=GxFxCxDxBxegedabagaced
alias ls='ls -F'
alias ll='ls -l'
alias l='ls -lA'
alias pip=pip3
alias lsblk='diskutil list'
alias unmount='diskutil unmount'

function wrap_netstat() {
    if [[ "$@" == "-tunlp" ]]; then
        sudo lsof -i -P | grep LISTEN | grep :$PORT
    else
        netstat $@
    fi
}
alias netstat='wrap_netstat'

alias reinstall-clash='brew reinstall --no-quarantine clash-for-windows'

# Use Touch ID to sudo:
if ! [[ `cat /etc/pam.d/sudo` == *"pam_tid.so"* ]]; then
    echo "Add pam_tid.so to /etc/pam.d/sudo..."
    sudo sed -i "" "1a\\
auth       sufficient     pam_tid.so\\
" /etc/pam.d/sudo
fi

# cd to current Finder folder:
cdf () {
  finderPath=`osascript -e 'tell application "Finder"
                               try
                                   set currentFolder to (folder of the front window as alias)
                               on error
                                   set currentFolder to (path to desktop folder as alias)
                               end try
                               POSIX path of currentFolder
                            end tell'`;
  cd "$finderPath"
}

export BASH_SILENCE_DEPRECATION_WARNING=1
# export ALL_PROXY=http://127.0.0.1:1080
# export ALL_PROXY=http://172.16.0.3:1080

# Android Studio
export USER_HOME=/Users/YOUR_USER
export ANDROID_HOME=${USER_HOME}/Library/Android/sdk
export ANDROID_SDK_ROOT=${USER_HOME}/Library/Android/sdk
export ANDROID_AVD_HOME=${USER_HOME}/.android/avd
