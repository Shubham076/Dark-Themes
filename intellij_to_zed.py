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
            'TEXT.FOREGROUND': ['editor.foreground', 'editor.selection.foreground', 'elevated_surface.foreground', 'text', 'text.accent', 'text.muted', 'terminal.foreground', 'editor.line_number'],
            'CARET_ROW_COLOR': ['editor.active_line.background', 'tab.active_background', 'scrollbar.thumb.background', 'editor.indent_guide', 'elevated_surface.background'],
            'SELECTION_BACKGROUND': ['editor.selection.background', 'element.selected', 'ghost_element.selected', 'search.match_background', 'panel.focused_border'],

            'MATCHED_BRACE_ATTRIBUTES.BACKGROUND': ['editor.indent_guide_active', 'editor.document_highlight.bracket_background'],

            # UI elements
            'CONSOLE_BACKGROUND_KEY': 'terminal.background',
            'CONSOLE_NORMAL_OUTPUT': 'terminal.foreground',

            # Terminal colors - regular
            # 'CONSOLE_BLACK_OUTPUT.FOREGROUND': 'terminal.ansi.black',
            # 'CONSOLE_RED_OUTPUT.FOREGROUND': 'terminal.ansi.red',
            # 'CONSOLE_GREEN_OUTPUT.FOREGROUND': 'terminal.ansi.green',
            # 'CONSOLE_YELLOW_OUTPUT.FOREGROUND': 'terminal.ansi.yellow',
            # 'CONSOLE_BLUE_OUTPUT.FOREGROUND': 'terminal.ansi.blue',
            # 'CONSOLE_MAGENTA_OUTPUT.FOREGROUND': 'terminal.ansi.magenta',
            # 'CONSOLE_CYAN_OUTPUT.FOREGROUND': 'terminal.ansi.cyan',
            # 'CONSOLE_WHITE_OUTPUT.FOREGROUND': 'terminal.ansi.white',

            #hint
            "DEFAULT_LINE_COMMENT.FOREGROUND": ["hint"],

            # Terminal colors - bright
            # 'CONSOLE_DARKGRAY_OUTPUT.FOREGROUND': 'terminal.ansi.bright_black',
            # 'CONSOLE_RED_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_red',
            # 'CONSOLE_GREEN_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_green',
            # 'CONSOLE_YELLOW_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_yellow',
            # 'CONSOLE_BLUE_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_blue',
            # 'CONSOLE_MAGENTA_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_magenta',
            # 'CONSOLE_CYAN_BRIGHT_OUTPUT.FOREGROUND': 'terminal.ansi.bright_cyan',
            # 'CONSOLE_GRAY_OUTPUT.FOREGROUND': 'terminal.ansi.bright_white'

            # UI borders and panels
            'BORDER_COLOR': 'border',

            # File status colors
            # 'FILESTATUS_ADDED': 'created',
            # 'FILESTATUS_MODIFIED': 'modified',
            # 'FILESTATUS_DELETED': 'deleted',
            # 'FILESTATUS_UNKNOWN': 'warning',
            # 'FILESTATUS_IDEA_FILESTATUS_IGNORED': 'ignored'
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

            # Additional state colors
            'conflict': '#fd79a8',
            'conflict.background': '#2d1b26',
            'conflict.border': '#fd79a8',

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
            'DEFAULT_LINE_COMMENT': ['comment', 'comment.doc', 'comment.documentation', 'string.documentation'],

            # Keywords - comprehensive coverage
            'DEFAULT_KEYWORD': ['keyword', 'keyword.modifier', 'keyword.type', 'keyword.coroutine',
                                'keyword.function', 'keyword.import', 'keyword.return', 'keyword.operator',
                                'keyword.repeat', 'keyword.debug', 'keyword.exception', 'keyword.conditional',
                                'keyword.conditional.ternary', 'keyword.export'],

            # Strings - all variants
            'DEFAULT_STRING': ['string', 'string.documentation', 'string.doc'],
            'DEFAULT_VALID_STRING_ESCAPE': ['string.escape', 'string.special', 'string.special.path',
                                            'string.special.symbol', 'string.special.url'],

            # Numbers - all numeric types
            'DEFAULT_NUMBER': ['number', 'number.float', 'float'],

            # Constants and booleans
            'DEFAULT_CONSTANT': ['constant', 'constant.builtin', 'constant.macro'],
            'DEFAULT_PREDEFINED_SYMBOL': ['boolean', 'constant.builtin'],
            'ENUM_CONST': ['enum'],

            # Functions - comprehensive function coverage
            'DEFAULT_FUNCTION_DECLARATION': ['function', 'function.builtin', 'function.call', 'function.macro',
                                             'function.method', 'function.method.call', 'function.decorator'],
            'DEFAULT_FUNCTION_CALL': ['function.call', 'function.method.call'],
            'DEFAULT_STATIC_METHOD': ['function.method', 'function.builtin'],

            # Types and classes - expanded coverage
            'DEFAULT_CLASS_NAME': ['type', 'type.builtin', 'type.definition', 'type.interface',
                                   'type.super', 'type.class.definition', 'namespace'],

            # Variables and identifiers - granular mapping
            'DEFAULT_IDENTIFIER': ['variable', 'variable.member', 'variable.builtin'],
            'DEFAULT_INSTANCE_FIELD': ['field', 'property'],
            'DEFAULT_PARAMETER': ['variable.parameter', 'parameter'],

            # Operators and punctuation
            'DEFAULT_OPERATION_SIGN': ['operator', 'punctuation', 'punctuation.delimiter'],
            'DEFAULT_BRACKETS': ['punctuation.bracket'],

            # HTML/XML - expanded
            'DEFAULT_TAG': ['tag', 'tag.delimiter'],
            'DEFAULT_ATTRIBUTE': ['attribute', 'tag.attribute'],

            # Special elements
            'DEFAULT_TEMPLATE_LANGUAGE_COLOR': ['text.literal', 'embedded'],
            'DEFAULT_METADATA': ['attribute', 'punctuation.special'],
            'DEFAULT_LABEL': ['label'],

            # Preprocessor and directives
            'DEFAULT_PREPROCESSOR_DIRECTIVE': ['keyword.directive', 'keyword.directive.define'],

            # Documentation and markup
            'DEFAULT_DOC_MARKUP': ['emphasis', 'emphasis.strong'],
            'DEFAULT_DOC_COMMENT_TAG': ['comment.doc', 'punctuation.special'],

            # Error and warning highlights
            'WRONG_REFERENCES_ATTRIBUTES': ['comment.error'],
            'WARNING_ATTRIBUTES': ['comment.warning'],

            'JSON.PROPERTY_KEY': ['property']

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

        # Generate darker variants for UI elements that need visual hierarchy
        if 'TEXT.BACKGROUND' in intellij_colors:
            base_bg = intellij_colors['TEXT.BACKGROUND']
            bg_variants = self.generate_color_variants(base_bg)

            # Use 20% darker for secondary UI elements
            darker_bg = bg_variants['darker_2']

            # Apply darker background to elements that need visual separation
            ui_elements_needing_darker_bg = [
                'surface.background', 'panel.background', 'element.background', 'tab_bar.background',
                'tab.inactive_background', 'status_bar.background'
            ]

            for element in ui_elements_needing_darker_bg:
                if element not in zed_colors:
                    zed_colors[element] = darker_bg

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

        # Process DEFAULT_ attributes first to establish base colors
        for intellij_name, intellij_attr in intellij_attributes.items():
            if intellij_name.startswith('DEFAULT_') and intellij_name in self.syntax_mapping:
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

        # Process non-DEFAULT attributes only if they don't conflict with existing mappings
        for intellij_name, intellij_attr in intellij_attributes.items():
            if not intellij_name.startswith('DEFAULT_') and intellij_name in self.syntax_mapping:
                zed_mapping = self.syntax_mapping[intellij_name]

                # Skip if this would override a DEFAULT_ mapping
                if isinstance(zed_mapping, list):
                    skip = any(zed_name in zed_syntax for zed_name in zed_mapping)
                else:
                    skip = zed_mapping in zed_syntax

                if skip:
                    continue

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
                            if zed_name not in zed_syntax:
                                zed_syntax[zed_name] = zed_attr.copy()
                    else:
                        # Single mapping
                        if zed_mapping not in zed_syntax:
                            zed_syntax[zed_mapping] = zed_attr

        # Add fallbacks for missing syntax colors using foreground color
        return self.add_syntax_fallbacks(zed_syntax)

    def add_syntax_fallbacks(self, zed_syntax: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Add fallback colors for missing syntax elements using foreground color."""
        # Define essential syntax elements that should have fallbacks
        essential_elements = [
            'comment', 'comment.doc', 'keyword', 'string', 'string.escape',
            'number', 'constant', 'boolean', 'function', 'type', 'variable',
            'variable.special', 'tag', 'attribute', 'text.literal', 'property'
        ]

        # Get foreground color as fallback (from TEXT.FOREGROUND or default)
        fallback_color = self.get_fallback_color()

        for element in essential_elements:
            if element not in zed_syntax:
                # Add fallback using foreground color
                zed_syntax[element] = {
                    'color': fallback_color,
                    'font_style': None,
                    'font_weight': None
                }
            elif 'color' not in zed_syntax[element] or not zed_syntax[element]['color']:
                # Element exists but has no color, use fallback
                zed_syntax[element]['color'] = fallback_color

        return zed_syntax

    def get_fallback_color(self) -> str:
        """Get fallback color (foreground color or reasonable default)."""
        # This will be set during conversion process
        return getattr(self, '_fallback_color', '#BBBBBB')

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

    def adjust_brightness(self, hex_color: str, factor: float) -> str:
        """Adjust brightness of a color by a factor (0.0 = black, 1.0 = original, >1.0 = brighter)."""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')

            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # Adjust brightness
            r = max(0, min(255, int(r * factor)))
            g = max(0, min(255, int(g * factor)))
            b = max(0, min(255, int(b * factor)))

            return f'#{r:02X}{g:02X}{b:02X}'
        except:
            # Fallback to original color
            return hex_color if hex_color.startswith('#') else f'#{hex_color}'

    def adjust_saturation(self, hex_color: str, factor: float) -> str:
        """Adjust saturation of a color (0.0 = grayscale, 1.0 = original, >1.0 = more saturated)."""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')

            # Convert to RGB
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0

            # Convert to HSL-like adjustment
            max_val = max(r, g, b)
            min_val = min(r, g, b)
            diff = max_val - min_val

            # Calculate luminance
            luminance = (max_val + min_val) / 2

            # Adjust saturation
            if diff == 0:  # Grayscale
                return hex_color if hex_color.startswith('#') else f'#{hex_color}'

            # Apply saturation adjustment
            r = luminance + (r - luminance) * factor
            g = luminance + (g - luminance) * factor
            b = luminance + (b - luminance) * factor

            # Clamp values
            r = max(0, min(1, r))
            g = max(0, min(1, g))
            b = max(0, min(1, b))

            # Convert back to RGB
            r_int = int(r * 255)
            g_int = int(g * 255)
            b_int = int(b * 255)

            return f'#{r_int:02X}{g_int:02X}{b_int:02X}'
        except:
            # Fallback to original color
            return hex_color if hex_color.startswith('#') else f'#{hex_color}'

    def add_alpha(self, hex_color: str, alpha: float) -> str:
        """Add alpha channel to a hex color (alpha: 0.0-1.0)."""
        try:
            # Ensure proper hex format
            if not hex_color.startswith('#'):
                hex_color = f'#{hex_color}'

            # Clamp alpha value
            alpha = max(0.0, min(1.0, alpha))
            alpha_hex = format(int(alpha * 255), '02X')

            return f'{hex_color}{alpha_hex}'
        except:
            return hex_color

    def generate_color_variants(self, base_color: str) -> Dict[str, str]:
        """Generate various color variants from a base color for theme consistency."""
        if not base_color:
            return {}

        variants = {
            'base': self.normalize_color(base_color),
        }

        base_normalized = variants['base']
        if not base_normalized:
            return variants

        # Brightness variants
        variants['darker_2'] = self.adjust_brightness(base_normalized, 0.98)
        variants['darker_5'] = self.adjust_brightness(base_normalized, 0.95)
        variants['darker_10'] = self.adjust_brightness(base_normalized, 0.9)
        variants['darker_15'] = self.adjust_brightness(base_normalized, 0.85)
        variants['darker_20'] = self.adjust_brightness(base_normalized, 0.80)

        variants['lighter_2'] = self.adjust_brightness(base_normalized, 1.02)
        variants['lighter_5'] = self.adjust_brightness(base_normalized, 1.05)
        variants['lighter_10'] = self.adjust_brightness(base_normalized, 1.10)
        variants['lighter_15'] = self.adjust_brightness(base_normalized, 1.15)
        variants['lighter_20'] = self.adjust_brightness(base_normalized, 1.2)

        # Combined variants (commonly used in themes)
        variants['hover'] = self.adjust_brightness(base_normalized, 1.1)  # Slightly lighter for hover
        variants['active'] = self.adjust_brightness(base_normalized, 0.9)  # Slightly darker for active
        variants['disabled'] = self.adjust_saturation(
            self.adjust_brightness(base_normalized, 0.7), 0.5
        )  # Darker and desaturated for disabled
        variants['muted'] = self.adjust_saturation(base_normalized, 0.6)  # Desaturated for muted

        return variants

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

        # Set fallback color for syntax elements (use mapped editor.foreground)
        self._fallback_color = zed_ui_colors.get('editor.foreground', '#BBBBBB')

        # Apply fallbacks to syntax elements
        zed_syntax = self.add_syntax_fallbacks(zed_syntax)

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

        zed_ui_colors["info"] = zed_ui_colors["editor.foreground"]
        zed_ui_colors["warning"] = zed_ui_colors["editor.foreground"]
        zed_ui_colors["error"] = zed_ui_colors["editor.foreground"]
        zed_ui_colors["hint"] = zed_ui_colors["editor.foreground"]
        zed_ui_colors["success"] = zed_ui_colors["editor.foreground"]

        caret_row_color = intellij_colors['CARET_ROW_COLOR']
        caret_variants = self.generate_color_variants(caret_row_color)

        # Use 2% darker for border elements
        border_color_dark = caret_variants['lighter_20']
        border_color_light = caret_variants['darker_15']

        if appearance == 'light':
            zed_ui_colors["info.background"] = "#C2D8F2"
            zed_ui_colors["info.border"] = "#C2D8F2"
            zed_ui_colors["error.background"] = "#FFD5CC"
            zed_ui_colors["error.border"] = "#FFD5CC"
            zed_ui_colors["warning.background"] = "#FFE8B4"
            zed_ui_colors["warning.border"] = "#FFE8B4"
            zed_ui_colors["hint.background"] = "#FFE8B4"
            zed_ui_colors["hint.border"] = "#FFE8B4"
            zed_ui_colors["success.background"] = "#BEE6BE"
            zed_ui_colors["success.border"]  = "#BEE6BE"

            zed_ui_colors["terminal.ansi.black"] = "#BFB9BA"
            zed_ui_colors["terminal.ansi.red"] = "#E14775"
            zed_ui_colors["terminal.ansi.green"] = "#269D69"
            zed_ui_colors["terminal.ansi.yellow"] = "#AB6763"
            zed_ui_colors["terminal.ansi.blue"] = "#E16032"
            zed_ui_colors["terminal.ansi.magenta"] = "#79619E"
            zed_ui_colors["terminal.ansi.cyan"] = "#286A84"
            zed_ui_colors["terminal.ansi.white"] = "#606060"
            zed_ui_colors["terminal.ansi.bright_black"] = "#A59FA0"
            zed_ui_colors["terminal.ansi.bright_red"] = "#E14775"
            zed_ui_colors["terminal.ansi.bright_green"] = "#269D69"
            zed_ui_colors["terminal.ansi.bright_yellow"] = "#AB6763"
            zed_ui_colors["terminal.ansi.bright_blue"] = "#E16032"
            zed_ui_colors["terminal.ansi.bright_magenta"] = "#79619E"
            zed_ui_colors["terminal.ansi.bright_cyan"] = "#286A84"
            zed_ui_colors["terminal.ansi.bright_white"] = "#918C8E"

            zed_ui_colors["created"] = "#319668"
            zed_ui_colors["modified"] = "#007599"
            zed_ui_colors["deleted"] = "#d75c4d"
            zed_ui_colors["ignored"] = "#8d8788"
            zed_ui_colors["renamed"] = "#664d9b"

            zed_ui_colors["border"] = border_color_light
        else:
            zed_ui_colors["info.background"] = "#385570"
            zed_ui_colors["info.border"] = "#385570"
            zed_ui_colors["error.background"] = "#45302B"
            zed_ui_colors["error.border"] = "#45302B"
            zed_ui_colors["warning.background"] = "#614438"
            zed_ui_colors["warning.border"] = "#614438"
            zed_ui_colors["hint.background"] = "#614438"
            zed_ui_colors["hint.border"] = "#614438"
            zed_ui_colors["success.background"] = "#294436"
            zed_ui_colors["success.border"] = "#294436"

            zed_ui_colors["terminal.ansi.black"] = "#353535"
            zed_ui_colors["terminal.ansi.red"] = "#F78D8C"
            zed_ui_colors["terminal.ansi.green"] = "#B8BB26"
            zed_ui_colors["terminal.ansi.yellow"] = "#FABD2F"
            zed_ui_colors["terminal.ansi.blue"] = "#84A498"
            zed_ui_colors["terminal.ansi.magenta"] = "#D3859A"
            zed_ui_colors["terminal.ansi.cyan"] = "#8EC07B"
            zed_ui_colors["terminal.ansi.white"] = "#EBDBB2"

            zed_ui_colors["terminal.ansi.bright_black"] = "#353535"
            zed_ui_colors["terminal.ansi.bright_red"] = "#F28E82"
            zed_ui_colors["terminal.ansi.bright_green"] = "#B2B437"
            zed_ui_colors["terminal.ansi.bright_yellow"] = "#F1BF4A"
            zed_ui_colors["terminal.ansi.bright_blue"] = "#95A19D"
            zed_ui_colors["terminal.ansi.bright_magenta"] = "#CD98A6"
            zed_ui_colors["terminal.ansi.bright_cyan"] = "#9EBD93"
            zed_ui_colors["terminal.ansi.bright_white"] = "#EBDBB2"

            zed_ui_colors["created"] = "#C3E887"
            zed_ui_colors["modified"] = "#80CBC4"
            zed_ui_colors["deleted"] = "#F77669"
            zed_ui_colors["ignored"] = "#637777"
            zed_ui_colors["renamed"] = "#C792EA"

            zed_ui_colors["border"] = border_color_dark


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
