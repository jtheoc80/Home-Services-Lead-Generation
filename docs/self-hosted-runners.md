# Self-Hosted GitHub Actions Runners Setup Guide

This guide explains how to set up and configure self-hosted GitHub Actions runners for the Home Services Lead Generation platform, specifically for data scraping and processing workflows.

## Why Self-Hosted Runners?

Self-hosted runners provide several advantages for data scraping and processing workflows:

- **Dedicated Resources**: Consistent performance without GitHub Actions usage limits
- **Network Control**: Better handling of rate limits and IP-based restrictions
- **Custom Environment**: Pre-installed tools and configurations
- **Cost Efficiency**: For heavy workloads, can be more cost-effective than GitHub-hosted runners
- **Geographic Control**: Run scraping from specific geographic locations if needed

## Runner Setup

### 1. Provision a Virtual Machine

**Minimum Requirements:**
- **OS**: Linux (Ubuntu 20.04+ or similar)
- **CPU**: 2+ cores
- **RAM**: 4GB+ (8GB recommended for heavy scraping)
- **Disk**: 20GB+ available space
- **Network**: Outbound internet access (no inbound required)

**Recommended Cloud Providers:**
- AWS EC2 (t3.medium or larger)
- Google Cloud Compute Engine (e2-medium or larger)  
- Azure Virtual Machines (Standard_B2s or larger)
- DigitalOcean Droplets (4GB+ memory)

### 2. Install GitHub Actions Runner

```bash
# Create a dedicated user for the runner
sudo useradd -m -s /bin/bash github-runner
sudo usermod -aG sudo github-runner

# Switch to the runner user
sudo su - github-runner

# Create runner directory
mkdir actions-runner && cd actions-runner

# Download the latest runner package
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure the runner (interactive)
./config.sh --url https://github.com/jtheoc80/Home-Services-Lead-Generation --token YOUR_TOKEN
```

### 3. Configure Runner Labels

When configuring the runner, use these specific labels:
```
linux,x64,scrape
```

This creates a runner that matches: `runs-on: [self-hosted, linux, x64, scrape]`

### 4. Install Dependencies

```bash
# System dependencies
sudo apt update
sudo apt install -y curl wget git jq python3 python3-pip nodejs npm

# Python dependencies for scraping
pip3 install requests pyyaml beautifulsoup4 pandas

# Node.js dependencies (install globally for runner access)
sudo npm install -g tsx typescript

# Verify installations
python3 --version
node --version
npm --version
```

### 5. Start Runner as Service

```bash
# Install as a system service
sudo ./svc.sh install github-runner

# Start the service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status

# Enable auto-start on boot
sudo systemctl enable actions.runner.jtheoc80-Home-Services-Lead-Generation.RUNNER_NAME.service
```

## Workflow Configuration

### Basic Self-Hosted Workflow Pattern

```yaml
name: Self-Hosted Workflow Example

on:
  workflow_dispatch: {}
  schedule:
    - cron: "0 6 * * *"

# Prevent overlapping runs
concurrency:
  group: scrape-${{ github.ref }}
  cancel-in-progress: false

jobs:
  scrape-job:
    runs-on: [self-hosted, linux, x64, scrape]
    timeout-minutes: 30
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install requests pyyaml
      - run: python scripts/your-scraper.py
```

### Health Check Workflow

The repository includes `self-hosted-health.yml` which runs every 30 minutes to check data source availability:

```yaml
jobs:
  health:
    runs-on: [self-hosted, linux, x64, scrape]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install requests pyyaml
      - run: python scripts/agents/source_probe.py
```

### Houston Backfill Workflow

The repository includes `self-hosted-houston-backfill.yml` for processing Houston permit archives:

```yaml
jobs:
  backfill:
    runs-on: [self-hosted, linux, x64, scrape]
    env:
      SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
      SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
      ARCHIVE_WEEKS: 12
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npx tsx scripts/ingest-coh-archives.ts
```

## Security Considerations

### Secrets Management

**✅ Do:**
- Store all secrets in GitHub Repository Secrets
- Use environment variables in workflows
- Rotate secrets regularly

**❌ Don't:**
- Store secrets on the runner machine
- Hardcode credentials in scripts
- Share secrets between environments

