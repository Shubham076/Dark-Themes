#!/usr/bin/env python3
"""
Script to update light theme.json files with Islands, MainWindow, and EditorTabs sections.
Extracts colors from corresponding XML files.
"""

import json
import re
import sys
from pathlib import Path


def extract_color_from_xml(xml_file, color_key):
    """Extract a color value from XML file."""
    try:
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Match: <option name="COLOR_KEY" value="HEXVALUE" />
            pattern = f'<option name="{color_key}" value="([^"]+)"'
            match = re.search(pattern, content)
            if match:
                color = match.group(1).strip()
                # Ensure it starts with #
                if not color.startswith('#'):
                    color = f'#{color}'
                return color.upper()
    except Exception as e:
        print(f"Error reading {xml_file}: {e}")
    return None


def get_xml_colors(xml_path):
    """Extract required colors from XML file."""
    colors = {}
    
    # Try CONSOLE_BACKGROUND_KEY first, fall back to GUTTER_BACKGROUND
    console_bg = extract_color_from_xml(xml_path, 'CONSOLE_BACKGROUND_KEY')
    if not console_bg or console_bg == '#':
        console_bg = extract_color_from_xml(xml_path, 'GUTTER_BACKGROUND')
    colors['console_background'] = console_bg
    
    colors['selection_background'] = extract_color_from_xml(xml_path, 'SELECTION_BACKGROUND')
    colors['caret_row_color'] = extract_color_from_xml(xml_path, 'CARET_ROW_COLOR')
    
    return colors


