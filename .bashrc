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
alias ll='ls -l'
alias l='ls -lA'
alias pip=pip3
alias lsblk='diskutil list'
alias unmount='diskutil unmount'

# Use Touch ID to sudo:
if ! [[ `cat /etc/pam.d/authorization` == *"pam_tid.so"* ]]; then
    echo "Add pam_tid.so to /etc/pam.d/authorization..."
    sudo sed -i "" "1a\\
auth       optional       pam_tid.so\\
" /etc/pam.d/authorization
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

# export ALL_PROXY=http://127.0.0.1:1080
