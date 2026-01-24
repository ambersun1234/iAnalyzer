#!/bin/sh
set -e

# Ensure we're in the correct working directory
cd /app

# Check if first argument starts with '--' (CLI-style arguments)
if [ -n "$1" ] && [ "$(echo "$1" | cut -c1-2)" = "--" ]; then
    # Direct CLI execution: pass all arguments as-is to main.py
    exec uv run python main.py "$@"
else
    # Docker/GitHub Actions execution: positional arguments
    # Domain is required (first argument)
    DOMAIN="$1"
    shift

    # Build arguments array
    ARGS="--domain $DOMAIN"

    # Process ignore-prefix if provided (second argument)
    if [ -n "$1" ] && [ "$1" != "" ]; then
        # Split comma-separated values and add each as --ignore-prefix
        IFS=','
        for prefix in $1; do
            # Trim whitespace
            prefix=$(echo "$prefix" | xargs)
            if [ -n "$prefix" ]; then
                ARGS="$ARGS --ignore-prefix $prefix"
            fi
        done
        unset IFS
    fi

    # Execute the main script with all arguments
    exec uv run python main.py $ARGS
fi
