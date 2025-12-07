#!/usr/bin/env zsh
# Smart Shell Assistant - Zsh Plugin
# Provides intelligent command suggestions based on context

# Configuration
SMART_ASSISTANT_API="${SMART_ASSISTANT_API:-http://127.0.0.1:8765}"
SMART_ASSISTANT_ENABLED="${SMART_ASSISTANT_ENABLED:-true}"
SMART_ASSISTANT_MAX_SUGGESTIONS="${SMART_ASSISTANT_MAX_SUGGESTIONS:-5}"
SMART_ASSISTANT_AUTO_SUGGEST="${SMART_ASSISTANT_AUTO_SUGGEST:-false}"

# Color codes
_SSA_GREEN="\033[0;32m"
_SSA_YELLOW="\033[0;33m"
_SSA_RED="\033[0;31m"
_SSA_BLUE="\033[0;34m"
_SSA_RESET="\033[0m"

# Track last command and exit code
typeset -g _SSA_LAST_COMMAND=""
typeset -g _SSA_LAST_EXIT_CODE=0

# Command history for context
typeset -ga _SSA_RECENT_COMMANDS=()
typeset -g _SSA_MAX_RECENT=10

# Capture last command before execution
_ssa_preexec() {
    _SSA_LAST_COMMAND="$1"
}

# Capture result after execution
_ssa_precmd() {
    _SSA_LAST_EXIT_CODE=$?

    # Add to recent commands (limit to last N)
    if [[ -n "$_SSA_LAST_COMMAND" ]]; then
        _SSA_RECENT_COMMANDS+=("$_SSA_LAST_COMMAND")
        if (( ${#_SSA_RECENT_COMMANDS[@]} > _SSA_MAX_RECENT )); then
            _SSA_RECENT_COMMANDS=("${_SSA_RECENT_COMMANDS[@]: -$_SSA_MAX_RECENT}")
        fi
    fi
}

# Register hooks
autoload -U add-zsh-hook
add-zsh-hook preexec _ssa_preexec
add-zsh-hook precmd _ssa_precmd

# Get command suggestions
smart-suggest() {
    local query="$1"

    if [[ -z "$query" ]]; then
        echo "${_SSA_YELLOW}Usage: smart-suggest <query>${_SSA_RESET}"
        return 1
    fi

    if [[ "$SMART_ASSISTANT_ENABLED" != "true" ]]; then
        echo "${_SSA_YELLOW}Smart Assistant is disabled${_SSA_RESET}"
        return 0
    fi

    # Build recent commands JSON array
    local recent_json="[]"
    if (( ${#_SSA_RECENT_COMMANDS[@]} > 0 )); then
        local commands_str=$(printf ',"%s"' "${_SSA_RECENT_COMMANDS[@]}")
        recent_json="[${commands_str:1}]"
    fi

    # Build JSON payload
    local payload=$(cat <<EOF
{
  "query": "$query",
  "cwd": "$PWD",
  "last_command": "$_SSA_LAST_COMMAND",
  "last_exit_code": $_SSA_LAST_EXIT_CODE,
  "recent_commands": $recent_json,
  "max_suggestions": $SMART_ASSISTANT_MAX_SUGGESTIONS
}
EOF
)

    # Call API
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$SMART_ASSISTANT_API/suggest" \
        2>/dev/null)

    if [[ $? -ne 0 ]] || [[ -z "$response" ]]; then
        echo "${_SSA_RED}✗ Failed to connect to Smart Assistant API${_SSA_RESET}"
        echo "${_SSA_YELLOW}  Make sure the backend is running: python backend/app.py${_SSA_RESET}"
        return 1
    fi

    # Parse response and display suggestions
    _ssa_display_suggestions "$response"
}

# Display suggestions from API response
_ssa_display_suggestions() {
    local response="$1"

    # Check if successful
    local success=$(echo "$response" | grep -o '"success":\s*true')
    if [[ -z "$success" ]]; then
        echo "${_SSA_RED}✗ No suggestions found${_SSA_RESET}"
        return 1
    fi

    echo "${_SSA_GREEN}Smart Suggestions:${_SSA_RESET}"
    echo ""

    # Extract suggestions (basic parsing, consider using jq for production)
    local suggestions=$(echo "$response" | \
        grep -o '"command":\s*"[^"]*"' | \
        sed 's/"command":\s*"\([^"]*\)"/\1/' | \
        head -n $SMART_ASSISTANT_MAX_SUGGESTIONS)

    local i=1
    while IFS= read -r cmd; do
        if [[ -n "$cmd" ]]; then
            echo "  ${_SSA_BLUE}[$i]${_SSA_RESET} $cmd"
            ((i++))
        fi
    done <<< "$suggestions"

    echo ""
    echo "${_SSA_YELLOW}Tip: Copy a suggestion or modify as needed${_SSA_RESET}"
}

# Get error fix suggestions
smart-fix() {
    if [[ $_SSA_LAST_EXIT_CODE -eq 0 ]]; then
        echo "${_SSA_GREEN}✓ Last command succeeded (exit code 0)${_SSA_RESET}"
        return 0
    fi

    echo "${_SSA_YELLOW}Analyzing last error...${_SSA_RESET}"

    # Get last command output (if available in history)
    local error_msg="Command failed with exit code $_SSA_LAST_EXIT_CODE"

    # Build JSON payload
    local payload=$(cat <<EOF
{
  "error_message": "$error_msg",
  "last_command": "$_SSA_LAST_COMMAND"
}
EOF
)

    # Call API
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$SMART_ASSISTANT_API/fix-error" \
        2>/dev/null)

    if [[ $? -ne 0 ]] || [[ -z "$response" ]]; then
        echo "${_SSA_RED}✗ Failed to connect to Smart Assistant API${_SSA_RESET}"
        return 1
    fi

    # Display fixes
    echo ""
    echo "${_SSA_GREEN}Suggested Fixes:${_SSA_RESET}"
    echo "$response" | grep -o '"fixes":\s*\[[^]]*\]' | head -n 3
    echo ""
}

# Toggle Smart Assistant
smart-toggle() {
    if [[ "$SMART_ASSISTANT_ENABLED" == "true" ]]; then
        export SMART_ASSISTANT_ENABLED="false"
        echo "${_SSA_YELLOW}Smart Assistant disabled${_SSA_RESET}"
    else
        export SMART_ASSISTANT_ENABLED="true"
        echo "${_SSA_GREEN}Smart Assistant enabled${_SSA_RESET}"
    fi
}

# Aliases
alias ss='smart-suggest'
alias sf='smart-fix'
alias st='smart-toggle'

# Show status on load
if [[ "$SMART_ASSISTANT_ENABLED" == "true" ]]; then
    echo "${_SSA_GREEN}✓ Smart Shell Assistant loaded${_SSA_RESET}"
fi
