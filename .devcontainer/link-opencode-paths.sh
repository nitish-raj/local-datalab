#!/usr/bin/env bash
set -euo pipefail

CONFIG_MOUNT="/var/opencode/config"
DATA_MOUNT="/var/opencode/data"
CODEX_HOME_MOUNT="/var/codex/home"

CONFIG_DEST="${HOME}/.config/opencode"
DATA_DEST="${HOME}/.local/share/opencode"
CODEX_HOME_DEST="${HOME}/.codex"

mkdir -p "${HOME}/.config" "${HOME}/.local/share" "${CONFIG_MOUNT}" "${DATA_MOUNT}" "${CODEX_HOME_MOUNT}"

link_path() {
  local src="$1"
  local dest="$2"

  if [ -L "${dest}" ]; then
    ln -sfn "${src}" "${dest}"
    return
  fi

  if [ -e "${dest}" ]; then
    rm -rf "${dest}"
  fi

  ln -s "${src}" "${dest}"
}

link_path "${CONFIG_MOUNT}" "${CONFIG_DEST}"
link_path "${DATA_MOUNT}" "${DATA_DEST}"
link_path "${CODEX_HOME_MOUNT}" "${CODEX_HOME_DEST}"

echo "[bootstrap] Linked OpenCode and Codex config/data into ${HOME}"
