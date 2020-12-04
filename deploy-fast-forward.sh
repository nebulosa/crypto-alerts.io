#!/bin/sh
CURRENT_DIR="$(cd "$(dirname "${0}")" && pwd)"

if [ -z "${1}" ]; then
    printf "%s\\n" "Define target environment: vagrant|stage|prod" >&2
    exit 1
fi

if [ ! -f "${CURRENT_DIR}/.vault_pass.txt" ]; then
    printf "%s\\n" "${CURRENT_DIR}/.vault_pass.txt doesn't exists, exiting ..." >&2
    exit 1
fi

cd "${CURRENT_DIR}"
cd provision/ansible/

#https://mitogen.readthedocs.io/en/latest/ansible.html
if [ ! -d "mitogen-0.2.9/ansible_mitogen/plugins/strategy" ]; then
    wget https://files.pythonhosted.org/packages/source/m/mitogen/mitogen-0.2.9.tar.gz
    tar zxf mitogen-0.2.9.tar.gz
fi

set -x
ansible-playbook app.yml -i inventories/"${1}"/hosts --vault-password-file ../../.vault_pass.txt --tags app
