#!/bin/bash

CONFIG_FILE="config.yaml"
TEMPLATE_FILE="templates/nginx_template.j2"

install_requirements() {
    apt-get install -qy python3-pip python3.10 python3.10-venv
    python3 -m venv .venv
    source .venv/bin/activate
    pip3 install --upgrade pip
    pip3 install -r python/requirements.txt
}

main() {
    echo "Using config: $CONFIG_FILE"
    python3 python/reverse_proxy.py $CONFIG_FILE $TEMPLATE_FILE
}


declare -A arguments
for argument in "$@"; do
    IFS='=' read -r item_key item_value <<< "$argument"
    case "$item_key" in
        "--install-requirements")
            install_requirements
            exit 0;
            ;;
        "--config")
            CONFIG_FILE=$item_value
            ;;
    esac
done

main
