#!/usr/bin/env python3


import re
import math
from collections import Counter
import tldextract
from dns_feature_extractor import DNSFeatureExtractor

class EnhancedDNSFeatureExtractor(DNSFeatureExtractor):
    """Extended feature extractor with additional advanced features"""

    def __init__(self):
        super().__init__()

        # Expanded keyword lists
        self.tracker_keywords = ['track', 'analytics', 'pixel', 'beacon', 'telemetry', 'stat', 'metric']
        self.cdn_keywords = ['cdn', 'static', 'media', 'asset', 'content', 'cache']
        self.suspicious_words = ['click', 'popup', 'banner', 'promo', 'offer', 'deal', 'win', 'prize']

        # Common legitimate patterns
        self.legit_patterns = ['api', 'www', 'mail', 'smtp', 'imap', 'ftp', 'docs', 'blog', 'wiki']

        # Known ad network substrings
        self.ad_networks = [
            'doubleclick', 'googlesyndication', 'googleadservices', 'adserver',
            'adsystem', 'serving-sys', 'criteo', 'outbrain', 'taboola',
            'pubmatic', 'smartadserver', 'rubiconproject', 'openx', 'yieldmanager'
        ]

    def extract_features(self, domain):
        # Get base features from parent class
        features = super().extract_features(domain)

        domain = domain.lower().strip().rstrip('.')
        ext = tldextract.extract(domain)
        subdomain = ext.subdomain
        domain_name = ext.domain
        tld = ext.suffix


        # 1. Advanced Keyword Features
        features['tracker_keyword_count'] = sum(1 for kw in self.tracker_keywords if kw in domain)
        features['cdn_keyword_count'] = sum(1 for kw in self.cdn_keywords if kw in domain)
        features['suspicious_word_count'] = sum(1 for kw in self.suspicious_words if kw in domain)
        features['legit_pattern_count'] = sum(1 for kw in self.legit_patterns if kw in domain)

        # 2. Known Ad Network Detection
        features['matches_ad_network'] = 1 if any(net in domain for net in self.ad_networks) else 0

        # 3. Domain Name Length Ratios
        full_length = len(domain)
        features['subdomain_to_domain_ratio'] = len(subdomain) / full_length if full_length > 0 else 0
        features['domain_to_full_ratio'] = len(domain_name) / full_length if full_length > 0 else 0
        features['tld_to_full_ratio'] = len(tld) / full_length if full_length > 0 else 0

        # 4. Character Pattern Analysis
        features['uppercase_count'] = sum(1 for c in domain if c.isupper())
        features['special_char_count'] = sum(1 for c in domain if c in '!@#$%^&*()+=[]{}|;:,<>?')
        features['alphanumeric_ratio'] = sum(1 for c in domain if c.isalnum()) / len(domain) if len(domain) > 0 else 0

        # 5. Repetition Patterns (ads often have repeated chars)
        features['max_char_repetition'] = self._max_char_repetition(domain)
        features['has_repeated_bigram'] = self._has_repeated_ngram(domain, 2)
        features['has_repeated_trigram'] = self._has_repeated_ngram(domain, 3)

        # 6. Lexical Diversity
        features['lexical_diversity'] = len(set(domain)) / len(domain) if len(domain) > 0 else 0
        features['vowel_consonant_ratio'] = self._vowel_consonant_ratio(domain_name)

        # 7. Subdomain Analysis
        if subdomain:
            subdomains = subdomain.split('.')
            features['subdomain_levels'] = len(subdomains)
            features['avg_subdomain_length'] = sum(len(s) for s in subdomains) / len(subdomains)
            features['subdomain_has_number'] = 1 if any(c.isdigit() for c in subdomain) else 0
            features['subdomain_all_numeric'] = 1 if subdomain.replace('.', '').isdigit() else 0
        else:
            features['subdomain_levels'] = 0
            features['avg_subdomain_length'] = 0
            features['subdomain_has_number'] = 0
            features['subdomain_all_numeric'] = 0

        # 8. Domain Name Patterns
        features['domain_name_has_number'] = 1 if any(c.isdigit() for c in domain_name) else 0
        features['domain_name_starts_with_ad'] = 1 if domain_name.startswith(('ad', 'ads')) else 0
        features['domain_name_ends_with_ad'] = 1 if domain_name.endswith(('ad', 'ads')) else 0

        # 9. TLD Analysis
        features['tld_is_country_code'] = 1 if len(tld) == 2 and tld.isalpha() else 0
        features['tld_is_new_gtld'] = 1 if tld in ['xyz', 'top', 'wang', 'win', 'bid', 'loan', 'click'] else 0

        # 10. Heuristic Scores
        features['ad_heuristic_score'] = self._calculate_ad_heuristic(domain, subdomain, domain_name)
        features['randomness_score'] = self._calculate_randomness_score(domain_name)

        # 11. Position-based Features
        features['has_number_in_subdomain_start'] = 1 if subdomain and subdomain[0].isdigit() else 0
        features['has_hyphen_after_keyword'] = self._has_hyphen_after_keyword(domain)

        # 12. Length Variance
        if subdomain:
            parts = subdomain.split('.') + [domain_name]
            features['part_length_variance'] = self._variance([len(p) for p in parts])
        else:
            features['part_length_variance'] = 0

        # 13. Compound Word Detection
        features['looks_like_compound_word'] = self._is_compound_word(domain_name)

        # 14. Numeric Pattern Features
        features['has_port_like_number'] = 1 if re.search(r'\b(80|443|8080|3000|5000)\b', domain) else 0
        features['has_year_like_number'] = 1 if re.search(r'\b(19|20)\d{2}\b', domain) else 0

        return features

    def _max_char_repetition(self, text):
        """Find maximum consecutive character repetition"""
        if not text:
            return 0
        max_rep = 1
        current_rep = 1
        for i in range(1, len(text)):
            if text[i] == text[i-1]:
                current_rep += 1
                max_rep = max(max_rep, current_rep)
            else:
                current_rep = 1
        return max_rep

    def _has_repeated_ngram(self, text, n):
        """Check if any n-gram appears more than once"""
        ngrams = [text[i:i+n] for i in range(len(text)-n+1)]
        return 1 if len(ngrams) != len(set(ngrams)) else 0

    def _vowel_consonant_ratio(self, text):
        """Calculate ratio of vowels to consonants"""
        if not text:
            return 0
        vowels = sum(1 for c in text.lower() if c in 'aeiou')
        consonants = sum(1 for c in text.lower() if c in 'bcdfghjklmnpqrstvwxyz')
        return vowels / consonants if consonants > 0 else 0

    def _calculate_ad_heuristic(self, domain, subdomain, domain_name):
        """Heuristic score combining multiple ad indicators"""
        score = 0

        # Keyword presence
        if any(kw in domain for kw in self.ad_keywords):
            score += 3

        # Number patterns
        if re.search(r'\d{3,}', domain):
            score += 1

        # Multiple hyphens
        if domain.count('-') >= 2:
            score += 2

        # Subdomain depth
        if subdomain and subdomain.count('.') >= 2:
            score += 1

        # Short domain with numbers
        if len(domain_name) < 5 and any(c.isdigit() for c in domain_name):
            score += 2

        return score

    def _calculate_randomness_score(self, text):
        """Calculate how random/generated the text looks"""
        if not text or len(text) < 3:
            return 0

        score = 0

        # High entropy
        entropy = self._calculate_entropy(text)
        if entropy > 3.5:
            score += 2

        # High consonant ratio
        consonant_ratio = self._consonant_ratio(text)
        if consonant_ratio > 0.7:
            score += 2

        # Low vowel ratio
        vowel_ratio = self._vowel_ratio(text)
        if vowel_ratio < 0.15:
            score += 2

        # Alternating letter-number pattern
        if re.search(r'([a-z]\d){2,}', text):
            score += 3

        return score

    def _has_hyphen_after_keyword(self, domain):
        """Check if hyphen appears after ad keywords"""
        for kw in self.ad_keywords:
            if f'{kw}-' in domain or f'-{kw}' in domain:
                return 1
        return 0

    def _variance(self, numbers):
        """Calculate variance of a list of numbers"""
        if not numbers:
            return 0
        mean = sum(numbers) / len(numbers)
        return sum((x - mean) ** 2 for x in numbers) / len(numbers)

    def _is_compound_word(self, text):
        """Check if domain looks like compound word (camelCase or concatenated)"""
        # Check for camelCase
        if re.search(r'[a-z][A-Z]', text):
            return 1

        # Check for very long words (likely concatenated)
        if len(text) > 15 and text.isalpha():
            return 1

        return 0


# Testing
if __name__ == "__main__":
    extractor = EnhancedDNSFeatureExtractor()

    test_domains = [
        'googleads.g.doubleclick.net',
        'www.google.com',
        'track123.ad-server.xyz',
        'api.github.com'
    ]

    for domain in test_domains:
        features = extractor.extract_features(domain)
        print(f"\n{domain}:")
        print(f"  Total features: {len(features)}")
        print(f"  Ad heuristic score: {features['ad_heuristic_score']}")
        print(f"  Randomness score: {features['randomness_score']}")
        print(f"  Matches ad network: {features['matches_ad_network']}")
