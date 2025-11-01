#!/usr/bin/env python3
"""
Script to run update_light_themes.py for all dark themes.
Identifies dark themes by checking the "dark" property in theme.json files.
"""

import json
import subprocess
import sys
from pathlib import Path


def is_dark_theme(theme_json_path):
    """Check if a theme is a dark theme by reading its JSON file."""
    try:
        with open(theme_json_path, 'r', encoding='utf-8') as f:
            theme_data = json.load(f)
            return theme_data.get('dark', False)
    except Exception as e:
        print(f"Error reading {theme_json_path}: {e}")
        return False


def get_theme_pairs():
    """Get all dark theme pairs (theme_name, xml_name)."""
    themes_dir = Path(__file__).parent / 'src' / 'main' / 'resources' / 'themes'
    
    dark_themes = []
    
    # Get all .theme.json files
    for json_file in themes_dir.glob('*.theme.json'):
        if is_dark_theme(json_file):
            theme_name = json_file.stem.replace('.theme', '')
            
            # Check if corresponding XML exists
            xml_file = themes_dir / f'{theme_name}.xml'
            if xml_file.exists():
                dark_themes.append((theme_name, theme_name))
                print(f"Found dark theme: {theme_name}")
            else:
                print(f"⚠️  Dark theme {theme_name} has no corresponding XML file")
    
    return dark_themes


def main():
    print("🔍 Scanning for dark themes...")
    
    dark_themes = get_theme_pairs()
    
    if not dark_themes:
        print("❌ No dark themes found!")
        sys.exit(1)
    
    print(f"\n📋 Found {len(dark_themes)} dark themes to update:")
    for theme_name, xml_name in dark_themes:
        print(f"  - {theme_name}")
    
    print(f"\n🚀 Starting updates...")
    
    success_count = 0
    failed_themes = []
    
    for i, (theme_name, xml_name) in enumerate(dark_themes, 1):
        print(f"\n[{i}/{len(dark_themes)}] Updating {theme_name}...")
        
        try:
            # Run the update script
            result = subprocess.run([
                sys.executable, 'update_light_themes.py', theme_name, xml_name
            ], capture_output=True, text=True, cwd=Path(__file__).parent)
            
            if result.returncode == 0:
                print(f"✅ {theme_name} updated successfully")
                success_count += 1
            else:
                print(f"❌ {theme_name} failed:")
                print(f"   stdout: {result.stdout}")
                print(f"   stderr: {result.stderr}")
                failed_themes.append(theme_name)
                
        except Exception as e:
            print(f"❌ {theme_name} failed with exception: {e}")
            failed_themes.append(theme_name)
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Successfully updated: {success_count}/{len(dark_themes)}")
    print(f"  ❌ Failed: {len(failed_themes)}")
    
    if failed_themes:
        print(f"\n❌ Failed themes:")
        for theme in failed_themes:
            print(f"  - {theme}")
        sys.exit(1)
    else:
        print(f"\n🎉 All dark themes updated successfully!")


if __name__ == '__main__':
    main()
