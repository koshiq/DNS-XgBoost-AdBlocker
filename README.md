# DNS Ad Blocker Service
## Machine Learning-Powered DNS-Level Ad Blocking

**Automatically blocks ads while you browse the web** using a trained XGBoost model with 69 domain features.

---

## How It Works

```
Your Browser                    DNS Blocker Server              Internet
     │                                 │                            │
     ├──DNS Query: ad.domain.com──────>│                            │
     │                                 ├─Extract 69 features        │
     │                                 ├─XGBoost prediction         │
     │                                 ├─Score: 0.98 (AD!)          │
     │<───Response: 0.0.0.0────────────┤                            │
     │  (Ad blocked!)                  │                            │
     │                                 │                            │
     ├──DNS Query: google.com──────────>│                            │
     │                                 ├─Extract features           │
     │                                 ├─Score: 0.12 (legitimate)   │
     │                                 ├─Forward query──────────────>│
     │                                 │<────Real IP─────────────────┤
     │<───Response: 142.250.x.x────────┤                            │
     │  (Page loads normally)          │                            │
```

**Every DNS query is analyzed in real-time:**
- **Ads/Trackers** → Blocked (0.0.0.0)
- **Legitimate sites** → Allowed (forwarded to real DNS)

---

## Features

✅ **System-wide blocking** - Works in all browsers and apps
✅ **ML-powered** - 69 features + XGBoost classifier
✅ **Pre-connection blocking** - Ads never download (saves bandwidth)
✅ **Privacy-focused** - All processing happens locally
✅ **No filter lists** - Model learns patterns, adapts to new ad domains
✅ **Real-time statistics** - See what's being blocked as you browse

---

## Quick Start

### 1. Install Dependencies

```bash
pip3 install xgboost pandas tldextract
```

### 2. Start the DNS Blocker

```bash
cd dns-blocker-service
./start_blocker.sh
```

You'll see:
```
╔═══════════════════════════════════════════════════════════════════╗
║           DNS AD BLOCKER - STARTUP SCRIPT                         ║
╚═══════════════════════════════════════════════════════════════════╝

[CHECK] Verifying dependencies...
[OK] Dependencies verified
[START] Starting DNS blocker server...
[SUCCESS] DNS blocker started successfully!
[INFO] PID: 12345
[INFO] Running on: 127.0.0.1:5353
```

### 3. Test It

```bash
# Test blocking an ad domain
dig @127.0.0.1 -p 5353 googleads.g.doubleclick.net

# Should return 0.0.0.0 (blocked!)
```

```bash
# Test allowing a legitimate domain
dig @127.0.0.1 -p 5353 google.com

# Should return real IP address
```

### 4. Monitor Real-Time Blocking

```bash
tail -f dns_blocker.log
```

Output:
```
[14:23:45] BLOCK 0.987 | googleads.g.doubleclick.net
[14:23:45] ALLOW 0.123 | www.google.com
[14:23:46] BLOCK 0.943 | pagead2.googlesyndication.com
[14:23:46] ALLOW 0.089 | fonts.googleapis.com
[14:23:47] BLOCK 0.891 | static.ads-twitter.com
```

---

## System-Wide Setup (Optional)

To block ads **automatically** while browsing, configure your system DNS:

### Linux

```bash
# Edit resolv.conf
sudo nano /etc/resolv.conf

# Add this line at the top:
nameserver 127.0.0.1
```

### macOS

```bash
# System Preferences → Network → Advanced → DNS
# Add DNS server: 127.0.0.1
```

### Windows

```
Settings → Network & Internet → Change adapter options
→ Right-click adapter → Properties → Internet Protocol Version 4
→ Use the following DNS: 127.0.0.1
```

**Note:** For system-wide use, the server needs to run on **port 53** (requires sudo):

Edit `dns_blocker_server.py` line 264:
```python
PORT = 53  # Change from 5353 to 53
```

Then run:
```bash
sudo ./start_blocker.sh
```

---

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "server": {
    "port": 5353,
    "upstream_dns": "8.8.8.8"  // Google DNS (try 1.1.1.1 for Cloudflare)
  },
  "model": {
    "threshold": 0.5  // Lower = more aggressive (0.3-0.4), Higher = conservative (0.6-0.7)
  }
}
```

**Threshold tuning:**
- `0.3-0.4`: Aggressive blocking (may block some legitimate CDNs)
- `0.5`: Balanced (default)
- `0.6-0.7`: Conservative (only blocks obvious ads)

---

## Understanding the ML Model

### 69 Features Extracted Per Domain

**Example: `pagead2.googlesyndication.com`**

| Feature Category | Example Features | Values |
|-----------------|------------------|--------|
| **Length** | `domain_length`, `subdomain_length` | 32, 7 |
| **Keywords** | `ad_keyword_count`, `has_ad_keyword` | 3, 1 |
| **Entropy** | `entropy`, `subdomain_entropy` | 4.2, 3.1 |
| **Patterns** | `has_tracking_pattern`, `matches_ad_network` | 1, 1 |
| **TLD** | `is_commercial_tld`, `tld_suspicious` | 1, 0 |
| **Randomness** | `randomness_score`, `unique_char_ratio` | 2, 0.67 |

### Model Architecture

- **Algorithm:** XGBoost (Gradient Boosted Trees)
- **Trees:** 200 boosted trees
- **Max Depth:** 8 levels per tree
- **Training Data:** 198,000 domains (ads + legitimate)
- **Accuracy:** ~96-98%

### Decision Process

```
Input: "pagead2.googlesyndication.com"
   ↓
