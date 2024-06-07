#!/bin/bash
set -e

# Colors for logging
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

CONFIG_FILE="config.yaml"
TEMPLATE_FILE="templates/nginx_template.j2"
DEBUG=false
DRY_RUN=false
HOST_NAME="localhost"
OUTPUT="output"
VIRTUAL_ENV=.venv

# Logger functions
log_info() {
    echo "${GREEN}INFO: $1 ${RESET}"
}

log_error() {
    echo "${RED}ERROR: $1 ${RESET}" >&2
}

log_warning() {
    echo "${YELLOW}WARNING: $1 ${RESET}"
}

ssh_execute() {
    local command="$1"
    if [ -n "$SSH_PASSWORD" ]; then
        sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$SSH_USERNAME@$HOST_NAME" "$command"
    elif [ -n "$SSH_PRIVATE_KEY" ]; then
        ssh -i "$SSH_PRIVATE_KEY" -o StrictHostKeyChecking=no "$SSH_USERNAME@$HOST_NAME" "$command"
    else
        log_error "Either SSH password or private key must be specified for deployment."
        exit 1
    fi
    if [ $? -ne 0 ]; then
        log_error "Failed to execute command $command"
        exit 1
    fi
}

ssh_copy() {
    local src=$1
    local dst=$2
    if [ -n "$SSH_PASSWORD" ]; then
        sshpass -p "$SSH_PASSWORD" scp -o StrictHostKeyChecking=no -r $src "$SSH_USERNAME@$HOST_NAME":$dst
    elif [ -n "$SSH_PRIVATE_KEY" ]; then
        scp -i "$SSH_PRIVATE_KEY" -o StrictHostKeyChecking=no -r $src "$SSH_USERNAME@$HOST_NAME":$dst
    fi
    if [ $? -ne 0 ]; then
        log_error "Failed to copy the $src to $dst"
        exit 1
    fi
}

help () {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --install-requirements          Install the required packages and Python dependencies."
    echo "  --config=<config_file>          Specify the configuration file to use (default: config.yaml)."
    echo "  --host=<ip or host>             Deploy the generated NGINX config to the specified host.(default: localhost)"
    echo "  --username=<ssh_username>       Specify the SSH username for deployment."
    echo "  --password=<ssh_password>       Specify the SSH password for deployment."
    echo "  --key=<ssh_private_key>         Specify the SSH private key for deployment."
    echo "  --build                         Build a python binary script file from source."
    echo "  --debug                         Run reverse proxy using source code."
    echo "  --dry-run                       Run the script to validate input config."
    echo "  --clean                         Clean the environment."
    echo "  --help                          Show this help message and exit."
    echo
    echo "Example:"
    echo "  $0 --install-requirements"
    echo "  $0 --config=my_config.yaml"
    echo "  $0 --host=hostname --username=myuser --password=mypassword"
    echo "  $0 --host=hostname --username=myuser --key=/path/to/private_key"
}

install_requirements() {
    DISTRO=$(lsb_release -cs)
    rm -rf $VIRTUAL_ENV
    case "$DISTRO" in
        jammy | noble)
            apt-get install -qy python3-pip python3.10 python3.10-venv python3-dev
            python3.10 -m venv $VIRTUAL_ENV
            ;;
        focal)
            apt-get install -qy python3-pip python3.8 python3.8-venv python3-dev
            python3.8 -m venv $VIRTUAL_ENV
            ;;
        bionic)
            apt-get install -qy python3-pip python3.7 python3.7-venv libpython3.7-dev
            python3.7 -m venv $VIRTUAL_ENV
            ;;
        *)
            log_error "Unsupported Ubuntu version to installing python requirements: $DISTRO"
            exit 1
            ;;
    esac
    source $VIRTUAL_ENV/bin/activate
    pip3 install --upgrade pip
    pip3 install -r src/python/requirements.txt
}

generate_config() {
    log_info "Using config: $CONFIG_FILE"
    if [ "$DEBUG" == true ]; then
        source $VIRTUAL_ENV/bin/activate
        python3 src/python/reverse_proxy.py $CONFIG_FILE $TEMPLATE_FILE $OUTPUT
    else
        BINARY_FILE=dist/reverse_proxy
        if [ ! -f "$BINARY_FILE" ]; then
            log_error "Binary script '$BINARY_FILE' not found! Use '--build' option".
            exit 1
        fi
        $BINARY_FILE $CONFIG_FILE $TEMPLATE_FILE $OUTPUT
    fi
    log_info "NGINX config successfully generated in $OUTPUT."
}

deploy_localy() {
    if ! command -v nginx &> /dev/null; then
        log_info "Installing nginx"
        apt-get install -qy nginx
    fi
    cp -rf $OUTPUT/*.conf /etc/nginx/conf.d/
    nginx -t
    systemctl restart nginx
    log_info "Deployed and restarted NGINX locally"
}

deploy_to_host() {
    if ! command -v sshpass &> /dev/null; then
        log_info "Installing sshpass"
        apt-get install -qy sshpass
    fi
    ssh_execute "apt-get update && sudo apt-get install -qy nginx"
    ssh_execute "ufw allow 'Nginx Full'"
    ssh_execute "ufw reload"
    ssh_copy "$OUTPUT/*.conf" "/etc/nginx/conf.d/"
    ssh_execute "nginx -t"
    ssh_execute "systemctl restart nginx"
    log_info "Deployed and restarted NGINX on $host"
}

clean() {
    rm -rf .venv dist build output || true
    log_info "Directory cleaned!"
}

build() {
    if [ ! -d .venv ]; then
        log_info "Requirements not found. Installing requirements"
        install_requirements
    fi
    source $VIRTUAL_ENV/bin/activate
    pyinstaller --onefile src/python/reverse_proxy.py 
    log_info "Binary script generated successfully!"
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
        "--dry-run")
            DRY_RUN=true
            ;;
        "--host")
            HOST_NAME=$item_value
            ;;
        "--username")
            SSH_USERNAME=$item_value
            ;;
        "--password")
            SSH_PASSWORD=$item_value
            ;;
        "--key")
            SSH_PRIVATE_KEY=$item_value
            ;;
        "--help")
            help
            exit 0;
            ;;
        "--debug")
            DEBUG=true
            ;;
        "--build")
            build
            exit 0;
            ;;
        "--clean")
            clean
            exit 0;
            ;;
        *)
            log_error "Unknown option: $item_key"
            help
            exit 1;
            ;;
    esac
done

main() {
    rm -rf $OUTPUT
    mkdir -p $OUTPUT
    generate_config
    if [ "$DRY_RUN" == true ]; then
        exit 0;
    fi
    if [[ $HOST_NAME == "localhost" ]]; then
        deploy_localy
    elif [[ ! -z $HOST_NAME ]]; then
        deploy_to_host
    else
        log_error "Invalid host name. use --host option"
    fi
}

main