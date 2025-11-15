# Network Traffic Analysis with ML

ML-powered DNS ad blocker using XGBoost to classify domains based on 68 features.

## Quick Start

### 1. Install Dependencies
```bash
pip3 install xgboost pandas tldextract
```

### 2. Run DNS Ad Blocker
```bash
cd dns-blocker-service
sudo ./setup_system_dns.sh  # One-time setup
sudo ./start_simple.sh      # Start blocker
```

### 3. Monitor Blocking
```bash
sudo tail -f dns_blocker.log
```

## Project Structure

- **`DNS/`** - DNS-level ad detection model & feature extraction
  - `dns_adblocker_model.ubj` - Trained XGBoost model (68 features)
  - `feature_names.json` - Model feature list
  - `enhanced_dns_features.py` - Feature extraction (domain analysis)
  - `train_dns_adblocker.ipynb` - Model training notebook

- **`dns-blocker-service/`** - Local DNS server for system-wide ad blocking
  - `dns_blocker_server.py` - Main DNS interceptor
  - `start_simple.sh` / `stop_blocker.sh` - Service controls
  - `setup_system_dns.sh` - System DNS configuration

- **`Data/`** - Training dataset
  - `dns_training_data.csv` - 198k labeled domains

- **`old HTML level/`** - Previous webpage-level models (Chrome extension)

## How It Works

1. Intercepts DNS queries at port 53
2. Extracts 58 features from domain names (length, entropy, keywords, patterns)
3. XGBoost model predicts ad probability
4. Blocks ads by returning 0.0.0.0, allows legitimate domains

## Model Performance

- **Accuracy**: 86.8%
- **Precision**: 92.9%
- **Recall**: 79.8%
- **Features**: 68 domain characteristics

## Known Limitations

Training data has minimal legitimate `www.` domains, causing some false positives on common sites. Model correctly blocks third-party trackers and ad networks.
