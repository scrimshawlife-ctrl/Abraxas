# Systemd Unit Files

These systemd service files enable Abraxas to run as a system service on Jetson Orin or other Linux systems.

## Installation

```bash
# Copy service files to systemd directory
sudo cp systemd/abraxas-core.service /etc/systemd/system/
sudo cp systemd/aal-overlay@.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start core service
sudo systemctl enable abraxas-core
sudo systemctl start abraxas-core

# Check status
sudo systemctl status abraxas-core
```

## Managing Overlays

```bash
# Start a specific overlay
sudo systemctl start aal-overlay@my-overlay

# Enable overlay to start on boot
sudo systemctl enable aal-overlay@my-overlay

# Check overlay status
sudo systemctl status aal-overlay@my-overlay

# Stop overlay
sudo systemctl stop aal-overlay@my-overlay
```

## Configuration

Edit the service files to customize:
- `User`: Run as different user (default: `orin`)
- `WorkingDirectory`: Installation path (default: `/opt/aal/abraxas`)
- Environment variables for runtime configuration

## Logs

View service logs:
```bash
# Core service logs
sudo journalctl -u abraxas-core -f

# Overlay logs
sudo journalctl -u aal-overlay@my-overlay -f
```
