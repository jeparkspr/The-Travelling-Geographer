#!/usr/bin/env bash

clear

git_comment="${1:-Claude cowork edits...}"

# Foreground (text) color variables
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'

# Background color variables
BG_RED='\033[41m'
BG_GREEN='\033[42m'
BG_YELLOW='\033[43m'
BG_BLUE='\033[44m'
BG_MAGENTA='\033[45m'
BG_CYAN='\033[46m'
BG_WHITE='\033[47m'
BG_BLACK='\033[40m'

NC='\033[0m' # No Color (reset)
INFOM=${WHITE}${BG_MAGENTA}
INFOB=${WHITE}${BG_BLUE}
INFOC=${WHITE}${BG_CYAN}
INFOG=${WHITE}${BG_GREEN}

echo -e "${INFOM}                                                                                ${NC}"
echo -e "${INFOM}    $(date +"%I:%M:%S") - PUSH REPOSITORY TO GITHUB                                        ${NC}"
echo -e "${INFOM}                                                                                ${NC}"
echo -e " "
cd "/mnt/c/Users/jepar/Documents/Claude/Projects/The Travelling Geographer/travelling-geographer-app"
git add -A
git commit -m "${git_comment}"
git push origin main