### Network Security

**Runner Network Configuration:**
- Outbound internet access required
- No inbound ports need to be open
- Consider firewall rules for specific destinations only

**Supabase IP Allowlists:**
If your Supabase project has IP allowlists enabled, add your runner's egress IP addresses:

```bash
# Get your runner's external IP
curl -s https://api.ipify.org
```

Then add this IP to your Supabase project settings.

### System Security

```bash
# Keep system updated
sudo apt update && sudo apt upgrade -y

# Configure automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades

# Basic firewall (outbound only)
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

## Monitoring and Maintenance

### Runner Health Monitoring

```bash
# Check runner service status
sudo systemctl status actions.runner.*.service

# View runner logs
sudo journalctl -u actions.runner.*.service -f

# Check disk space
df -h

# Check system resources
htop
```

### Workflow Monitoring

Monitor self-hosted workflows in GitHub Actions:
- Check for failed runs due to runner unavailability
- Monitor runner utilization and queue times
- Review artifact uploads and storage usage

### Maintenance Tasks

**Weekly:**
- Check system updates
- Review workflow success rates
- Monitor disk space usage

**Monthly:**
- Rotate runner registration tokens
- Review and update dependencies
- Check for GitHub Actions runner updates

## Troubleshooting

### Runner Not Appearing in GitHub

1. Check runner service status:
   ```bash
   sudo systemctl status actions.runner.*.service
   ```

2. Verify network connectivity:
   ```bash
   curl -I https://github.com
   ```

3. Check runner logs:
   ```bash
   sudo journalctl -u actions.runner.*.service -n 50
   ```

### Workflow Failures

1. **Network timeouts**: Increase timeout values or check internet connectivity
2. **Permission errors**: Verify runner user has necessary permissions
3. **Missing dependencies**: Ensure all required packages are installed
4. **Disk space**: Check available disk space for artifacts and logs

### Performance Issues

1. **High CPU usage**: Monitor with `htop`, consider larger instance
2. **Memory issues**: Check with `free -h`, increase RAM if needed
3. **Slow network**: Test bandwidth with speed tests

## Migration from GitHub-Hosted Runners

To migrate existing workflows to self-hosted runners:

1. **Update `runs-on`**:
   ```yaml
   # Before
   runs-on: ubuntu-latest
   
   # After  
   runs-on: [self-hosted, linux, x64, scrape]
   ```

2. **Add concurrency controls**:
   ```yaml
   concurrency:
     group: scrape-${{ github.ref }}
     cancel-in-progress: false
   ```

3. **Test thoroughly**:
   - Run workflows manually first
   - Verify all dependencies are available
   - Check artifact uploads work correctly

4. **Monitor initial runs**:
   - Watch for timeouts or failures
   - Verify performance is acceptable
   - Check resource usage on runner

## Cost Analysis

**GitHub-hosted runners:**
- $0.008/minute for Linux runners
- 2,000 free minutes/month for private repos

**Self-hosted runners:**
- VM costs vary by provider ($20-100/month typical)
- No GitHub Actions minute charges
- Break-even point: ~250-1,250 minutes/month depending on VM cost

For heavy scraping workloads (>500 minutes/month), self-hosted runners are typically more cost-effective.

## Example Configurations

### Development/Testing Runner

```bash
# Smaller VM for testing
# 1 vCPU, 2GB RAM, 10GB disk
# Suitable for occasional testing
```

### Production Scraping Runner

```bash
# Dedicated scraping VM
# 2+ vCPU, 4GB+ RAM, 20GB+ disk
# For daily/hourly scraping workflows
```

### High-Volume Processing Runner

```bash
# Heavy processing VM
# 4+ vCPU, 8GB+ RAM, 50GB+ disk
# For large-scale data processing
```

## Related Documentation

- [GitHub Actions Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Repository Secrets Configuration](./workflows-secrets.md)
- [GitHub Actions Runbook](./github-actions-runbook.md)
- [Operations Runbooks](./ops/runbooks.md)

## Support

For issues with self-hosted runner setup:

1. Check this documentation first
2. Review GitHub Actions runner logs
3. Test with simple workflows before complex ones
4. Consider starting with GitHub-hosted runners for initial development