"""
IntelliJ to Zed Theme Converter
Converts IntelliJ .icls theme files to Zed .json theme files
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse
import re
from typing import Dict, List, Any, Optional


class IntelliJToZedConverter:
    def __init__(self):
        # Map IntelliJ colors to Zed UI colors
        self.color_mapping = {
            # Editor colors - use TEXT attribute colors
            'TEXT.BACKGROUND': ['editor.background', 'editor.gutter.background', 'toolbar.background'],
            'TEXT.FOREGROUND': ['editor.foreground'],
            'CARET_COLOR': 'editor.foreground',
            'CARET_ROW_COLOR': 'editor.active_line.background',
            'SELECTION_BACKGROUND': ['editor.selection.background', 'tab.active_background', 'element.selected', 'ghost_element.selected'],
            'SELECTION_FOREGROUND': 'editor.selection.foreground',
            'LINE_NUMBERS_COLOR': 'editor.line_number',

            'MATCHED_BRACE_ATTRIBUTES.BACKGROUND': ['editor.indent_guide_active', 'editor.document_highlight.bracket_background'],

            # UI elements
            'CONSOLE_BACKGROUND_KEY': 'terminal.background',
            'CONSOLE_NORMAL_OUTPUT': 'terminal.foreground',

            # Terminal colors - regular
            'CONSOLE_BLACK_OUTPUT.FOREGROUND': 'terminal.ansi.black',
            'CONSOLE_RED_OUTPUT.FOREGROUND': 'terminal.ansi.red',
            'CONSOLE_GREEN_OUTPUT.FOREGROUND': 'terminal.ansi.green',
            'CONSOLE_YELLOW_OUTPUT.FOREGROUND': 'terminal.ansi.yellow',
            'CONSOLE_BLUE_OUTPUT.FOREGROUND': 'terminal.ansi.blue',
            'CONSOLE_MAGENTA_OUTPUT.FOREGROUND': 'terminal.ansi.magenta',
            'CONSOLE_CYAN_OUTPUT.FOREGROUND': 'terminal.ansi.cyan',
            'CONSOLE_WHITE_OUTPUT.FOREGROUND': 'terminal.ansi.white',

            #hint
            "DEFAULT_LINE_COMMENT.FOREGROUND": ["hint"],

            # Terminal colors - bright
            'CONSOLE_DARKGRAY_OUTPUT.FOREGROUND': 'terminal.ansi.bright_black',
            'CONSOLE_RED_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_red',
            'CONSOLE_GREEN_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_green',
            'CONSOLE_YELLOW_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_yellow',
            'CONSOLE_BLUE_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_blue',
            'CONSOLE_MAGENTA_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_magenta',
            'CONSOLE_CYAN_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_cyan',
            'CONSOLE_GRAY_OUTPUT.FOREGROUND': 'terminal.ansi.bright_white',

            # UI borders and panels
            'BORDER_COLOR': 'border',

            # File status colors
            'FILESTATUS_ADDED': 'created',
            'FILESTATUS_MODIFIED': 'modified',
            'FILESTATUS_DELETED': 'deleted',
            'FILESTATUS_UNKNOWN': 'warning',
            'FILESTATUS_IDEA_FILESTATUS_IGNORED': 'ignored',
        }

        # Map IntelliJ theme.json UI colors to Zed UI colors
        self.theme_ui_mapping = {
            # General UI colors - Core
            '*.background': ['background', 'surface.background', 'terminal.background', 'panel.background'],
            '*.foreground': ['text', 'text.accent', 'text.muted', 'terminal.foreground'],
            '*.selectionBackground': ['editor.selection.background', 'search.match_background'],
            '*.selectionForeground': 'editor.selection.foreground',
            '*.button': ['element.background'],
            '*.secondaryBackground': ['elevated_surface.background'],
            '*.disabled': ['text.placeholder', 'text.disabled', 'element.disabled', 'ghost_element.disabled', 'icon.disabled'],
            '*.contrast': ['border.variant', 'editor.wrap_guide'],
            '*.accent': ['text.accent', 'icon.accent'],
            # '*.highlight': ['element.selected', 'ghost_element.selected'],
            '*.selectionInactiveBackground': 'editor.highlighted_line.background',

            # Borders
            '*.border': ['border', 'editor.indent_guide'],

            # Tab colors
            'DefaultTabs.background': ['tab_bar.background', 'tab.inactive_background'],

            # Element states
            'TabbedPane.hoverColor': ['element.hover', 'ghost_element.hover'],
            'Button.focus': 'border.focused',

            # Tool windows and panels
            'ToolWindow.Header.inactiveBackground': ['title_bar.inactive_background'],
            'Popup.Header.activeBackground': ['elevated_surface.background'],

            # Status and notifications
            '*.notifications': ['status_bar.background', 'elevated_surface.background'],

            # Plugin buttons (map to element states)
            'Plugins.Button.installBackground': 'element.background',
            'Plugins.Button.updateBackground': 'element.active',
        }

        # Additional comprehensive mappings for Zed UI elements not covered by theme.json
        self.additional_zed_mappings = {
            # Editor specific elements (derived from base colors)
            'editor.active_line.background': 'editor.highlighted_line.background',
            'editor.active_wrap_guide': 'border.focused',
            'editor.invisible': 'text.placeholder',
            'editor.subheader.background': 'surface.background',

            # Pane and panel elements
            'pane.focused_border': 'border.focused',
            'pane_group.border': 'border.variant',
            'panel.focused_border': 'border.focused',
            'panel.indent_guide': 'border.variant',
            'panel.indent_guide_active': 'border',
            'panel.indent_guide_hover': 'border.focused',

            # Scrollbar elements (derived)
            'scrollbar.thumb.background': 'element.background',
            'scrollbar.thumb.border': 'border.variant',
            'scrollbar.thumb.hover_background': 'element.hover',
            'scrollbar.track.background': 'surface.background',
            'scrollbar.track.border': 'border.variant',


            # Status colors (will be set to reasonable defaults)
            'error': '#ff6b6b',
            'error.background': '#2d1b1b',
            'error.border': '#ff6b6b',
            'warning': '#ffd93d',
            'warning.background': '#2d2a1b',
            'warning.border': '#ffd93d',
            'success': '#6bcf7f',
            'success.background': '#1b2d1f',
            'success.border': '#6bcf7f',
            'info': '#74b9ff',
            'info.background': '#1b2332',
            'info.border': '#74b9ff',
            'hint': '#a29bfe',
            'hint.background': '#23212d',
            'hint.border': '#a29bfe',

            # Additional state colors
            'conflict': '#fd79a8',
            'conflict.background': '#2d1b26',
            'conflict.border': '#fd79a8',
            'created': '#00b894',
            'created.background': '#1b2d28',
            'created.border': '#00b894',
            'deleted': '#e17055',
            'deleted.background': '#2d201b',
            'deleted.border': '#e17055',
            'modified': '#fdcb6e',
            'modified.background': '#2d271b',
            'modified.border': '#fdcb6e',
            'renamed': '#a29bfe',
            'renamed.background': '#23212d',
            'renamed.border': '#a29bfe',
            'hidden': '#636e72',
            'hidden.background': '#1e2021',
            'hidden.border': '#636e72',
            'unreachable': '#636e72',
            'unreachable.background': '#1e2021',
            'unreachable.border': '#636e72',
            'predictive': '#74b9ff',
            'predictive.background': '#1b2332',
            'predictive.border': '#74b9ff',

            # Terminal ANSI colors (reasonable defaults)
            'terminal.ansi.black': '#2d3748',
            'terminal.ansi.red': '#e53e3e',
            'terminal.ansi.green': '#38a169',
            'terminal.ansi.yellow': '#d69e2e',
            'terminal.ansi.blue': '#3182ce',
            'terminal.ansi.magenta': '#805ad5',
            'terminal.ansi.cyan': '#319795',
            'terminal.ansi.white': '#a0aec0',
            'terminal.ansi.bright_black': '#4a5568',
            'terminal.ansi.bright_red': '#f56565',
            'terminal.ansi.bright_green': '#48bb78',
            'terminal.ansi.bright_yellow': '#ed8936',
            'terminal.ansi.bright_blue': '#4299e1',
            'terminal.ansi.bright_magenta': '#9f7aea',
            'terminal.ansi.bright_cyan': '#4fd1c7',
            'terminal.ansi.bright_white': '#f7fafc',
            'terminal.ansi.dim_black': '#1a202c',
            'terminal.ansi.dim_red': '#c53030',
            'terminal.ansi.dim_green': '#2f855a',
            'terminal.ansi.dim_yellow': '#b7791f',
            'terminal.ansi.dim_blue': '#2c5282',
            'terminal.ansi.dim_magenta': '#6b46c1',
            'terminal.ansi.dim_cyan': '#285e61',
            'terminal.ansi.dim_white': '#718096',
            'terminal.bright_foreground': '#f7fafc',
            'terminal.dim_foreground': '#718096',

            # Link and other interactive elements
            'link_text.hover': 'text.accent',
            'drop_target.background': 'element.selected',

            # Document highlight backgrounds - use subtle highlighting that won't conflict with caret row
            'editor.document_highlight.read_background': None,  # Disable to avoid conflicts
            'editor.document_highlight.write_background': 'editor.selection.background',

            # Title bar
            'title_bar.background': 'surface.background',
        }

        # Map IntelliJ attributes to Zed syntax elements
        self.syntax_mapping = {
            # Comments
            'DEFAULT_LINE_COMMENT': 'comment',
            'DEFAULT_BLOCK_COMMENT': 'comment',
            'DEFAULT_DOC_COMMENT': 'comment.doc',
            'CUSTOM_LINE_COMMENT_ATTRIBUTES': 'comment',
            'CUSTOM_MULTI_LINE_COMMENT_ATTRIBUTES': 'comment',

            # Keywords
            'DEFAULT_KEYWORD': 'keyword',
            'CUSTOM_KEYWORD1_ATTRIBUTES': 'keyword',
            'CUSTOM_KEYWORD2_ATTRIBUTES': 'keyword',
            'CUSTOM_KEYWORD3_ATTRIBUTES': 'keyword',
            'CUSTOM_KEYWORD4_ATTRIBUTES': 'keyword',

            # Strings
            'DEFAULT_STRING': 'string',
            'CUSTOM_STRING_ATTRIBUTES': 'string',
            'DEFAULT_VALID_STRING_ESCAPE': 'string.escape',
            'CUSTOM_VALID_STRING_ESCAPE_ATTRIBUTES': 'string.escape',
            'DEFAULT_INVALID_STRING_ESCAPE': 'string.escape',
            'CUSTOM_INVALID_STRING_ESCAPE_ATTRIBUTES': 'string.escape',

            # Numbers
            'DEFAULT_NUMBER': 'number',
            'CUSTOM_NUMBER_ATTRIBUTES': 'number',

            # Constants and booleans
            'DEFAULT_CONSTANT': 'constant',
            'DEFAULT_PREDEFINED_SYMBOL': 'boolean',
            'ENUM_CONST': 'constant',

            # Functions
            'DEFAULT_FUNCTION_DECLARATION': 'function',
            'DEFAULT_FUNCTION_CALL': 'function',
            'DEFAULT_STATIC_METHOD': 'function',

            # Types and classes
            'DEFAULT_CLASS_NAME': 'type',
            'DEFAULT_CLASS_REFERENCE': 'type',
            'DEFAULT_INTERFACE_NAME': 'type',

            # Variables and identifiers
            'DEFAULT_IDENTIFIER': 'variable',
            'DEFAULT_INSTANCE_FIELD': 'variable',
            'DEFAULT_STATIC_FIELD': 'variable',
            'DEFAULT_LOCAL_VARIABLE': 'variable',
            'DEFAULT_PARAMETER': 'variable.special',
            'DEFAULT_GLOBAL_VARIABLE': 'variable',

            # HTML/XML
            'DEFAULT_TAG': 'tag',
            'DEFAULT_ATTRIBUTE': 'attribute',
            'HTML_TAG': 'tag',
            'HTML_TAG_NAME': 'tag',
            'HTML_ATTRIBUTE_NAME': 'attribute',

            # Text literals
            'DEFAULT_TEMPLATE_LANGUAGE_COLOR': 'text.literal',

            # Language-specific mappings
            'PY.STRING': 'string',
            'RUBY_STRING': 'string',
            'COFFEESCRIPT.STRING': 'string',
            'CSS.PROPERTY_VALUE': 'string',
            'JSON.PROPERTY_KEY': 'attribute',
            'JAVA_DOC_TAG': 'comment.doc',
            'GO_PACKAGE': 'type',
            'JS.GLOBAL_FUNCTION': 'function',
            'JS.GLOBAL_VARIABLE': 'variable',
        }

    def load_intellij_theme(self, theme_path: Path) -> ET.Element:
        """Load IntelliJ theme from .icls file."""
        try:
            tree = ET.parse(theme_path)
            return tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Error parsing IntelliJ theme XML: {e}")
        except Exception as e:
            raise ValueError(f"Error loading IntelliJ theme: {e}")

    def load_theme_json(self, theme_json_path: Path) -> Dict[str, Any]:
        """Load IntelliJ theme.json file for additional UI colors."""
        try:
            with open(theme_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing theme.json file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading theme.json file: {e}")

    def normalize_color(self, color: str) -> str:
        """Normalize color format for Zed (ensure proper hex format)."""
        if not color:
            return None

        # Remove any whitespace and ensure uppercase
        color = color.strip().upper()

        # Add # prefix if missing
        if not color.startswith('#'):
            color = f'#{color}'

        # Ensure 6-digit hex (pad if needed)
        if len(color) == 4:  # #RGB -> #RRGGBB
            color = f'#{color[1]*2}{color[2]*2}{color[3]*2}'
        elif len(color) == 7:  # #RRGGBB (already correct)
            pass
        elif len(color) == 9:  # #RRGGBBAA -> #RRGGBB (remove alpha)
            color = color[:7]

        return color

    def extract_colors(self, root: ET.Element) -> Dict[str, str]:
        """Extract color definitions from IntelliJ theme."""
        colors = {}

        # Extract from colors section
        colors_element = root.find('colors')
        if colors_element is not None:
            for option in colors_element.findall('option'):
                name = option.get('name')
                value = option.get('value')
                if name and value:
                    normalized_color = self.normalize_color(value)
                    if normalized_color:
                        colors[name] = normalized_color

        # Extract colors from TEXT attribute (background and foreground)
        attributes_element = root.find('attributes')
        if attributes_element is not None:
            text_option = attributes_element.find("option[@name='TEXT']")
            if text_option is not None:
                value_element = text_option.find('value')
                if value_element is not None:
                    # Extract TEXT foreground
                    fg_option = value_element.find("option[@name='FOREGROUND']")
                    if fg_option is not None:
                        fg_color = self.normalize_color(fg_option.get('value'))
                        if fg_color:
                            colors['TEXT.FOREGROUND'] = fg_color

                    # Extract TEXT background
                    bg_option = value_element.find("option[@name='BACKGROUND']")
                    if bg_option is not None:
                        bg_color = self.normalize_color(bg_option.get('value'))
                        if bg_color:
                            colors['TEXT.BACKGROUND'] = bg_color

        # Extract background colors from all attributes for color mapping
        attributes_element = root.find('attributes')
        if attributes_element is not None:
            for option in attributes_element.findall('option'):
                name = option.get('name')
                if not name:
                    continue

                value_element = option.find('value')
                if value_element is not None:
                    # Extract background color for this attribute
                    bg_option = value_element.find("option[@name='BACKGROUND']")
                    if bg_option is not None:
                        bg_color = self.normalize_color(bg_option.get('value'))
                        if bg_color:
                            colors[f'{name}.BACKGROUND'] = bg_color

                    # Extract foreground color for this attribute
                    fg_option = value_element.find("option[@name='FOREGROUND']")
                    if fg_option is not None:
                        fg_color = self.normalize_color(fg_option.get('value'))
                        if fg_color:
                            colors[f'{name}.FOREGROUND'] = fg_color

        return colors

    def extract_theme_ui_colors(self, theme_json: Dict[str, Any]) -> Dict[str, str]:
        """Extract UI colors from IntelliJ theme.json file."""
        ui_colors = {}

        if 'ui' not in theme_json:
            return ui_colors

        ui_section = theme_json['ui']

        # Process UI sections
        for section_key, section_value in ui_section.items():
            if isinstance(section_value, dict):
                for property_key, color_value in section_value.items():
                    if isinstance(color_value, str) and color_value:
                        # Create full key like "*.background" or "DefaultTabs.borderColor"
                        full_key = f"{section_key}.{property_key}"
                        normalized_color = self.normalize_color(color_value)
                        if normalized_color:
                            ui_colors[full_key] = normalized_color

        return ui_colors

    def extract_attributes(self, root: ET.Element) -> Dict[str, Dict[str, Any]]:
        """Extract syntax highlighting attributes from IntelliJ theme."""
        attributes = {}

        attributes_element = root.find('attributes')
        if attributes_element is not None:
            for option in attributes_element.findall('option'):
                name = option.get('name')
                if not name:
                    continue

                attribute = {}
                value_element = option.find('value')
                if value_element is not None:
                    # Extract foreground color
                    fg_option = value_element.find("option[@name='FOREGROUND']")
                    if fg_option is not None:
                        fg_color = self.normalize_color(fg_option.get('value'))
                        if fg_color:
                            attribute['color'] = fg_color

                    # Extract background color
                    bg_option = value_element.find("option[@name='BACKGROUND']")
                    if bg_option is not None:
                        bg_color = self.normalize_color(bg_option.get('value'))
                        if bg_color:
                            attribute['background'] = bg_color

                    # Extract font style
                    font_option = value_element.find("option[@name='FONT_TYPE']")
                    if font_option is not None:
                        font_type = font_option.get('value')
                        if font_type:
                            try:
                                font_int = int(font_type)
                                if font_int & 1:  # Bold
                                    attribute['font_weight'] = 'bold'
                                if font_int & 2:  # Italic
                                    attribute['font_style'] = 'italic'
                            except ValueError:
                                pass

                if attribute:
                    attributes[name] = attribute
        return attributes

    def map_colors_to_zed(self, intellij_colors: Dict[str, str]) -> Dict[str, str]:
        """Map IntelliJ colors to Zed UI colors."""
        zed_colors = {}

        for intellij_name, zed_mapping in self.color_mapping.items():
            if intellij_name in intellij_colors:
                color_value = intellij_colors[intellij_name]

                # Handle both single mappings and multiple mappings
                if isinstance(zed_mapping, list):
                    # Map to multiple Zed properties
                    for zed_name in zed_mapping:
                        zed_colors[zed_name] = color_value
                else:
                    # Single mapping
                    zed_colors[zed_mapping] = color_value

        # Add some default Zed UI colors if not present
        if 'background' not in zed_colors and 'TEXT.BACKGROUND' in intellij_colors:
            zed_colors['background'] = intellij_colors['TEXT.BACKGROUND']

        if 'editor.background' not in zed_colors and 'TEXT.BACKGROUND' in intellij_colors:
            zed_colors['editor.background'] = intellij_colors['TEXT.BACKGROUND']

        if 'text' not in zed_colors and 'TEXT.FOREGROUND' in intellij_colors:
            zed_colors['text'] = intellij_colors['TEXT.FOREGROUND']

        if 'editor.foreground' not in zed_colors and 'TEXT.FOREGROUND' in intellij_colors:
            zed_colors['editor.foreground'] = intellij_colors['TEXT.FOREGROUND']

        # Set reasonable defaults for common UI elements
        if 'border' not in zed_colors:
            # Derive border color from background (lighter)
            bg_color = zed_colors.get('background', '#2D2D2D')
            zed_colors['border'] = self.derive_lighter_color(bg_color)

        return zed_colors

    def map_theme_ui_colors_to_zed(self, theme_ui_colors: Dict[str, str]) -> Dict[str, str]:
        """Map IntelliJ theme.json UI colors to Zed UI colors."""
        zed_colors = {}

        for theme_key, zed_mapping in self.theme_ui_mapping.items():
            if theme_key in theme_ui_colors:
                color_value = theme_ui_colors[theme_key]

                # Handle both single mappings and multiple mappings
                if isinstance(zed_mapping, list):
                    # Map to multiple Zed properties
                    for zed_name in zed_mapping:
                        zed_colors[zed_name] = color_value
                else:
                    # Single mapping
                    zed_colors[zed_mapping] = color_value

        return zed_colors

    def apply_additional_zed_mappings(self, zed_colors: Dict[str, str]) -> Dict[str, str]:
        """Apply additional Zed UI element mappings using existing colors as sources."""
        for target_zed_key, source_key in self.additional_zed_mappings.items():
            if target_zed_key not in zed_colors:
                if isinstance(source_key, str):
                    if source_key.startswith('#'):
                        # Direct color value
                        zed_colors[target_zed_key] = source_key
                    elif source_key in zed_colors:
                        # Use existing color as source
                        zed_colors[target_zed_key] = zed_colors[source_key]
                    elif source_key == 'background' and 'background' in zed_colors:
                        # Special handling for background references
                        zed_colors[target_zed_key] = zed_colors['background']
                    elif source_key == 'text.muted' and 'text.disabled' in zed_colors:
                        # Fallback for text.muted to text.disabled
                        zed_colors[target_zed_key] = zed_colors['text.disabled']
                    elif source_key == 'text.placeholder' and 'text.disabled' in zed_colors:
                        # Fallback for text.placeholder to text.disabled
                        zed_colors[target_zed_key] = zed_colors['text.disabled']

        return zed_colors

    def map_syntax_to_zed(self, intellij_attributes: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Map IntelliJ syntax attributes to Zed syntax elements."""
        zed_syntax = {}

        for intellij_name, intellij_attr in intellij_attributes.items():
            if intellij_name in self.syntax_mapping:
                zed_mapping = self.syntax_mapping[intellij_name]

                zed_attr = {}
                if 'color' in intellij_attr:
                    zed_attr['color'] = intellij_attr['color']

                if 'font_style' in intellij_attr:
                    zed_attr['font_style'] = intellij_attr['font_style']
                else:
                    zed_attr['font_style'] = None

                if 'font_weight' in intellij_attr:
                    zed_attr['font_weight'] = intellij_attr['font_weight']
                else:
                    zed_attr['font_weight'] = None

                # Only add if we have meaningful content
                if zed_attr.get('color') or zed_attr.get('font_style') or zed_attr.get('font_weight'):
                    # Handle both single mappings and multiple mappings
                    if isinstance(zed_mapping, list):
                        # Map to multiple Zed syntax elements
                        for zed_name in zed_mapping:
                            zed_syntax[zed_name] = zed_attr.copy()
                    else:
                        # Single mapping
                        zed_syntax[zed_mapping] = zed_attr

        return zed_syntax

    def derive_lighter_color(self, hex_color: str, factor: float = 1.2) -> str:
        """Derive a lighter version of a color."""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')

            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # Lighten by factor
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))

            return f'#{r:02X}{g:02X}{b:02X}'
        except:
            # Fallback to a reasonable default
            return '#404040'

    def generate_default_players(self) -> List[Dict[str, str]]:
        """Generate default player colors for collaborative editing."""
        player_colors = [
            "#566dda", "#bf41bf", "#aa563b", "#955ae6",
            "#3a8bc6", "#be4677", "#a06d3a", "#2b9292"
        ]

        players = []
        for color in player_colors:
            players.append({
                "cursor": f"{color}ff",
                "background": f"{color}ff",
                "selection": f"{color}3d"
            })

        return players

    def convert_to_zed(self, intellij_root: ET.Element, theme_name: str, author: str = "Converted from IntelliJ", theme_json: Dict[str, Any] = None) -> Dict[str, Any]:
        """Convert IntelliJ theme to Zed format."""

        # Extract colors and attributes from .icls file
        intellij_colors = self.extract_colors(intellij_root)
        intellij_attributes = self.extract_attributes(intellij_root)

        # Map .icls colors to Zed format
        zed_ui_colors = self.map_colors_to_zed(intellij_colors)
        zed_syntax = self.map_syntax_to_zed(intellij_attributes)

        # Extract and merge UI colors from theme.json if provided
        if theme_json:
            theme_ui_colors = self.extract_theme_ui_colors(theme_json)
            zed_theme_ui_colors = self.map_theme_ui_colors_to_zed(theme_ui_colors)

            # Merge theme.json UI colors (they take priority over .icls colors)
            zed_ui_colors.update(zed_theme_ui_colors)

        # Apply additional comprehensive Zed UI mappings
        zed_ui_colors = self.apply_additional_zed_mappings(zed_ui_colors)

        # Determine appearance (dark/light) based on background color
        appearance = "dark"
        if 'background' in zed_ui_colors:
            bg_color = zed_ui_colors['background']
            # Simple heuristic: if background is light, theme is light
            try:
                bg_rgb = int(bg_color.lstrip('#'), 16)
                luminance = (bg_rgb >> 16) + ((bg_rgb >> 8) & 0xFF) + (bg_rgb & 0xFF)
                if luminance > 384:  # Threshold for light theme
                    appearance = "light"
            except:
                pass

        # Build Zed theme structure
        zed_theme = {
            "$schema": "https://zed.dev/schema/themes/v0.1.0.json",
            "name": theme_name,
            "author": author,
            "themes": [
                {
                    "name": theme_name,
                    "appearance": appearance,
                    "style": {
                        **zed_ui_colors,
                        "players": self.generate_default_players(),
                        "syntax": zed_syntax
                    }
                }
            ]
        }

        return zed_theme

    def convert_theme_file(self, input_path: Path, output_path: Path = None, author: str = None, theme_json_path: Path = None) -> Path:
        """Convert an IntelliJ theme file to Zed format."""

        # Load IntelliJ theme
        intellij_root = self.load_intellij_theme(input_path)

        # Load optional theme.json file
        theme_json = None
        if theme_json_path and theme_json_path.exists():
            theme_json = self.load_theme_json(theme_json_path)

        # Get theme name
        theme_name = intellij_root.get('name', input_path.stem)

        # Generate output path if not provided
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_zed.json"

        # Set author
        if author is None:
            author = f"Converted from IntelliJ ({theme_name})"

        # Convert to Zed format
        zed_theme = self.convert_to_zed(intellij_root, theme_name, author, theme_json)

        # Write output file with proper formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(zed_theme, f, indent=2, ensure_ascii=False)

        return output_path


def main():
    parser = argparse.ArgumentParser(description='Convert IntelliJ themes to Zed format')
    parser.add_argument('input', type=Path, help='Input IntelliJ theme .icls file')
    parser.add_argument('-o', '--output', type=Path, help='Output Zed theme .json file')
    parser.add_argument('-a', '--author', type=str, help='Theme author name')
    parser.add_argument('-t', '--theme-json', type=Path, help='Optional IntelliJ theme.json file for enhanced UI colors')

    args = parser.parse_args()

    converter = IntelliJToZedConverter()

    try:
        output_path = converter.convert_theme_file(args.input, args.output, args.author, args.theme_json)
        print(f"✅ Successfully converted theme!")
        print(f"📁 Input:  {args.input}")
        if args.theme_json:
            print(f"📁 Theme JSON: {args.theme_json}")
        print(f"📁 Output: {output_path}")

    except Exception as e:
        print(f"❌ Error converting theme: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
