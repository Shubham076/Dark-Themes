#!/usr/bin/env python3
"""
Script to add ToolWindow button hover properties to all light themes.
Uses each theme's hover or selectionBackground color.
"""

import json
import os
from pathlib import Path

def get_hover_color(theme_data):
    """Extract the hover or selection color from theme."""
    # Check colors section first
    if 'colors' in theme_data:
        if 'hover' in theme_data['colors']:
            return theme_data['colors']['hover']
        if 'selectionBackground' in theme_data['colors']:
            return theme_data['colors']['selectionBackground']
    
    # Check ui section
    if 'ui' in theme_data:
        if 'ActionButton' in theme_data['ui'] and 'hoverBackground' in theme_data['ui']['ActionButton']:
            return theme_data['ui']['ActionButton']['hoverBackground']
        if 'EditorTabs' in theme_data['ui'] and 'hoverBackground' in theme_data['ui']['EditorTabs']:
            return theme_data['ui']['EditorTabs']['hoverBackground']
    
    # Default to a subtle hover color
    return "#00000012"  # 7% black overlay

def fix_toolwindow_hover(filepath):
    """Add ToolWindow hover properties to theme if missing."""
    with open(filepath, 'r', encoding='utf-8') as f:
        theme = json.load(f)
    
    theme_name = theme.get('name', filepath.stem)
    
    # Skip dark themes
    if theme.get('dark', False):
        print(f"  Skipping {theme_name} (dark theme)")
        return False
    
    # Get hover color
    hover_color = get_hover_color(theme)
    
    # Check if ToolWindow exists
    if 'ui' not in theme:
        theme['ui'] = {}
    
    if 'ToolWindow' not in theme['ui']:
        theme['ui']['ToolWindow'] = {}
    
    tool_window = theme['ui']['ToolWindow']
    modified = False
    
    # Add HeaderTab if missing
    if 'HeaderTab' not in tool_window:
        tool_window['HeaderTab'] = {}
        modified = True
    
    # Add hover properties if missing
    header_tab = tool_window['HeaderTab']
    if 'hoverBackground' not in header_tab:
        header_tab['hoverBackground'] = hover_color
        modified = True
    if 'hoverInactiveBackground' not in header_tab:
        header_tab['hoverInactiveBackground'] = hover_color
        modified = True
    
    # Add Button hover if missing
    if 'Button' not in tool_window:
        tool_window['Button'] = {}
        modified = True
    
    if 'hoverBackground' not in tool_window['Button']:
        tool_window['Button']['hoverBackground'] = hover_color
        modified = True
    
    if modified:
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(theme, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ Updated {theme_name}: ToolWindow hover = {hover_color}")
        return True
    else:
        print(f"  ✓ {theme_name} already has ToolWindow hover properties")
        return False

def main():
    themes_dir = Path("src/main/resources/themes")
    
    if not themes_dir.exists():
        print(f"Error: themes directory not found at {themes_dir}")
        return
    
    light_themes = []
    fixed_count = 0
    
    print("Scanning for light themes...")
    
    # Find all light theme files
    for theme_file in sorted(themes_dir.glob("*.theme.json")):
        with open(theme_file, 'r', encoding='utf-8') as f:
            try:
                theme = json.load(f)
                if not theme.get('dark', False):
                    light_themes.append(theme_file)
            except json.JSONDecodeError:
                print(f"  ⚠️  Error reading {theme_file.name}")
    
    print(f"\nFound {len(light_themes)} light themes\n")
    print("Updating ToolWindow hover properties...")
    
    for theme_file in light_themes:
        if fix_toolwindow_hover(theme_file):
            fixed_count += 1
    
    print(f"\n{'='*50}")
    print(f"Summary: Updated {fixed_count} light themes")
    print(f"Total light themes: {len(light_themes)}")
    
    print("\nProperties added:")
    print("  ToolWindow.HeaderTab.hoverBackground")
    print("  ToolWindow.HeaderTab.hoverInactiveBackground") 
    print("  ToolWindow.Button.hoverBackground")

if __name__ == "__main__":
    main()
