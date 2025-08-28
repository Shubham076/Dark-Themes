#!/usr/bin/env python3
"""
IntelliJ to Sublime Theme Converter (JSON Format)

This script converts IntelliJ IDEA theme files (.icls/.xml) to Sublime Text's modern
JSON theme format (.sublime-color-scheme).
It parses the IntelliJ scheme format and maps the colors and attributes to Sublime's
modern JSON format with variables, globals, and rules.

Usage:
    python intellij_to_sublime_json.py input_theme.icls output_theme.sublime-color-scheme
"""

import xml.etree.ElementTree as ET
import argparse
import sys
import os
import json
from typing import Dict, List, Optional, Tuple


class IntelliJToSublimeJSONConverter:
    """Converts IntelliJ themes to Sublime Text's modern JSON format."""

    def __init__(self):
        # Comprehensive mapping from IntelliJ attributes to grouped Sublime scopes
        # Following the semantic grouping approach used in real Sublime themes
        self.semantic_groups = {
            'Keywords': {
                'scopes': 'keyword, keyword.other, keyword.control, variable.language.class, storage.modifier',
                'intellij_attrs': ['DEFAULT_KEYWORD', 'CUSTOM_KEYWORD1_ATTRIBUTES', 'CUSTOM_KEYWORD2_ATTRIBUTES', 'CUSTOM_KEYWORD3_ATTRIBUTES', 'CUSTOM_KEYWORD4_ATTRIBUTES'],
                'variable': 'keyword_color'
            },
            'Storage Types': {
                'scopes': 'storage, storage.type, storage.type.builtin, storage.modifier, meta.namespace, entity.name, support.class, entity.name.type, entity.name.class',
                'intellij_attrs': ['DEFAULT_CLASS_NAME', 'DEFAULT_CLASS_REFERENCE', 'DEFAULT_INTERFACE_NAME', 'DEFAULT_METADATA', 'GO_PACKAGE', 'PY.ANNOTATION'],
                'variable': 'storage_color'
            },
            'Strings': {
                'scopes': 'string, string.quoted, string.quoted.single, string.quoted.double, string.quoted.triple, string.unquoted, string.template, string.regexp, string.other.link',
                'intellij_attrs': ['DEFAULT_STRING'],
                'variable': 'string_color'
            },
            'Functions': {
                'scopes': 'entity.name.function, variable.function, support.function, meta.function-call, keyword.other.special-method, support.function.builtin',
                'intellij_attrs': ['DEFAULT_FUNCTION_DECLARATION', 'DEFAULT_FUNCTION_CALL', 'DEFAULT_STATIC_METHOD', 'BASH.EXTERNAL_COMMAND', 'JS.GLOBAL_FUNCTION', 'PY.BUILTIN_NAME', 'CSS.FUNCTION'],
                'variable': 'function_color'
            },
            'Variables': {
                'scopes': 'variable, variable.other, variable.other.readwrite, variable.other.member, variable.other.global, variable.other.local, variable.other.constant, meta.block variable.other, variable.language.anonymous, meta.function.declaration variable.parameter, variable.other.readwrite.declaration, variable.parameter',
                'intellij_attrs': ['DEFAULT_IDENTIFIER', 'DEFAULT_PARAMETER', 'DEFAULT_LOCAL_VARIABLE', 'DEFAULT_INSTANCE_FIELD', 'DEFAULT_STATIC_FIELD', 'DEFAULT_GLOBAL_VARIABLE', 'DEFAULT_REASSIGNED_LOCAL_VARIABLE', 'DEFAULT_REASSIGNED_PARAMETER', 'JS.GLOBAL_VARIABLE', 'PY.SELF_PARAMETER', 'PY.KEYWORD_ARGUMENT', 'GO_METHOD_RECEIVER'],
                'variable': 'variable_color'
            },
            'Constants': {
                'scopes': 'constant, constant.numeric, constant.language, constant.character, constant.character.escape, constant.other, variable.other.constant, support.constant, keyword.other.unit',
                'intellij_attrs': ['DEFAULT_CONSTANT', 'DEFAULT_NUMBER', 'DEFAULT_VALID_STRING_ESCAPE', 'CSS.UNIT', 'CSS.COLOR'],
                'variable': 'constant_color'
            },
            'Comments': {
                'scopes': 'comment, comment.line, comment.block, comment.documentation, punctuation.definition.comment, comment.line.shebang',
                'intellij_attrs': ['DEFAULT_COMMENT', 'DEFAULT_LINE_COMMENT', 'DEFAULT_BLOCK_COMMENT', 'DEFAULT_DOC_COMMENT', 'BASH.SHEBANG'],
                'variable': 'comment_color'
            },
            'Operators': {
                'scopes': 'keyword.operator, keyword.operator.logical, keyword.operator.comparison, keyword.operator.assignment, keyword.operator.arithmetic, keyword.operator.regexp',
                'intellij_attrs': ['DEFAULT_OPERATION_SIGN', 'CSS.OPERATORS', 'REGEXP.META', 'REGEXP.QUANTIFIER'],
                'variable': 'operator_color'
            },
            'Punctuation': {
                'scopes': 'punctuation, punctuation.separator, punctuation.separator.comma, punctuation.terminator, punctuation.terminator.semicolon, punctuation.section, punctuation.section.braces, punctuation.section.brackets, punctuation.section.parens, punctuation.accessor.dot, punctuation.separator.colon, punctuation.definition',
                'intellij_attrs': ['DEFAULT_BRACES', 'DEFAULT_BRACKETS', 'DEFAULT_PARENTHS', 'DEFAULT_COMMA', 'DEFAULT_DOT', 'DEFAULT_SEMICOLON', 'DEFAULT_COLON', 'REGEXP.PARENTHS', 'REGEXP.BRACKETS', 'REGEXP.BRACES'],
                'variable': 'punctuation_color'
            },
            'JSON Keys': {
                'scopes': 'source.json meta.mapping.key.json string.quoted.double.json',
                'intellij_attrs': ['JSON.PROPERTY_KEY'],
                'variable': 'json_key_color'
            },
            'JSON Values': {
                'scopes': 'source.json meta.mapping.value.json meta.string.json string.quoted.double.json',
                'intellij_attrs': ['JSON.PROPERTY_VALUE'],
                'variable': 'json_value_color'
            },
            'YAML Keys': {
                'scopes': 'source.yaml meta.mapping.key.yaml meta.string.yaml string.unquoted.plain.out.yaml, source.yaml meta.mapping.key.yaml meta.string.yaml string.quoted.double.yaml, source.yaml meta.mapping.key.yaml meta.string.yaml string.quoted.single.yaml',
                'intellij_attrs': ['YAML_SCALAR_KEY'],
                'variable': 'yaml_key_color'
            },
            'YAML Values': {
                'scopes': 'source.yaml meta.string.yaml string.unquoted.plain.out.yaml,source.yaml meta.string.yaml string.quoted.single.yaml, source.yaml meta.string.yaml string.quoted.double.yaml',
                'intellij_attrs': ['YAML_SCALAR_VALUE'],
                'variable': 'yaml_value_color'
            },
            'XML/HTML Tags': {
                'scopes': 'meta.tag, entity.name.tag, entity.name.tag.html, entity.name.tag.xml, entity.other.attribute-name, entity.other.attribute-name.html, entity.other.attribute-name.xml, string.quoted.double.xml, string.quoted.single.xml, string.quoted.double.html, string.quoted.single.html, punctuation.definition.tag, punctuation.definition.tag.html, punctuation.definition.tag.xml, meta.tag.preprocessor.xml, meta.tag.sgml, constant.character.entity.html, constant.character.entity.xml, punctuation.definition.entity.html, punctuation.definition.entity.xml, meta.tag.inline, meta.tag.block, meta.tag.other',
                'intellij_attrs': ['HTML_TAG', 'HTML_ATTRIBUTE_NAME', 'HTML_ENTITY_REFERENCE', 'HTML_CUSTOM_TAG_NAME'],
                'variable': 'tag_color'
            },
            'Annotations': {
                'scopes': 'variable.annotation, punctuation.definition.annotation, meta.annotation, storage.type.annotation, entity.name.function.annotation, keyword.other.annotation, support.type.annotation, meta.declaration.annotation, punctuation.definition.annotation.java, storage.modifier.annotation, entity.other.attribute-name.annotation',
                'intellij_attrs': ['DEFAULT_METADATA', 'ANNOTATION_ATTRIBUTE_NAME_ATTRIBUTES', 'ANNOTATION_NAME_ATTRIBUTES', 'PY.ANNOTATION'],
                'variable': 'annotation_color'
            },
            'Markup/Markdown': {
                'scopes': 'markup.heading, markup.heading.1, markup.heading.2, markup.heading.3, markup.heading.4, markup.heading.5, markup.heading.6, markup.raw.inline, markup.raw.block, markup.underline.link, markup.bold, markup.italic, string.other.link.destination, punctuation.definition.heading.markdown, punctuation.definition.bold.markdown, punctuation.definition.italic.markdown',
                'intellij_attrs': ['MARKDOWN_HEADER_LEVEL_1', 'MARKDOWN_HEADER_LEVEL_2', 'MARKDOWN_HEADER_LEVEL_3', 'MARKDOWN_HEADER_LEVEL_4', 'MARKDOWN_HEADER_LEVEL_5', 'MARKDOWN_HEADER_LEVEL_6', 'MARKDOWN_CODE_SPAN', 'MARKDOWN_CODE_BLOCK', 'MARKDOWN_LINK_TEXT', 'MARKDOWN_LINK_DESTINATION'],
                'variable': 'markup_color'
            },
            'CSS Selectors': {
                'scopes': 'entity.other.attribute-name.class.css, entity.other.attribute-name.id.css, entity.other.attribute-name.pseudo-class.css, entity.other.attribute-name.pseudo-element.css, support.type.property-name.css',
                'intellij_attrs': ['CSS.CLASS_NAME', 'CSS.ATTRIBUTE_NAME'],
                'variable': 'css_selector_color'
            },
            'RegExp': {
                'scopes': 'string.regexp, constant.character.character-class.regexp, constant.character.escape.regexp, keyword.operator.quantifier.regexp, punctuation.section.group.regexp, punctuation.section.character-class.regexp',
                'intellij_attrs': ['REGEXP.CHARACTER', 'REGEXP.CHAR_CLASS', 'REGEXP.ESC_CHARACTER'],
                'variable': 'regexp_color'
            },
            'Errors/Invalid': {
                'scopes': 'invalid, invalid.illegal, invalid.deprecated, invalid.illegal.bad-character, invalid.deprecated.trailing-whitespace',
                'intellij_attrs': ['ERRORS_ATTRIBUTES', 'BAD_CHARACTER', 'GENERIC_SERVER_ERROR_OR_WARNING', 'DEPRECATED_ATTRIBUTES', 'DEFAULT_INVALID_STRING_ESCAPE'],
                'variable': 'error_color'
            },
            'Documentation': {
                'scopes': 'comment.documentation, keyword.other.documentation, variable.parameter.documentation, markup.other.documentation',
                'intellij_attrs': ['DEFAULT_DOC_COMMENT_TAG', 'DEFAULT_DOC_COMMENT_TAG_VALUE', 'DEFAULT_DOC_MARKUP'],
                'variable': 'doc_color'
            }
        }

        # Create reverse mapping for quick lookup
        self.attribute_to_group = {}
        for group_name, group_data in self.semantic_groups.items():
            for attr in group_data['intellij_attrs']:
                self.attribute_to_group[attr] = group_name

        # Global theme settings mapping (supports both string and list values)
        self.global_color_mapping = {
            'BACKGROUND': 'background',
            'FOREGROUND': ['foreground', 'find_highlight_foreground'],
            'CARET_COLOR': 'caret',
            'CARET_ROW_COLOR': ['line_highlight', 'active_guide'],
            'SELECTION_BACKGROUND': ['selection', 'inactive_selection', "find_highlight"],
            'SELECTION_FOREGROUND': 'selection_foreground',
            'LINE_NUMBERS_COLOR': ['gutter_foreground'],
            'GUTTER_BACKGROUND': 'gutter_background',
            'LINE_DIFF_ADDED': 'line_diff_added',
            'LINE_DIFF_MODIFIED': 'line_diff_modified',
            'LINE_DIFF_DELETED': 'line_diff_deleted',
        }

    def normalize_color(self, color: str) -> str:
        """Convert color format from IntelliJ to Sublime (add # prefix if missing)."""
        if not color:
            return color

        color = color.strip()
        if not color.startswith('#') and len(color) in [3, 6, 8]:
            color = '#' + color

        return color

    def parse_intellij_theme(self, file_path: str) -> Tuple[Dict, Dict, str]:
        """Parse IntelliJ theme file and extract colors, attributes, and theme name."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            theme_name = root.get('name', 'Converted Theme')

            # Parse colors section
            colors = {}
            colors_section = root.find('colors')
            if colors_section is not None:
                for option in colors_section.findall('option'):
                    name = option.get('name')
                    value = option.get('value')
                    if name and value:
                        colors[name] = self.normalize_color(value)

            # Parse attributes section
            attributes = {}
            attributes_section = root.find('attributes')
            if attributes_section is not None:
                for option in attributes_section.findall('option'):
                    name = option.get('name')
                    if name:
                        attr_dict = {}

                        # Check if it uses baseAttributes
                        base_attrs = option.get('baseAttributes')
                        if base_attrs:
                            attr_dict['baseAttributes'] = base_attrs

                        # Parse value section
                        value_section = option.find('value')
                        if value_section is not None:
                            for value_option in value_section.findall('option'):
                                attr_name = value_option.get('name')
                                attr_value = value_option.get('value')
                                if attr_name and attr_value:
                                    if attr_name in ['FOREGROUND', 'BACKGROUND', 'EFFECT_COLOR']:
                                        attr_value = self.normalize_color(attr_value)
                                    attr_dict[attr_name] = attr_value

                        if attr_dict:
                            attributes[name] = attr_dict

            return colors, attributes, theme_name

        except ET.ParseError as e:
            raise ValueError(f"Error parsing IntelliJ theme file: {e}")
        except Exception as e:
            raise ValueError(f"Error reading theme file: {e}")

    def create_sublime_json_theme(self, colors: Dict, attributes: Dict, theme_name: str) -> Dict:
        """Create Sublime theme JSON structure from IntelliJ data using semantic grouping."""

        # Initialize the theme structure
        theme = {
            "name": theme_name,
            "author": "Converted from IntelliJ theme",
            "variables": {},
            "globals": {},
            "rules": []
        }

        # Extract base colors for variables
        base_colors = {}

        # Get foreground and background from TEXT or first available
        if 'TEXT' in attributes:
            default_text = attributes['TEXT']
            if 'FOREGROUND' in default_text:
                base_colors['foreground'] = default_text['FOREGROUND']
            if 'BACKGROUND' in default_text:
                base_colors['background'] = default_text['BACKGROUND']

        # Fallback to colors section if TEXT not available
        if 'BACKGROUND' in colors and 'background' not in base_colors:
            base_colors['background'] = colors['BACKGROUND']
        if 'FOREGROUND' in colors and 'foreground' not in base_colors:
            base_colors['foreground'] = colors['FOREGROUND']

        # Group attributes by semantic meaning
        group_colors = {}

        # Collect colors for each semantic group
        for attr_name, attr_data in attributes.items():
            group_name = self.attribute_to_group.get(attr_name)
            if group_name and attr_data:
                if group_name not in group_colors:
                    group_colors[group_name] = {'attrs': [], 'colors': {}}

                group_colors[group_name]['attrs'].append(attr_name)

                # Take the first non-empty color we find for this group
                # Prioritize certain attributes for color selection
                priority_attrs = ['DEFAULT_KEYWORD', 'DEFAULT_STRING', 'DEFAULT_FUNCTION_DECLARATION',
                                'DEFAULT_IDENTIFIER', 'DEFAULT_COMMENT', 'DEFAULT_CONSTANT']

                # Handle colors with priority logic
                if attr_name in priority_attrs or not group_colors[group_name]['colors']:
                    if 'FOREGROUND' in attr_data:
                        group_colors[group_name]['colors']['foreground'] = attr_data['FOREGROUND']
                    if 'BACKGROUND' in attr_data:
                        group_colors[group_name]['colors']['background'] = attr_data['BACKGROUND']


        # Create variables section
        variables = {}

        # Add permanent color palette variables based on theme brightness
        light_theme_colors = {
            "--bluish": "#063FDB",
            "--cyanish": "#4f8787",
            "--greenish": "#B8BB26",
            "--orangish": "#F78D8C",
            "--pinkish": "#D3859A",
            "--purplish": "#e5bb00",
            "--redish": "#af483c",
            "--yellowish": "#B28C00"
        }

        dark_theme_colors = {
            "--bluish": "#84a498",
            "--cyanish": "#8ec07b",
            "--greenish": "#b8bb26",
            "--orangish": "#ebdbb2",
            "--pinkish": "#d3859a",
            "--purplish": "#ebdbb2",
            "--redish": "#dd7b70",
            "--yellowish": "#fabd2f"
        }

        # Determine if theme is light or dark based on background color brightness
        is_light_theme = True  # Default to light
        if 'background' in base_colors:
            bg_color = base_colors['background'].lstrip('#')
            if len(bg_color) == 6:
                # Calculate perceived brightness using relative luminance
                r = int(bg_color[0:2], 16) / 255
                g = int(bg_color[2:4], 16) / 255
                b = int(bg_color[4:6], 16) / 255
                # Apply gamma correction and calculate luminance
                r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
                g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
                b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                is_light_theme = luminance > 0.5

        # Use appropriate color palette
        chosen_colors = light_theme_colors if is_light_theme else dark_theme_colors
        variables.update(chosen_colors)

        # Add base colors as variables
        if 'foreground' in base_colors:
            variables['textcolor'] = base_colors['foreground']
        if 'background' in base_colors:
            variables['background'] = base_colors['background']

        # Add fallback colors for JSON and YAML keys (not values) if they don't have specific colors
        key_fallback_groups = ['JSON Keys', 'YAML Keys']
        foreground_fallback = base_colors.get('foreground', variables.get('textcolor', '#000000'))

        for fallback_group in key_fallback_groups:
            if fallback_group in self.semantic_groups:
                if fallback_group not in group_colors or not group_colors[fallback_group]['colors']:
                    # Create the group with fallback foreground color
                    if fallback_group not in group_colors:
                        group_colors[fallback_group] = {'attrs': [], 'colors': {}, 'font_style': None}
                    group_colors[fallback_group]['colors']['foreground'] = foreground_fallback

        # Add group colors as variables
        for group_name, group_info in group_colors.items():
            if group_name in self.semantic_groups and group_info['colors']:
                group_data = self.semantic_groups[group_name]
                var_name = group_data['variable']

                if 'foreground' in group_info['colors']:
                    variables[var_name] = group_info['colors']['foreground']

        theme['variables'] = variables

        # Create globals section
        globals_dict = {}

        # Map IntelliJ global colors to Sublime globals (handle both string and list mappings)
        for intellij_color, sublime_keys in self.global_color_mapping.items():
            if intellij_color in colors:
                color_value = colors[intellij_color]
                if isinstance(sublime_keys, list):
                    # Apply the same color to multiple Sublime globals
                    for sublime_key in sublime_keys:
                        globals_dict[sublime_key] = color_value
                else:
                    # Single mapping
                    globals_dict[sublime_keys] = color_value

        # Add base colors if not already set
        if 'background' not in globals_dict and 'background' in base_colors:
            globals_dict['background'] = base_colors['background']
        if 'foreground' not in globals_dict and 'foreground' in base_colors:
            globals_dict['foreground'] = base_colors['foreground']
        # Also set find_highlight_foreground to match foreground if not already set
        if 'find_highlight_foreground' not in globals_dict and 'foreground' in base_colors:
            globals_dict['find_highlight_foreground'] = base_colors['foreground']

        # Add some default settings if not present
        if 'caret' not in globals_dict:
            globals_dict['caret'] = variables.get('textcolor', '#000000')
        if 'selection' not in globals_dict:
            # Create a lighter version of background for selection
            bg = variables.get('background', '#ffffff')
            if bg.startswith('#'):
                # Simple alpha blend for selection
                globals_dict['selection'] = bg + '40'  # Add alpha

        theme['globals'] = globals_dict

        # Create rules section
        rules = []

        # Create theme entries for each semantic group with colors
        for group_name, group_info in group_colors.items():
            if group_name in self.semantic_groups and group_info['colors']:
                group_data = self.semantic_groups[group_name]
                var_name = group_data['variable']

                rule = {
                    "name": group_name,
                    "scope": group_data['scopes']
                }

                # Use variable reference if available, otherwise use direct color
                if var_name in variables:
                    rule['foreground'] = f'var({var_name})'
                elif 'foreground' in group_info['colors']:
                    rule['foreground'] = group_info['colors']['foreground']

                if 'background' in group_info['colors']:
                    rule['background'] = group_info['colors']['background']

                rules.append(rule)

        # Handle any unmapped attributes individually
        for attr_name, attr_data in attributes.items():
            if attr_name not in self.attribute_to_group and attr_data:
                rule = {
                    "name": attr_name.replace('_', ' ').title(),
                    "scope": f"source.{attr_name.lower().replace('_', '.')}"
                }

                if 'FOREGROUND' in attr_data:
                    rule['foreground'] = attr_data['FOREGROUND']
                if 'BACKGROUND' in attr_data:
                    rule['background'] = attr_data['BACKGROUND']

                rules.append(rule)

        # Add bracket highlighter rule using SELECTION_BACKGROUND color
        if 'SELECTION_BACKGROUND' in colors:
            bracket_rule = {
                "scope": "brackethighlighter",
                "background": colors['SELECTION_BACKGROUND']
            }
            rules.append(bracket_rule)

        theme['rules'] = rules
        return theme


    def convert(self, input_file: str, output_file: str) -> None:
        """Convert IntelliJ theme to Sublime JSON theme."""
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        print(f"Converting {input_file} to {output_file}...")

        # Parse IntelliJ theme
        colors, attributes, theme_name = self.parse_intellij_theme(input_file)

        print(f"Found {len(colors)} colors and {len(attributes)} attributes")
        print(f"Theme name: {theme_name}")

        # Create Sublime theme JSON structure
        theme_json = self.create_sublime_json_theme(colors, attributes, theme_name)

        # Write output file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(theme_json, f, indent=4, ensure_ascii=False)

        print(f"✅ Successfully converted theme to {output_file}")
        print(f"📊 Generated {len(theme_json['variables'])} variables and {len(theme_json['rules'])} rules")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Convert IntelliJ IDEA theme files to Sublime Text modern JSON format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python intellij_to_sublime_json.py theme.icls theme.sublime-color-scheme
  python intellij_to_sublime_json.py /path/to/monokai.icls /path/to/monokai.sublime-color-scheme
        '''
    )

    parser.add_argument('input', help='Input IntelliJ theme file (.icls or .xml)')
    parser.add_argument('output', help='Output Sublime theme file (.sublime-color-scheme)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    converter = IntelliJToSublimeJSONConverter()

    try:
        converter.convert(args.input, args.output)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
