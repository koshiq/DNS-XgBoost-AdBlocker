#!/usr/bin/env python3
"""
DNS-Level Feature Extraction for Ad Detection
Extracts features from domain names that can be used for ML classification
"""

import re
import math
from collections import Counter
import tldextract

class DNSFeatureExtractor:
    """Extract features from DNS queries for ad detection"""

    def __init__(self):
        # Known ad-related keywords
        self.ad_keywords = [
            'ad', 'ads', 'advert', 'adserver', 'adsystem', 'adservice',
            'banner', 'click', 'tracker', 'track', 'analytic', 'analytics',
            'pixel', 'tag', 'doubleclick', 'googlead', 'pagead', 'sponsor',
            'popup', 'pop', 'promo', 'marketing', 'affiliate', 'impression',
            'beacon', 'telemetry', 'stats', 'metric', 'count', 'event'
        ]

        # Suspicious TLDs commonly used by ads
        self.suspicious_tlds = {
            'xyz', 'top', 'win', 'bid', 'gdn', 'loan', 'click', 'online',
            'work', 'gq', 'ml', 'cf', 'tk', 'ga', 'buzz', 'stream'
        }

    def extract_features(self, domain):
        """
        Extract all features from a domain name
        Returns dict of features suitable for ML model
        """
        domain = domain.lower().strip().rstrip('.')

        # Parse domain into components
        ext = tldextract.extract(domain)
        subdomain = ext.subdomain
        domain_name = ext.domain
        tld = ext.suffix

        features = {}

        # === 1. LENGTH FEATURES ===
        features['domain_length'] = len(domain)
        features['domain_name_length'] = len(domain_name)
        features['subdomain_length'] = len(subdomain)
        features['subdomain_count'] = subdomain.count('.') + (1 if subdomain else 0)
        features['path_depth'] = domain.count('.')

        # === 2. CHARACTER DISTRIBUTION FEATURES ===
        features['digit_count'] = sum(c.isdigit() for c in domain)
        features['digit_ratio'] = features['digit_count'] / len(domain) if len(domain) > 0 else 0

        features['hyphen_count'] = domain.count('-')
        features['hyphen_ratio'] = features['hyphen_count'] / len(domain) if len(domain) > 0 else 0

        features['underscore_count'] = domain.count('_')
        features['consonant_ratio'] = self._consonant_ratio(domain_name)
        features['vowel_ratio'] = self._vowel_ratio(domain_name)

        # === 3. ENTROPY FEATURES ===
        features['entropy'] = self._calculate_entropy(domain)
        features['domain_name_entropy'] = self._calculate_entropy(domain_name)
        features['subdomain_entropy'] = self._calculate_entropy(subdomain) if subdomain else 0

        # === 4. KEYWORD FEATURES ===
        features['ad_keyword_count'] = self._count_ad_keywords(domain)
        features['has_ad_keyword'] = 1 if features['ad_keyword_count'] > 0 else 0

        # Keyword with special character boundary (more precise)
        features['keyword_with_boundary'] = self._keyword_with_boundary(domain)

        # === 5. N-GRAM FEATURES ===
        # Common ad-related bigrams and trigrams
        features['has_ad_bigram'] = self._has_ad_ngram(domain, 2)
        features['has_ad_trigram'] = self._has_ad_ngram(domain, 3)

        # === 6. TLD FEATURES ===
        features['tld_suspicious'] = 1 if tld in self.suspicious_tlds else 0
        features['tld_length'] = len(tld)
        features['is_commercial_tld'] = 1 if tld in ['com', 'net', 'biz'] else 0

        # === 7. PATTERN FEATURES ===
        features['has_multiple_hyphens'] = 1 if domain.count('-') >= 3 else 0
        features['has_number_sequence'] = 1 if re.search(r'\d{3,}', domain) else 0
        features['starts_with_number'] = 1 if (domain_name and domain_name[0].isdigit()) else 0

        # Random-looking patterns (e.g., cdn1234.example.com)
        features['has_random_pattern'] = self._detect_random_pattern(domain)

        # === 8. LEXICAL FEATURES ===
        features['max_consonant_sequence'] = self._max_consonant_sequence(domain_name)
        features['max_digit_sequence'] = len(max(re.findall(r'\d+', domain), key=len, default=''))

        # Ratio of unique characters (randomness indicator)
        features['unique_char_ratio'] = len(set(domain)) / len(domain) if len(domain) > 0 else 0

        # === 9. COMMON AD PATTERNS ===
        # CDN-like patterns (cdn123, static123, etc.)
        features['has_cdn_pattern'] = 1 if re.search(r'(cdn|static|media|asset)\d+', domain) else 0

        # Tracking/analytics patterns
        features['has_tracking_pattern'] = 1 if re.search(r'(track|analytic|pixel|tag|beacon)\w*\d*', domain) else 0

        # Geographic/network identifiers common in ad networks
        features['has_geo_identifier'] = 1 if re.search(r'(us|eu|asia|cdn)\d*[.-]', domain) else 0

        # === 10. STRUCTURAL FEATURES ===
        # Check if subdomain looks auto-generated (e.g., a1b2c3.example.com)
        features['subdomain_looks_random'] = self._looks_random(subdomain) if subdomain else 0

        # Check for multiple numeric segments
        features['numeric_segments'] = len(re.findall(r'\d+', domain))

        return features

    def _consonant_ratio(self, text):
        """Calculate ratio of consonants"""
        if not text:
            return 0
        consonants = sum(1 for c in text.lower() if c in 'bcdfghjklmnpqrstvwxyz')
        return consonants / len(text)

    def _vowel_ratio(self, text):
        """Calculate ratio of vowels"""
        if not text:
            return 0
        vowels = sum(1 for c in text.lower() if c in 'aeiou')
        return vowels / len(text)

    def _calculate_entropy(self, text):
        """Calculate Shannon entropy"""
        if not text:
            return 0
        counts = Counter(text)
        probs = [count / len(text) for count in counts.values()]
        return -sum(p * math.log2(p) for p in probs)

    def _count_ad_keywords(self, domain):
        """Count number of ad-related keywords present"""
        count = 0
        for keyword in self.ad_keywords:
            if keyword in domain:
                count += 1
        return count

    def _keyword_with_boundary(self, domain):
        """Check if ad keyword appears with special character boundary"""
        boundaries = r'[-_./]'
        for keyword in self.ad_keywords:
            pattern = f'{boundaries}{keyword}{boundaries}|^{keyword}{boundaries}|{boundaries}{keyword}$'
            if re.search(pattern, domain):
                return 1
        return 0

    def _has_ad_ngram(self, domain, n):
        """Check for common ad-related n-grams"""
        ad_ngrams = {
            2: ['ad', 'px', 'ds', 'bn', 'tr', 'tk'],  # bigrams
            3: ['ads', 'trk', 'tag', 'cdn', 'bid', 'clk']  # trigrams
        }

        if n not in ad_ngrams:
            return 0

        for i in range(len(domain) - n + 1):
            if domain[i:i+n] in ad_ngrams[n]:
                return 1
        return 0

    def _detect_random_pattern(self, domain):
        """Detect random-looking alphanumeric patterns"""
        # Patterns like: a1b2c3, x9y8z7, etc.
        if re.search(r'([a-z]\d){3,}', domain):
            return 1
        # Patterns like: xyz123abc, random456key
        if re.search(r'[a-z]{3,}\d{3,}[a-z]{3,}', domain):
            return 1
        return 0

    def _max_consonant_sequence(self, text):
        """Find longest sequence of consecutive consonants"""
        if not text:
            return 0
        sequences = re.findall(r'[bcdfghjklmnpqrstvwxyz]+', text.lower())
        return max([len(s) for s in sequences], default=0)

    def _looks_random(self, text):
        """Check if text looks randomly generated"""
        if not text or len(text) < 4:
            return 0

        # High entropy indicates randomness
        entropy = self._calculate_entropy(text)

        # High consonant ratio
        consonant_ratio = self._consonant_ratio(text)

        # Low vowel ratio
        vowel_ratio = self._vowel_ratio(text)

        # Heuristic: high entropy, high consonant, low vowel = likely random
        if entropy > 3.5 and consonant_ratio > 0.7 and vowel_ratio < 0.2:
            return 1

        return 0


