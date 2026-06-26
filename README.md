# Homelab Network Diagnostics (`homelab-netstats`)

`homelab-netstats` is a Streamlit-based web application that displays local system network configurations and performs real-time latency and DNS resolution diagnostics.

While initially created as a dummy/test project to validate the **Proxmox Cloud-Init VM deployment pathway** in `homelab-factory`, it serves as a highly functional diagnostics dashboard for monitoring homelab network stability.

---

## ⚡ Features

- **System Network Config**: Shows active network interfaces, IP addresses, default gateway, and system DNS resolvers (reads `/etc/resolv.conf`).
- **Latency Diagnostics (ICMP)**: Measures round-trip average latencies and packet loss to key homelab & public endpoints:
  - Default Gateway
  - Local AdGuard DNS (`192.168.20.214`)
  - Cloudflare DNS (`1.1.1.1`)
  - Google DNS (`8.8.8.8`)
- **DNS Resolution Testing**: Performs quick lookups and measures resolution speeds (in milliseconds) for target hosts like `google.com`, `npm.mapleleafhome.net`, and local internal domains, utilizing both the system's default resolver and the local AdGuard resolver specifically.

---

## 🚀 Quickstart & Orchestration

The project contains a `Makefile` to simplify local running, Docker image builds, and Docker Compose orchestration.

### Prerequisites

To run locally on your host:
- Python 3.10+
- `iputils-ping` (Linux) / standard `ping` (macOS)
- `dnsutils` (`dig` command)

To run via Docker:
- Docker and Docker Compose

### Makefile Targets

| Command | Action |
| :--- | :--- |
| `make` | Runs the default target (`make help`), displaying a formatted help menu of all commands. |
| `make env` | Installs system/Python dependencies and creates the `.venv` virtual environment. |
| `make dev` | Launches the Streamlit server locally on `http://localhost:8501`. (Automatically runs `make env` first if the virtual environment doesn't exist). |
| `make docker-build` | Builds the production-ready Docker container `homelab-netstats:latest`. |
| `make docker-run` | Runs the containerized application via Docker Compose in detached mode. |
| `make docker-stop` | Stops the active Docker Compose stack. |
| `make clean` | Removes the local virtual environment and Python compiler caches. |

---

## 📂 Detailed Documentation

For deep dives into how this tool operates and integrates with the overall homelab setup, please reference:

- 🏗️ **[Architecture & Diagnostics](docs/architecture.md)**: Explains the internal mechanisms of how network stats, DNS logs, and ping details are acquired.
- 🚀 **[Deployment Guide](docs/deployment.md)**: Details the onboarding process to `homelab-factory`, Proxmox Cloud-Init configuration, Ansible playbooks, and proxy integration.
