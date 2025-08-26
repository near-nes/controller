#!/bin/sh

alias ls='ls -h --color=auto'
alias l='ls -alFh --color=auto --group-directories-first --time-style=+"%Y-%m-%d %H:%M:%S"'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias envg='env | grep -i' # Usage: envg UID
alias psg='ps aux | grep -v grep | grep -i' # Usage: psg python