import streamlit as st
import subprocess
import re
import pandas as pd
import time
import os
import platform
import urllib.request

st.set_page_config(
    page_title="Homelab Network Diagnostics",
    page_icon="🕸️",
    layout="wide"
)

st.title("🕸️ Homelab Network Stats & Diagnostics")
st.caption(f"Running on Host: `{platform.node()}` ({platform.system()} {platform.release()})")

# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions for System Diagnostics
# ──────────────────────────────────────────────────────────────────────────────
def run_cmd(args):
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return res.stdout.strip()
        else:
            return f"Error (code {res.returncode}): {res.stderr.strip()}"
    except Exception as e:
        return f"Failed to run command: {str(e)}"

def get_interfaces():
    if platform.system() == "Linux":
        out = run_cmd(["ip", "-br", "addr", "show"])
        lines = []
        for line in out.split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                status = parts[1]
                ips = parts[2:] if len(parts) > 2 else []
                lines.append({"Interface": name, "Status": status, "IP Addresses": ", ".join(ips)})
        return pd.DataFrame(lines)
    else:
        # macOS or fallback
        out = run_cmd(["ifconfig"])
        interfaces = []
        current_iface = None
        for line in out.split("\n"):
            if line and not line.startswith("\t"):
                current_iface = line.split(":")[0]
            elif line.strip().startswith("inet "):
                parts = line.strip().split()
                if len(parts) >= 2:
                    interfaces.append({"Interface": current_iface, "Status": "UP", "IP Addresses": parts[1]})
        return pd.DataFrame(interfaces)

def get_gateway():
    if platform.system() == "Linux":
        out = run_cmd(["ip", "route"])
        for line in out.split("\n"):
            if line.startswith("default via"):
                parts = line.split()
                if len(parts) >= 3:
                    return parts[2]
    else:
        # macOS/BSD
        out = run_cmd(["netstat", "-rn"])
        for line in out.split("\n"):
            if line.startswith("default"):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
    return "192.168.20.1" # default fallback

def get_dns_resolvers():
    resolvers = []
    if os.path.exists("/etc/resolv.conf"):
        with open("/etc/resolv.conf", "r") as f:
            for line in f:
                if line.startswith("nameserver"):
                    parts = line.split()
                    if len(parts) >= 2:
                        resolvers.append(parts[1])
    return resolvers if resolvers else ["None found"]

def ping_host(host):
    # -c 3 on Linux, -c 3 on macOS
    cmd = ["ping", "-c", "3", "-W", "2", host]
    out = run_cmd(cmd)
    
    # Parse average latency
    # Linux: rtt min/avg/max/mdev = 0.052/0.058/0.065/0.007 ms
    # macOS: round-trip min/avg/max/stddev = 0.052/0.058/0.065/0.007 ms
    avg_lat = None
    loss_pct = 100
    
    for line in out.split("\n"):
        if "packets transmitted" in line:
            # e.g. "3 packets transmitted, 3 received, 0% packet loss"
            match = re.search(r'(\d+)% packet loss', line)
            if match:
                loss_pct = int(match.group(1))
        if line.startswith("rtt") or line.startswith("round-trip"):
            parts = line.split("=")
            if len(parts) >= 2:
                stats = parts[1].strip().split("/")
                if len(stats) >= 2:
                    avg_lat = float(stats[1])
                    
    return avg_lat, loss_pct, out

def dns_lookup(host, server=None):
    start = time.time()
    cmd = ["dig", "+short", "+tries=1", "+timeout=2", host]
    if server:
        cmd.append(f"@{server}")
    out = run_cmd(cmd)
    duration_ms = (time.time() - start) * 1000
    return out, duration_ms

