#!/usr/bin/env bash
# Smart Shell Assistant - Bash Plugin
# Provides intelligent command suggestions based on context

# Configuration
export SMART_ASSISTANT_API="${SMART_ASSISTANT_API:-http://127.0.0.1:8765}"
export SMART_ASSISTANT_ENABLED="${SMART_ASSISTANT_ENABLED:-true}"
export SMART_ASSISTANT_MAX_SUGGESTIONS="${SMART_ASSISTANT_MAX_SUGGESTIONS:-5}"

# Color codes
_SSA_GREEN="\033[0;32m"
_SSA_YELLOW="\033[0;33m"
_SSA_RED="\033[0;31m"
_SSA_BLUE="\033[0;34m"
_SSA_RESET="\033[0m"

# Track last command and exit code
_SSA_LAST_COMMAND=""
_SSA_LAST_EXIT_CODE=0

# Command history for context
declare -a _SSA_RECENT_COMMANDS=()
_SSA_MAX_RECENT=10

# Capture command before execution (via DEBUG trap)
_ssa_preexec() {
    _SSA_LAST_COMMAND="$BASH_COMMAND"
}

# Capture result after execution (via PROMPT_COMMAND)
_ssa_precmd() {
    _SSA_LAST_EXIT_CODE=$?

    # Add to recent commands
    if [[ -n "$_SSA_LAST_COMMAND" ]]; then
        _SSA_RECENT_COMMANDS+=("$_SSA_LAST_COMMAND")

        # Limit size
        if (( ${#_SSA_RECENT_COMMANDS[@]} > _SSA_MAX_RECENT )); then
            _SSA_RECENT_COMMANDS=("${_SSA_RECENT_COMMANDS[@]: -$_SSA_MAX_RECENT}")
        fi
    fi
}

# Set up hooks
trap '_ssa_preexec' DEBUG
PROMPT_COMMAND="_ssa_precmd${PROMPT_COMMAND:+; $PROMPT_COMMAND}"

# Get command suggestions
smart-suggest() {
    local query="$1"

    if [[ -z "$query" ]]; then
        echo -e "${_SSA_YELLOW}Usage: smart-suggest <query>${_SSA_RESET}"
        return 1
    fi

    if [[ "$SMART_ASSISTANT_ENABLED" != "true" ]]; then
        echo -e "${_SSA_YELLOW}Smart Assistant is disabled${_SSA_RESET}"
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
        echo -e "${_SSA_RED}✗ Failed to connect to Smart Assistant API${_SSA_RESET}"
        echo -e "${_SSA_YELLOW}  Make sure the backend is running: python backend/app.py${_SSA_RESET}"
        return 1
    fi

    # Display suggestions
    _ssa_display_suggestions "$response"
}

# Display suggestions from API response
_ssa_display_suggestions() {
    local response="$1"

    # Check if successful
    if ! echo "$response" | grep -q '"success":\s*true'; then
        echo -e "${_SSA_RED}✗ No suggestions found${_SSA_RESET}"
        return 1
    fi

    echo -e "${_SSA_GREEN}Smart Suggestions:${_SSA_RESET}"
    echo ""

    # Extract suggestions
    local suggestions=$(echo "$response" | \
        grep -o '"command":\s*"[^"]*"' | \
        sed 's/"command":\s*"\([^"]*\)"/\1/' | \
        head -n "$SMART_ASSISTANT_MAX_SUGGESTIONS")

    local i=1
    while IFS= read -r cmd; do
        if [[ -n "$cmd" ]]; then
            echo -e "  ${_SSA_BLUE}[$i]${_SSA_RESET} $cmd"
            ((i++))
        fi
    done <<< "$suggestions"

    echo ""
    echo -e "${_SSA_YELLOW}Tip: Copy a suggestion or modify as needed${_SSA_RESET}"
}

# Get error fix suggestions
smart-fix() {
    if [[ $_SSA_LAST_EXIT_CODE -eq 0 ]]; then
        echo -e "${_SSA_GREEN}✓ Last command succeeded (exit code 0)${_SSA_RESET}"
        return 0
    fi

    echo -e "${_SSA_YELLOW}Analyzing last error...${_SSA_RESET}"

    # Build JSON payload
    local payload=$(cat <<EOF
{
  "error_message": "Command failed with exit code $_SSA_LAST_EXIT_CODE",
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
        echo -e "${_SSA_RED}✗ Failed to connect to Smart Assistant API${_SSA_RESET}"
        return 1
    fi

    # Display fixes
    echo ""
    echo -e "${_SSA_GREEN}Suggested Fixes:${_SSA_RESET}"
    echo "$response" | grep -o '"fixes":\s*\[[^]]*\]' | head -n 3
    echo ""
}

# Toggle Smart Assistant
smart-toggle() {
    if [[ "$SMART_ASSISTANT_ENABLED" == "true" ]]; then
        export SMART_ASSISTANT_ENABLED="false"
        echo -e "${_SSA_YELLOW}Smart Assistant disabled${_SSA_RESET}"
    else
        export SMART_ASSISTANT_ENABLED="true"
        echo -e "${_SSA_GREEN}Smart Assistant enabled${_SSA_RESET}"
    fi
}

# Aliases
alias ss='smart-suggest'
alias sf='smart-fix'
alias st='smart-toggle'

# Show status on load
if [[ "$SMART_ASSISTANT_ENABLED" == "true" ]]; then
    echo -e "${_SSA_GREEN}✓ Smart Shell Assistant loaded${_SSA_RESET}"
fi
