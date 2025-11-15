#!/usr/bin/env python3
"""
Generate Balanced DNS Training Dataset
Fixes the www subdomain bias by adding more legitimate www domains
"""

import pandas as pd
import requests
from tqdm import tqdm

print("="*70)
print("  BALANCED DNS TRAINING DATA GENERATOR")
print("="*70)
print()

# Load original data
print("[1/4] Loading original training data...")
original_df = pd.read_csv('../Data/dns_training_data.csv')
print(f"      Original: {len(original_df):,} domains")
print(f"      Ads: {(original_df['label']==1).sum():,}")
print(f"      Legitimate: {(original_df['label']==0).sum():,}")

# Analyze www distribution
legit_www = original_df[(original_df['label']==0) & (original_df['domain'].str.startswith('www.'))]
ads_www = original_df[(original_df['label']==1) & (original_df['domain'].str.startswith('www.'))]
print(f"\n      Current www distribution:")
print(f"        Legitimate www: {len(legit_www)} ({len(legit_www)/(original_df['label']==0).sum()*100:.1f}%)")
print(f"        Ads www: {len(ads_www)} ({len(ads_www)/(original_df['label']==1).sum()*100:.1f}%)")
print()

# Popular legitimate www domains to add
print("[2/4] Adding popular legitimate www domains...")
legitimate_www_domains = [
    # Top websites
    'www.google.com', 'www.youtube.com', 'www.facebook.com', 'www.amazon.com',
    'www.wikipedia.org', 'www.twitter.com', 'www.instagram.com', 'www.linkedin.com',
    'www.reddit.com', 'www.netflix.com', 'www.twitch.tv', 'www.stackoverflow.com',

    # News sites
    'www.cnn.com', 'www.bbc.com', 'www.nytimes.com', 'www.theguardian.com',
    'www.washingtonpost.com', 'www.reuters.com', 'www.nbcnews.com', 'www.foxnews.com',
    'www.usatoday.com', 'www.wsj.com', 'www.bloomberg.com', 'www.forbes.com',

    # Tech sites
    'www.github.com', 'www.microsoft.com', 'www.apple.com', 'www.adobe.com',
    'www.nvidia.com', 'www.intel.com', 'www.amd.com', 'www.dell.com',

    # E-commerce
    'www.ebay.com', 'www.walmart.com', 'www.target.com', 'www.bestbuy.com',
    'www.etsy.com', 'www.aliexpress.com', 'www.shopify.com',

    # Education
    'www.mit.edu', 'www.stanford.edu', 'www.harvard.edu', 'www.berkeley.edu',
    'www.coursera.org', 'www.udemy.com', 'www.khanacademy.org',

    # Government
    'www.gov.uk', 'www.usa.gov', 'www.whitehouse.gov', 'www.nih.gov',
    'www.nasa.gov', 'www.cdc.gov',

    # Entertainment
    'www.spotify.com', 'www.soundcloud.com', 'www.imdb.com', 'www.rottentomatoes.com',
    'www.hulu.com', 'www.disneyplus.com', 'www.hbo.com',

    # Social/Communication
    'www.discord.com', 'www.slack.com', 'www.zoom.us', 'www.dropbox.com',
    'www.gmail.com', 'www.outlook.com', 'www.yahoo.com',

    # Sports
    'www.espn.com', 'www.nba.com', 'www.nfl.com', 'www.mlb.com',
    'www.nhl.com', 'www.fifa.com',

    # Finance
    'www.paypal.com', 'www.chase.com', 'www.wellsfargo.com', 'www.bankofamerica.com',

    # Travel
    'www.expedia.com', 'www.booking.com', 'www.airbnb.com', 'www.tripadvisor.com',

    # Health
    'www.webmd.com', 'www.mayoclinic.org', 'www.healthline.com',

    # Gaming
    'www.steam.com', 'www.epicgames.com', 'www.ea.com', 'www.rockstargames.com',
    'www.minecraft.net', 'www.roblox.com',

    # Other popular
    'www.medium.com', 'www.quora.com', 'www.pinterest.com', 'www.tumblr.com',
    'www.yelp.com', 'www.craigslist.org', 'www.weather.com',
]

# Add variations with api, cdn, static subdomains for legitimate sites
legitimate_subdomain_variations = []
popular_domains = [
    'google.com', 'facebook.com', 'microsoft.com', 'amazon.com', 'github.com',
    'cloudflare.com', 'apple.com', 'adobe.com', 'netflix.com', 'spotify.com'
]

for domain in popular_domains:
    legitimate_subdomain_variations.extend([
        f'api.{domain}',
        f'cdn.{domain}',
        f'static.{domain}',
        f'images.{domain}',
        f'assets.{domain}',
        f'media.{domain}',
        f'developers.{domain}',
        f'docs.{domain}',
        f'blog.{domain}',
        f'help.{domain}',
        f'support.{domain}',
        f'status.{domain}',
    ])

all_new_legitimate = legitimate_www_domains + legitimate_subdomain_variations
print(f"      Adding {len(all_new_legitimate)} legitimate domains with subdomains")

# Create new legitimate entries
new_legitimate = pd.DataFrame({
    'domain': all_new_legitimate,
    'label': 0
})

print()
print("[3/4] Combining datasets...")
# Combine original data with new legitimate domains
combined_df = pd.concat([original_df, new_legitimate], ignore_index=True)

# Remove duplicates (keep original if exists)
combined_df = combined_df.drop_duplicates(subset=['domain'], keep='first')

print(f"      Total domains after adding: {len(combined_df):,}")
print(f"      Ads: {(combined_df['label']==1).sum():,}")
print(f"      Legitimate: {(combined_df['label']==0).sum():,}")

# Check new www distribution
new_legit_www = combined_df[(combined_df['label']==0) & (combined_df['domain'].str.startswith('www.'))]
new_ads_www = combined_df[(combined_df['label']==1) & (combined_df['domain'].str.startswith('www.'))]
print(f"\n      New www distribution:")
print(f"        Legitimate www: {len(new_legit_www)} ({len(new_legit_www)/(combined_df['label']==0).sum()*100:.1f}%)")
print(f"        Ads www: {len(new_ads_www)} ({len(new_ads_www)/(combined_df['label']==1).sum()*100:.1f}%)")

# Shuffle the dataset
combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)

print()
print("[4/4] Saving balanced training data...")
output_file = 'dns_training_data_balanced.csv'
combined_df.to_csv(output_file, index=False)

import os
file_size = os.path.getsize(output_file) / (1024 * 1024)
print(f"      Saved to: {output_file}")
print(f"      File size: {file_size:.1f} MB")
print()

print("="*70)
print("  BALANCED DATASET CREATED!")
print("="*70)
print()
print("Summary:")
print(f"  - Total domains: {len(combined_df):,}")
print(f"  - Legitimate: {(combined_df['label']==0).sum():,}")
print(f"  - Ads: {(combined_df['label']==1).sum():,}")
print(f"  - Legitimate www domains: {len(new_legit_www)} (improved from {len(legit_www)})")
print()
print("Next step: Upload 'dns_training_data_balanced.csv' to Google Colab")
print("            Use DNS/train_dns_adblocker.ipynb as template for training")
