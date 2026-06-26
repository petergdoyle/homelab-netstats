# Deployment & Homelab Integration Guide

This guide details how `homelab-netstats` is integrated into the larger `homelab-factory` orchestration platform as a Proxmox Cloud-Init Virtual Machine.

---

## 🚀 Homelab Wizard Onboarding

`homelab-netstats` was registered in the homelab inventory using the interactive wizard:
```bash
python3 scripts/homelab_wizard.py
```

### Wizard Inputs:
- **Application Name**: `homelab-netstats`
- **Hosting Model**: `Proxmox VM (Cloud-Init)`
- **VM ID**: `216` (IP: `192.168.20.216`)
- **Port**: `8501` (HTTP, WebSockets enabled)
- **Domain**: `homelab-netstats.mapleleafhome.net`
- **Visibility**: `internal`
- **SSO Authentication**: Required (`auth_level: user`)

---

## 🛠️ Infrastructure Configuration (Terraform)

The VM is provisioned via the `bpg/proxmox` (v0.51.1) provider on Proxmox, using the `proxmox_virtual_environment_vm` resource.

### 1. Inventory Entry (`homelab.yml`)
The app registration inside `homelab-factory/homelab.yml`:
```yaml
    homelab-netstats:
      vm_id: 216
      hostname: homelab-netstats
      ip_address: 192.168.20.216
      hosting_type: vm
      cores: 2
      memory: 1024
      repo_url: git@github.com:petergdoyle/homelab-netstats.git
      template_vm_id: 9000
      auth_level: user
      visibility: internal
```

### 2. VM VM Template & Cloud-Init
- **Template ID `9000`**: A pre-baked Debian 13 (Trixie) Cloud-Init image.
- **SSH Key & User**: Terraform dynamically injects the public SSH keys and assigns the default Cloud-Init login user: `"debian"`.
- **Ansible Variable Association**: The dynamic Ansible inventory parser automatically maps `ansible_user: debian` for this target when parsing VM host configurations.

---

## 🛰️ Deployment Playbook (Ansible)

A dedicated playbook (`ansible/playbooks/apps/homelab-netstats.yml`) was generated to manage the software state on the VM:
1. Installs Docker, Docker Compose, and utility packages.
2. Clones the application repository `git@github.com:petergdoyle/homelab-netstats.git` to `/opt/homelab-netstats`.
3. Triggers the Docker Compose systemd service or compose orchestrator.
4. Starts the Streamlit service on port `8501`.

---

## 🛡️ Reverse Proxy & SSO (Nginx)

Because Streamlit relies heavily on persistent WebSocket connections for UI rendering and state updates, specific proxy parameters are enforced:

### Nginx Config Overrides (`docs/nginx/advanced_homelab-netstats.conf`)
- **WebSockets Support**:
  ```nginx
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  ```
- **SSO Integration**: Routed through the local Authentik instance (`auth_level: user`) to ensure only authorized homelab users can trigger ping/DNS checks.