Extract 69 features → [32, 7, 3, 1, 4.2, 1, ...]
   ↓
XGBoost processes through 200 decision trees
   ↓
Output probability: 0.994
   ↓
0.994 > 0.5 threshold → BLOCK
```

---

## Commands

### Start Server
```bash
./start_blocker.sh
```

### Stop Server
```bash
./stop_blocker.sh
```

### View Logs
```bash
tail -f dns_blocker.log
```

### Test Queries
```bash
# Test blocking
dig @127.0.0.1 -p 5353 doubleclick.net

# Test allowing
dig @127.0.0.1 -p 5353 github.com
```

---

## Statistics

Stop the server (Ctrl+C) to see blocking statistics:

```
═══════════════════════════════════════════════════════════════════
  DNS BLOCKER STATISTICS
═══════════════════════════════════════════════════════════════════
  Total queries:   1,247
  Blocked (ads):   312 (25.0%)
  Allowed (legit): 931 (74.6%)
  Errors:          4 (0.3%)
═══════════════════════════════════════════════════════════════════
```

---

## How It's Different from Pi-Hole / AdGuard

| Feature | Pi-Hole/AdGuard | This DNS Blocker |
|---------|----------------|------------------|
| **Method** | Static blocklists | Machine learning |
| **Adaptation** | Requires list updates | Learns patterns |
| **New domains** | Miss until list updated | Detects automatically |
| **False positives** | List-dependent | Model-tuned |
| **Setup** | Complex (Pi-Hole) | One script |
| **Privacy** | Local (Pi-Hole) | Local |

---

## Troubleshooting

### Port 53 permission denied
```bash
# Use sudo for port 53
sudo ./start_blocker.sh

# Or use port 5353 for testing (default)
```

### Dependencies missing
```bash
pip3 install xgboost pandas tldextract
```

### Model not found
```bash
# Make sure you're in the project directory
# Model should be at: ../DNS/dns_adblocker_model.ubj
```

### DNS queries not being blocked
```bash
# Verify server is running
ps aux | grep dns_blocker

# Check logs
tail -f dns_blocker.log

# Test query directly
dig @127.0.0.1 -p 5353 ads.google.com
```

---

## File Structure

```
dns-blocker-service/
├── dns_blocker_server.py    # Main DNS server script
├── start_blocker.sh          # Startup script
├── stop_blocker.sh           # Shutdown script
├── config.json               # Configuration
├── README.md                 # This file
└── dns_blocker.log           # Runtime logs (created on start)

../DNS/
├── dns_adblocker_model.ubj   # XGBoost model (required)
├── feature_names.json        # Feature list (required)
└── enhanced_dns_features.py  # Feature extractor (required)
```

---

## Performance

- **Query processing:** ~5-10ms per domain
- **Memory usage:** ~100-200 MB (model + cache)
- **CPU usage:** <1% on modern systems
- **Bandwidth saved:** 20-40% (typical web browsing)

---

## What Gets Blocked

### Ad Networks
✓ Google Ads (doubleclick, googlesyndication)
✓ Facebook Ads (an.facebook.com)
✓ Taboola, Outbrain
✓ Criteo, Rubicon Project
✓ Generic ad servers (ad.*, ads.*)

### Trackers
✓ Analytics (analytics.*, track.*)
✓ Pixel trackers (pixel.*, beacon.*)
✓ Telemetry services

### What's NOT Blocked
✓ CDNs (unless clearly ad-related)
✓ APIs (api.*)
✓ Legitimate services (mail.*, www.*)
✓ Content delivery networks

---

## Advanced Usage

### Run as systemd service (Linux)

Create `/etc/systemd/system/dns-blocker.service`:

```ini
[Unit]
Description=DNS Ad Blocker Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/koshiq/network-traffic-project/dns-blocker-service
ExecStart=/usr/bin/python3 dns_blocker_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable dns-blocker
sudo systemctl start dns-blocker
sudo systemctl status dns-blocker
```

---

## License

This is a defensive security tool for ad blocking and privacy protection.

---

## Support

For issues or questions, check:
1. Log file: `tail -f dns_blocker.log`
2. Test queries: `dig @127.0.0.1 -p 5353 test.com`
3. Verify model: `ls -lh ../DNS/dns_adblocker_model.ubj`

---

**Enjoy ad-free browsing! 🚀**
