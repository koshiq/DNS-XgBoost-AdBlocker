#!/usr/bin/env python3
"""
DNS Ad Blocker Server
Intercepts DNS queries and blocks ads using ML model
"""

import socket
import struct
import sys
import os
import json
from datetime import datetime
import xgboost as xgb
import pandas as pd

# Add parent directory to path to import feature extractor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'DNS'))
from enhanced_dns_features import EnhancedDNSFeatureExtractor


class DNSBlockerServer:
    def __init__(self, model_path, feature_names_path, upstream_dns='8.8.8.8', port=53, threshold=0.5):
        """
        Initialize DNS blocker server

        Args:
            model_path: Path to XGBoost model file (.ubj)
            feature_names_path: Path to feature names JSON
            upstream_dns: Upstream DNS server for legitimate queries (default: Google DNS)
            port: Port to listen on (default: 53)
            threshold: Classification threshold (default: 0.5)
        """
        self.port = port
        self.upstream_dns = upstream_dns
        self.upstream_port = 53
        self.threshold = threshold

        # Statistics
        self.stats = {
            'total_queries': 0,
            'blocked': 0,
            'allowed': 0,
            'errors': 0
        }

        print(f"[INIT] Loading DNS Ad Blocker Server...")
        print(f"[INIT] Upstream DNS: {upstream_dns}")
        print(f"[INIT] Listening port: {port}")
        print(f"[INIT] Block threshold: {threshold}")

        # Load model
        print(f"[INIT] Loading model from {model_path}...")
        self.model = xgb.Booster()
        self.model.load_model(model_path)
        print(f"[INIT] Model loaded successfully")

        # Load feature names
        print(f"[INIT] Loading feature names from {feature_names_path}...")
        with open(feature_names_path, 'r') as f:
            self.feature_names = json.load(f)
        print(f"[INIT] {len(self.feature_names)} features loaded")

        # Initialize feature extractor
        self.extractor = EnhancedDNSFeatureExtractor()
        print(f"[INIT] Feature extractor initialized")

        # Create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"[INIT] Server initialized successfully!\n")

    def start(self):
        """Start the DNS server"""
        try:
            self.sock.bind(('127.0.0.1', self.port))
            print(f"{'='*70}")
            print(f"  DNS AD BLOCKER SERVER RUNNING")
            print(f"{'='*70}")
            print(f"  Listening on: 127.0.0.1:{self.port}")
            print(f"  Upstream DNS: {self.upstream_dns}")
            print(f"  Model: XGBoost with {len(self.feature_names)} features")
            print(f"  Status: ACTIVE - Intercepting DNS queries...")
            print(f"{'='*70}\n")

            while True:
                try:
                    data, addr = self.sock.recvfrom(512)
                    self.handle_query(data, addr)
                except KeyboardInterrupt:
                    print("\n\n[SHUTDOWN] Received interrupt signal")
                    break
                except Exception as e:
                    self.stats['errors'] += 1
                    print(f"[ERROR] {e}")

        finally:
            self.print_stats()
            self.sock.close()
            print("[SHUTDOWN] DNS server stopped")

    def handle_query(self, data, addr):
        """Handle incoming DNS query"""
        self.stats['total_queries'] += 1

        try:
            # Parse DNS query
            domain = self.parse_dns_query(data)

            if not domain:
                # Invalid query, forward it
                self.forward_query(data, addr)
                return

            # Extract features
            features = self.extractor.extract_features(domain)
            features_df = pd.DataFrame([features])[self.feature_names].fillna(0)
            dmatrix = xgb.DMatrix(features_df)

            # Predict
            prediction = self.model.predict(dmatrix)[0]

            timestamp = datetime.now().strftime('%H:%M:%S')

            if prediction >= self.threshold:
                # BLOCK - Return 0.0.0.0
                self.stats['blocked'] += 1
                print(f"[{timestamp}] BLOCK {prediction:.3f} | {domain}")
                response = self.create_blocked_response(data)
                self.sock.sendto(response, addr)
            else:
                # ALLOW - Forward to upstream DNS
                self.stats['allowed'] += 1
                print(f"[{timestamp}] ALLOW {prediction:.3f} | {domain}")
                self.forward_query(data, addr)

        except Exception as e:
            self.stats['errors'] += 1
            print(f"[ERROR] Failed to process query: {e}")
            # On error, forward the query
            self.forward_query(data, addr)

    def parse_dns_query(self, data):
        """Extract domain name from DNS query"""
        try:
            # Skip DNS header (12 bytes)
            pos = 12
            domain_parts = []

            while pos < len(data):
                length = data[pos]
                if length == 0:
                    break
                pos += 1
                domain_parts.append(data[pos:pos+length].decode('utf-8'))
                pos += length

            domain = '.'.join(domain_parts)
            return domain.lower() if domain else None

        except Exception as e:
            return None

    def create_blocked_response(self, query_data):
        """Create DNS response with 0.0.0.0 (blocked)"""
        try:
            # DNS Header - copy transaction ID and set response flags
            transaction_id = query_data[0:2]
            flags = b'\x81\x80'  # Standard query response, no error
            questions = b'\x00\x01'  # 1 question
            answer_rrs = b'\x00\x01'  # 1 answer
            authority_rrs = b'\x00\x00'
            additional_rrs = b'\x00\x00'

            header = transaction_id + flags + questions + answer_rrs + authority_rrs + additional_rrs

            # Question section - copy from original query
            question_start = 12
            question_end = query_data.index(b'\x00', question_start) + 5  # Find null + type + class
            question = query_data[question_start:question_end]

            # Answer section - point to blocked IP (0.0.0.0)
            answer = (
                b'\xc0\x0c'  # Pointer to domain name in question
                b'\x00\x01'  # Type A
                b'\x00\x01'  # Class IN
                b'\x00\x00\x00\x3c'  # TTL (60 seconds)
                b'\x00\x04'  # Data length (4 bytes for IPv4)
                b'\x00\x00\x00\x00'  # IP: 0.0.0.0 (blocked)
            )

            return header + question + answer

        except Exception as e:
            # If response creation fails, return minimal response
            return query_data[:2] + b'\x81\x80' + query_data[4:6] + b'\x00\x00\x00\x00\x00\x00' + query_data[12:]

    def forward_query(self, data, client_addr):
        """Forward query to upstream DNS server"""
        try:
            # Create new socket for upstream query
            upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            upstream_sock.settimeout(5)  # 5 second timeout

            # Send to upstream DNS
            upstream_sock.sendto(data, (self.upstream_dns, self.upstream_port))

            # Receive response
            response, _ = upstream_sock.recvfrom(512)

            # Send response back to client
            self.sock.sendto(response, client_addr)

            upstream_sock.close()

        except socket.timeout:
            print(f"[WARN] Upstream DNS timeout")
        except Exception as e:
            print(f"[ERROR] Forward failed: {e}")

    def print_stats(self):
        """Print server statistics"""
        print(f"\n{'='*70}")
        print(f"  DNS BLOCKER STATISTICS")
        print(f"{'='*70}")
        print(f"  Total queries:   {self.stats['total_queries']:,}")
        print(f"  Blocked (ads):   {self.stats['blocked']:,} ({self.stats['blocked']/max(self.stats['total_queries'],1)*100:.1f}%)")
        print(f"  Allowed (legit): {self.stats['allowed']:,} ({self.stats['allowed']/max(self.stats['total_queries'],1)*100:.1f}%)")
        print(f"  Errors:          {self.stats['errors']:,}")
        print(f"{'='*70}\n")


