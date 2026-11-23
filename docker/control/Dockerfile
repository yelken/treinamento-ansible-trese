# Nó de controle do laboratório: é aqui que o aluno trabalha.
# Contexto de build: docker/   (veja compose.yml)
FROM python:3.13.18-slim-trixie

ARG DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

# Ferramentas de linha de comando do aluno.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates; \
    apt-get install -y --no-install-recommends \
        openssh-client sshpass git vim nano curl jq less tree rsync procps \
        iputils-ping bash-completion unzip; \
    rm -rf /var/lib/apt/lists/*

# Certificados de CA corporativa (proxy com inspeção TLS). Opcional: veja docker/certs/README.md
COPY certs/ /tmp/certs/
RUN set -eux; \
    for f in /tmp/certs/*.crt; do \
        [ -e "$f" ] && cp "$f" /usr/local/share/ca-certificates/ || true; \
    done; \
    update-ca-certificates; \
    rm -rf /tmp/certs

# Ansible e ferramentas de qualidade (versões fixadas; constraints.txt trava também as dependências).
COPY control/requirements.txt control/constraints.txt control/requirements.yml /tmp/build/
RUN set -eux; \
    export PIP_CERT=/etc/ssl/certs/ca-certificates.crt; \
    pip install -r /tmp/build/requirements.txt -c /tmp/build/constraints.txt; \
    mkdir -p /usr/share/ansible/collections; \
    ansible-galaxy collection install -r /tmp/build/requirements.yml \
        -p /usr/share/ansible/collections; \
    rm -rf /tmp/build /root/.ansible

# Usuário do aluno (uid 1000; o entrypoint ajusta o uid ao dono de /lab em hosts Linux).
RUN set -eux; \
    groupadd --gid 1000 aluno; \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash aluno; \
    install -d -m 0755 -o aluno -g aluno /lab; \
    install -d -m 0700 -o aluno -g aluno /home/aluno/.ssh; \
    install -d -m 0755 -o root -g root /lab-pub

# Scripts do laboratório: ficam na imagem, fora de /lab.
COPY control/etc/ansible.cfg /etc/ansible/ansible.cfg
COPY control/etc/ssh-lab.conf /etc/ssh/ssh_config.d/10-lab.conf
COPY control/etc/bashrc-lab /etc/lab/bashrc
COPY control/etc/vimrc.local /etc/vim/vimrc.local
COPY control/etc/nanorc-lab /etc/lab/nanorc
COPY control/lab/ /opt/lab/
RUN set -eux; \
    chmod 0644 /etc/ansible/ansible.cfg /etc/ssh/ssh_config.d/10-lab.conf; \
    printf '\n# Laboratório Ansible\n[ -f /etc/lab/bashrc ] && . /etc/lab/bashrc\n' >> /etc/bash.bashrc; \
    printf '\n# Laboratório Ansible (por último, para o PS1 do lab vencer o padrão do Debian)\n[ -f /etc/lab/bashrc ] && . /etc/lab/bashrc\n' >> /home/aluno/.bashrc; \
    cat /etc/lab/nanorc >> /etc/nanorc; \
    chmod -R a+rX /opt/lab; \
    chmod 0755 /opt/lab/bin/*

ENV ANSIBLE_CONFIG=/etc/ansible/ansible.cfg \
    LANG=C.UTF-8

WORKDIR /lab
ENTRYPOINT ["/opt/lab/bin/entrypoint.sh"]
CMD ["sleep", "infinity"]
