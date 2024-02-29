#!/bin/bash

# Wrapper around the module (environment modules) command which disables
# commands that modify the current environment.
module() {
    args=("$@")
    for arg in "${args[@]}"; do
        case $arg in
            add|load|rm|unload|swap|switch|use|unuse|purge)
                echo "command disabled: module ""${args[*]}" 1>&2
                return 1
                ;;
        esac
    done
    _module_raw "${args[@]}" 2>&1
    return $?
}