def update_theme_json(theme_json_path, xml_path):
    """Update a theme.json file with Islands, MainWindow, and EditorTabs sections."""
    
    # Extract colors from XML
    colors = get_xml_colors(xml_path)
    
    if not colors['console_background']:
        print(f"⚠️  Could not extract CONSOLE_BACKGROUND_KEY from {xml_path}")
        return False
    
    print(f"  Colors extracted:")
    print(f"    Console BG: {colors['console_background']}")
    print(f"    Selection BG: {colors['selection_background']}")
    print(f"    Caret Row: {colors['caret_row_color']}")
    
    # Load theme.json
    with open(theme_json_path, 'r', encoding='utf-8') as f:
        theme_data = json.load(f)
    
    # Add color variables section - remove old variable names if they exist
    if 'colors' not in theme_data:
        theme_data['colors'] = {}
    # Remove old variable names
    theme_data['colors'].pop('ConsoleBackground', None)
    theme_data['colors'].pop('CaretRowColor', None)
    theme_data['colors'].pop('SelectionBackground', None)
    # Add new simplified variable names
    theme_data['colors']['background'] = colors['console_background']
    theme_data['colors']['selectionBackground'] = colors['selection_background']
    theme_data['colors']['hover'] = colors['caret_row_color']
    
    # 1. Update "*" background
    if '*' in theme_data.get('ui', {}):
        theme_data['ui']['*']['background'] = 'background'
    
    # 2. Add Islands and Island sections (after "*" section)
    ui_dict = theme_data.get('ui', {})
    
    # Create new ordered dict with Islands after "*"
    new_ui = {}
    for key, value in ui_dict.items():
        # Skip old Islands/Island/MainWindow.background/Terminal/ActionButton as we'll add them fresh
        if key in ['Islands', 'Island', 'MainWindow.background', 'Terminal', 'ActionButton']:
            continue
        new_ui[key] = value
        if key == '*':
            # Add Islands sections right after "*"
            new_ui['Islands'] = 1
            new_ui['Island'] = {
                "arc": 20,
                "borderWidth": 4,
                "borderColor": 'background',
                "inactiveAlpha": 0.44,
                "inactiveAlphaInStatusBar": {
                    "os.mac": 0.2,
                    "os.windows": 0.2,
                    "os.linux": 0.15
                }
            }
            new_ui['MainWindow.background'] = 'selectionBackground'
    
    # 3. Update/Add DefaultTabs
    new_ui['DefaultTabs'] = {
        "background": 'background',
        "borderColor": 'background'
    }
    
    # Keep other sections that come after DefaultTabs but before EditorTabs
    for key, value in ui_dict.items():
        if key not in new_ui and key not in ['DefaultTabs', 'EditorTabs', 'ActionButton', 'Terminal']:
            new_ui[key] = value
    
    # 4. Update/Add EditorTabs with full structure
    new_ui['EditorTabs'] = {
        "background": 'background',
        "underTabsBorderColor": 'background',
        "underlinedTabBackground": 'selectionBackground',
        "underlinedBorderColor": 'selectionBackground',
        "inactiveUnderlinedTabBackground": 'selectionBackground',
        "inactiveUnderlinedTabBorderColor": 'selectionBackground',
        "hoverBackground": 'hover',
        "tabInsets": "-6,8,-6,8",
        "tabInsets.compact": "-2,6,-2,4",
        "tabContentActionsRightInsets": "0,2,0,2"
    }
    
    # Add remaining sections after EditorTabs (except ActionButton, Terminal which we add later)
    for key, value in ui_dict.items():
        if key in ['EditorTabs', 'ActionButton', 'Terminal']:
            continue
        if key not in new_ui:
            new_ui[key] = value
    
    # 5. Add ActionButton section - use same border color for hover and pressed
    new_ui['ActionButton'] = {
        "hoverBackground": 'hover',
        "hoverBorderColor": 'background',
        "pressedBackground": 'background',
        "pressedBorderColor": 'background'
    }
    
    # 6. Update ToolWindow to fix terminal tab bar color
    if 'ToolWindow' not in new_ui:
        new_ui['ToolWindow'] = {}
    new_ui['ToolWindow']['background'] = 'background'
    
    if 'Header' not in new_ui.get('ToolWindow', {}):
        new_ui['ToolWindow']['Header'] = {}
    new_ui['ToolWindow']['Header']['background'] = 'background'
    new_ui['ToolWindow']['Header']['inactiveBackground'] = 'background'
    
    theme_data['ui'] = new_ui
    
    # Reorder theme_data to have colors before ui (like test.theme.json)
    ordered_data = {}
    # First add metadata
    for key in ['name', 'author', 'dark', 'editorScheme', 'parentTheme']:
        if key in theme_data:
            ordered_data[key] = theme_data[key]
    # Then colors
    if 'colors' in theme_data:
        ordered_data['colors'] = theme_data['colors']
    # Then ui
    ordered_data['ui'] = theme_data['ui']
    # Then any other sections
    for key, value in theme_data.items():
        if key not in ordered_data:
            ordered_data[key] = value
    
    # Save updated theme.json with proper formatting
    with open(theme_json_path, 'w', encoding='utf-8') as f:
        json_str = json.dumps(ordered_data, indent=2, ensure_ascii=False)
        # Add blank lines in EditorTabs for readability
        json_str = json_str.replace(
            ',\n      "underlinedTabBackground"',
            ',\n\n      "underlinedTabBackground"'
        )
        json_str = json_str.replace(
            ',\n      "inactiveUnderlinedTabBackground"',
            ',\n\n      "inactiveUnderlinedTabBackground"'
        )
        json_str = json_str.replace(
            ',\n      "hoverBackground"',
            ',\n\n      "hoverBackground"'
        )
        json_str = json_str.replace(
            ',\n      "tabInsets"',
            ',\n\n      "tabInsets"'
        )
        f.write(json_str)
    
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_light_themes.py <theme_name> [xml_name]")
        print("Example: python update_light_themes.py autumn")
        print("Example: python update_light_themes.py bracketsLightPro brackets")
        sys.exit(1)
    
    theme_name = sys.argv[1]
    xml_name = sys.argv[2] if len(sys.argv) > 2 else theme_name
    
    themes_dir = Path(__file__).parent / 'src' / 'main' / 'resources' / 'themes'
    
    theme_json_path = themes_dir / f'{theme_name}.theme.json'
    xml_path = themes_dir / f'{xml_name}.xml'
    
    if not theme_json_path.exists():
        print(f"❌ Theme JSON not found: {theme_json_path}")
        sys.exit(1)
    
    if not xml_path.exists():
        print(f"❌ XML file not found: {xml_path}")
        sys.exit(1)
    
    print(f"🔧 Updating {theme_name}...")
    
    if update_theme_json(theme_json_path, xml_path):
        print(f"✅ Successfully updated {theme_json_path}")
    else:
        print(f"❌ Failed to update {theme_json_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