def get_cloudflare_trace():
    try:
        req = urllib.request.Request(
            "https://www.cloudflare.com/cdn-cgi/trace",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            text = response.read().decode("utf-8")
            data = {}
            for line in text.strip().split("\n"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    data[parts[0]] = parts[1]
            return data
    except Exception as e:
        return {"error": str(e)}

# ──────────────────────────────────────────────────────────────────────────────
# Dashboard UI Layout
# ──────────────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 System Network Config")
    
    st.markdown("**Active Interfaces**")
    df_iface = get_interfaces()
    st.dataframe(df_iface, use_container_width=True)
    
    gw = get_gateway()
    st.markdown(f"**Default Gateway**: `{gw}`")
    
    resolvers = get_dns_resolvers()
    st.markdown(f"**System DNS Resolvers**: `{', '.join(resolvers)}`")
    
    st.markdown("---")
    st.markdown("**Raw DNS `/etc/resolv.conf` contents:**")
    if os.path.exists("/etc/resolv.conf"):
        with open("/etc/resolv.conf", "r") as f:
            st.code(f.read(), language="text")
    else:
        st.write("File `/etc/resolv.conf` not found.")

    st.markdown("---")
    st.subheader("🌐 Public WAN & Cloudflare Edge")
    trace = get_cloudflare_trace()
    if "error" not in trace:
        st.success("Connected to Cloudflare Edge")
        st.markdown(f"**Public WAN IP**: `{trace.get('ip', 'Unknown')}`")
        st.markdown(f"**Cloudflare Data Center**: `{trace.get('colo', 'Unknown')}` ({trace.get('loc', 'Unknown')})")
        st.markdown(f"**Protocol / Security**: `{trace.get('http', 'Unknown')}` / `{trace.get('tls', 'Unknown')}`")
        st.markdown(f"**Warp Status**: `{trace.get('warp', 'off')}`")
    else:
        st.error("Offline / Unable to reach Cloudflare Edge")
        st.caption(f"Error details: `{trace.get('error')}`")

with col2:
    st.subheader("⚡ Active Latency & DNS Verification")
    
    # Diagnostic targets
    targets = {
        "Default Gateway": gw,
        "AdGuard DNS": "192.168.20.214",
        "Cloudflare (1.1.1.1)": "1.1.1.1",
        "Google (8.8.8.8)": "8.8.8.8",
        "Tailscale Subnet Router (205)": "192.168.20.205",
        "Tailscale MagicDNS": "100.100.100.100",
        "Cloudflare Tunnel Daemon (213)": "192.168.20.213"
    }
    
    if st.button("🔄 Run Telemetry Ping Diagnostics", type="primary"):
        st.write("Measuring latency and packet loss (3 ICMP pings per host)...")
        
        metrics = []
        for name, ip in targets.items():
            avg_lat, loss_pct, raw_out = ping_host(ip)
            metrics.append({
                "Target": name,
                "IP Address": ip,
                "Avg Latency (ms)": f"{avg_lat:.2f} ms" if avg_lat is not None else "TIMEOUT",
                "Packet Loss (%)": f"{loss_pct}%",
                "Status": "✅ HEALTHY" if loss_pct == 0 else ("⚠️ LOSS" if loss_pct < 100 else "❌ DOWN")
            })
            
        st.table(pd.DataFrame(metrics))
        
        st.subheader("🔎 DNS Resolution Checks")
        st.write("Testing DNS resolution latency and results...")
        
        dns_targets = ["google.com", "npm.mapleleafhome.net", "speedtest-telemetry.mapleleafhome.net"]
        dns_metrics = []
        for dhost in dns_targets:
            # 1. Resolve using system default
            res, dur = dns_lookup(dhost)
            dns_metrics.append({
                "Query Name": dhost,
                "Resolver": "System Default",
                "Result": res if res else "failed",
                "Time (ms)": f"{dur:.1f} ms"
            })
            # 2. Resolve using local AdGuard DNS specifically
            res_ag, dur_ag = dns_lookup(dhost, "192.168.20.214")
            dns_metrics.append({
                "Query Name": dhost,
                "Resolver": "AdGuard (192.168.20.214)",
                "Result": res_ag if res_ag else "failed",
                "Time (ms)": f"{dur_ag:.1f} ms"
            })
            # 3. Resolve using Tailscale MagicDNS
            res_ts, dur_ts = dns_lookup(dhost, "100.100.100.100")
            dns_metrics.append({
                "Query Name": dhost,
                "Resolver": "Tailscale MagicDNS (100.100.100.100)",
                "Result": res_ts if res_ts else "failed",
                "Time (ms)": f"{dur_ts:.1f} ms"
            })
            
        st.table(pd.DataFrame(dns_metrics))
    else:
        st.info("Click the button above to execute live ping and DNS diagnostics.")