def main():
    """Main entry point"""
    # Paths (relative to script location)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, '..', 'DNS', 'DNSadblocker_model.ubj')
    feature_names_path = os.path.join(script_dir, '..', 'FeatureNames.json')

    # Check if files exist
    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found: {model_path}")
        sys.exit(1)

    if not os.path.exists(feature_names_path):
        print(f"[ERROR] Feature names file not found: {feature_names_path}")
        sys.exit(1)

    # Configuration
    UPSTREAM_DNS = '8.8.8.8'  # Google DNS (change to 1.1.1.1 for Cloudflare)
    PORT = 53  # DNS port (requires root/sudo)
    THRESHOLD = 0.95  # Classification threshold for new balanced model

    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                   DNS AD BLOCKER SERVER                           ║
║                   Machine Learning Powered                        ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    # Note about permissions
    if PORT == 53:
        print("[NOTE] Port 53 requires root privileges. Run with sudo:")
        print("       sudo python3 dns_blocker_server.py\n")
    else:
        print(f"[NOTE] Running on port {PORT} (testing mode)")
        print(f"       To use system-wide, you need to run on port 53 with sudo\n")

    # Create and start server
    try:
        server = DNSBlockerServer(
            model_path=model_path,
            feature_names_path=feature_names_path,
            upstream_dns=UPSTREAM_DNS,
            port=PORT,
            threshold=THRESHOLD
        )
        server.start()

    except PermissionError:
        print(f"\n[ERROR] Permission denied. Port {PORT} requires root privileges.")
        print(f"[ERROR] Run with: sudo python3 {sys.argv[0]}")
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] Server failed to start: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