# Example usage and testing
if __name__ == "__main__":
    extractor = DNSFeatureExtractor()

    # Test with example domains
    test_domains = [
        # Likely ads
        'googleads.g.doubleclick.net',
        'pagead2.googlesyndication.com',
        'static.ads-twitter.com',
        'cdn123.ad-server.net',
        'track.analytics-service.com',

        # Likely legitimate
        'www.google.com',
        'api.github.com',
        'cdn.jsdelivr.net',
        'www.wikipedia.org',
        'mail.yahoo.com'
    ]

    print("Feature Extraction Examples:\n")
    for domain in test_domains:
        features = extractor.extract_features(domain)
        print(f"\n{'='*60}")
        print(f"Domain: {domain}")
        print(f"{'='*60}")

        # Show most relevant features
        important_features = [
            'domain_length', 'subdomain_count', 'entropy',
            'ad_keyword_count', 'has_ad_keyword', 'keyword_with_boundary',
            'tld_suspicious', 'has_random_pattern', 'has_cdn_pattern',
            'has_tracking_pattern', 'digit_ratio', 'consonant_ratio'
        ]

        for feat in important_features:
            if feat in features:
                print(f"  {feat:25s}: {features[feat]:.3f}" if isinstance(features[feat], float) else f"  {feat:25s}: {features[feat]}")

    print("\n\nTotal features extracted:", len(features))
    print("Feature names:", list(features.keys()))
