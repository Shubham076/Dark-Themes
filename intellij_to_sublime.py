#!/usr/bin/env python3
"""
IntelliJ to Sublime Theme Converter

This script converts IntelliJ IDEA theme files (.xml) to Sublime Text theme files (.tmTheme).
It parses the IntelliJ scheme format and maps the colors and attributes to Sublime's plist format.

Usage:
    python theme_converter.py input_theme.xml output_theme.tmTheme
"""

import xml.etree.ElementTree as ET
import argparse
import sys
import os
from typing import Dict, List, Optional, Tuple


class IntelliJToSublimeConverter:
    """Converts IntelliJ themes to Sublime Text format."""

    def __init__(self):
        # Comprehensive mapping from IntelliJ attributes to grouped Sublime scopes
        # Following the semantic grouping approach used in real Sublime themes
        self.semantic_groups = {
            'Keyword': {
                'scopes': 'keyword,keyword.other,keyword.control,variable.language.class,source.yaml meta.mapping.key.yaml meta.string.yaml string.unquoted.plain.out.yaml,storage.modifier',
                'intellij_attrs': ['DEFAULT_KEYWORD', 'CUSTOM_KEYWORD1_ATTRIBUTES', 'CUSTOM_KEYWORD2_ATTRIBUTES', 'CUSTOM_KEYWORD3_ATTRIBUTES', 'CUSTOM_KEYWORD4_ATTRIBUTES']
            },
            'Storage': {
                'scopes': 'storage,storage.type,storage.type.builtin,storage.modifier,meta.namespace,source meta.function.declaration meta.type storage.type support.type.builtin,source meta.function.declaration storage.type support.type.builtin,meta.function.declaration variable.other,support.type.builtin,meta.function.declaration storage.type,meta.block storage.type,variable.namespace,entity.name,support.class,entity.name.type,entity.name.class',
                'intellij_attrs': ['DEFAULT_CLASS_NAME', 'DEFAULT_CLASS_REFERENCE', 'DEFAULT_INTERFACE_NAME', 'DEFAULT_METADATA', 'GO_PACKAGE', 'PY.ANNOTATION']
            },
            'String': {
                'scopes': 'string,string.quoted,string.quoted.single,string.quoted.double,string.quoted.triple,string.unquoted,source meta.string.go string.quoted.double constant.other.placeholder,meta.string.go string.quoted.single constant.other.placeholder,string.template,string.regexp,string.other.link',
                'intellij_attrs': ['DEFAULT_STRING', 'JS.REGEXP', 'BASH.HERE_DOC_START', 'BASH.HERE_DOC_END']
            },
            'Functions': {
                'scopes': 'entity.name.function,variable.function,support.function,meta.function-call,keyword.other.special-method,support.function.builtin',
                'intellij_attrs': ['DEFAULT_FUNCTION_DECLARATION', 'DEFAULT_FUNCTION_CALL', 'DEFAULT_STATIC_METHOD', 'BASH.EXTERNAL_COMMAND', 'JS.GLOBAL_FUNCTION', 'PY.BUILTIN_NAME', 'CSS.FUNCTION']
            },
            'Variables': {
                'scopes': 'variable,variable.other,variable.other.readwrite,variable.other.member,variable.other.global,variable.other.local,variable.other.constant,meta.block variable.other,variable.language.anonymous,meta.function.declaration variable.parameter,variable.other.readwrite.declaration,keyword.operator.logical,keyword.operator.assignment,keyword.operator.comparison,punctuation.section,punctuation.section.parens,constant.language,constant.boolean,variable.language.this,variable.parameter,source.yaml meta.string.yaml string.unquoted.plain.out.yaml',
                'intellij_attrs': ['DEFAULT_IDENTIFIER', 'DEFAULT_PARAMETER', 'DEFAULT_LOCAL_VARIABLE', 'DEFAULT_INSTANCE_FIELD', 'DEFAULT_STATIC_FIELD', 'DEFAULT_GLOBAL_VARIABLE', 'DEFAULT_REASSIGNED_LOCAL_VARIABLE', 'DEFAULT_REASSIGNED_PARAMETER', 'JS.GLOBAL_VARIABLE', 'PY.SELF_PARAMETER', 'PY.KEYWORD_ARGUMENT', 'GO_METHOD_RECEIVER']
            },
            'Constants': {
                'scopes': 'constant,constant.numeric,constant.language,constant.character,constant.character.escape,constant.other,variable.other.constant,support.constant,keyword.other.unit',
                'intellij_attrs': ['DEFAULT_CONSTANT', 'DEFAULT_NUMBER', 'DEFAULT_VALID_STRING_ESCAPE', 'CSS.UNIT', 'CSS.COLOR']
            },
            'Comments': {
                'scopes': 'comment,comment.line,comment.block,comment.documentation,punctuation.definition.comment,comment.line.shebang',
                'intellij_attrs': ['DEFAULT_COMMENT', 'DEFAULT_LINE_COMMENT', 'DEFAULT_BLOCK_COMMENT', 'DEFAULT_DOC_COMMENT', 'BASH.SHEBANG']
            },
            'Operators': {
                'scopes': 'keyword.operator,keyword.operator.logical,keyword.operator.comparison,keyword.operator.assignment,keyword.operator.arithmetic,keyword.operator.regexp',
                'intellij_attrs': ['DEFAULT_OPERATION_SIGN', 'CSS.OPERATORS', 'REGEXP.META', 'REGEXP.QUANTIFIER']
            },
            'Punctuation': {
                'scopes': 'punctuation,punctuation.separator,punctuation.separator.comma,punctuation.terminator,punctuation.terminator.semicolon,punctuation.section,punctuation.section.braces,punctuation.section.brackets,punctuation.section.parens,punctuation.accessor.dot,punctuation.separator.colon,punctuation.definition',
                'intellij_attrs': ['DEFAULT_BRACES', 'DEFAULT_BRACKETS', 'DEFAULT_PARENTHS', 'DEFAULT_COMMA', 'DEFAULT_DOT', 'DEFAULT_SEMICOLON', 'DEFAULT_COLON', 'REGEXP.PARENTHS', 'REGEXP.BRACKETS', 'REGEXP.BRACES']
            },
            'JSON': {
                'scopes': 'source.json meta.structure.dictionary.json support.type.property-name.json,source.json meta.structure.dictionary.json meta.structure.dictionary.value.json meta.structure.dictionary.json support.type.property-name.json,meta.object-literal.key.json,string.quoted.double.json,punctuation.support.type.property-name.begin.json,punctuation.support.type.property-name.end.json,punctuation.separator.dictionary.key-value.json',
                'intellij_attrs': ['JSON.KEYWORD', 'JSON.PROPERTY_KEY']
            },
            'YAML': {
                'scopes': 'source.yaml meta.mapping.key.yaml string.unquoted.plain.out.yaml,source.yaml meta.mapping.value.yaml string.unquoted.plain.out.yaml,punctuation.definition.block.sequence.item.yaml,punctuation.definition.mapping.key.yaml,punctuation.definition.mapping.value.yaml',
                'intellij_attrs': []  # Will be mapped generically if found
            },
            'XML_HTML_Tags': {
                'scopes': 'meta.tag,entity.name.tag,entity.name.tag.html,entity.name.tag.xml,entity.other.attribute-name,entity.other.attribute-name.html,entity.other.attribute-name.xml,string.quoted.double.xml,string.quoted.single.xml,string.quoted.double.html,string.quoted.single.html,punctuation.definition.tag,punctuation.definition.tag.html,punctuation.definition.tag.xml,meta.tag.preprocessor.xml,meta.tag.sgml,constant.character.entity.html,constant.character.entity.xml,punctuation.definition.entity.html,punctuation.definition.entity.xml,meta.tag.inline,meta.tag.block,meta.tag.other',
                'intellij_attrs': ['HTML_TAG', 'HTML_ATTRIBUTE_NAME', 'HTML_ENTITY_REFERENCE', 'HTML_CUSTOM_TAG_NAME']
            },
            'XML_HTML_Text': {
                'scopes': 'text.xml,text.html,text.html.basic,source.xml,source.html',
                'intellij_attrs': []  # Will use variable color as fallback
            },
            'Annotations': {
                'scopes': 'variable.annotation,punctuation.definition.annotation,meta.annotation,storage.type.annotation,entity.name.function.annotation,keyword.other.annotation,support.type.annotation,meta.declaration.annotation,punctuation.definition.annotation.java,storage.modifier.annotation,entity.other.attribute-name.annotation',
                'intellij_attrs': ['DEFAULT_METADATA', 'ANNOTATION_ATTRIBUTE_NAME_ATTRIBUTES', 'ANNOTATION_NAME_ATTRIBUTES', 'PY.ANNOTATION']
            },
            'Markup_Markdown': {
                'scopes': 'markup.heading,markup.heading.1,markup.heading.2,markup.heading.3,markup.heading.4,markup.heading.5,markup.heading.6,markup.raw.inline,markup.raw.block,markup.underline.link,markup.bold,markup.italic,string.other.link.destination,punctuation.definition.heading.markdown,punctuation.definition.bold.markdown,punctuation.definition.italic.markdown',
                'intellij_attrs': ['MARKDOWN_HEADER_LEVEL_1', 'MARKDOWN_HEADER_LEVEL_2', 'MARKDOWN_HEADER_LEVEL_3', 'MARKDOWN_HEADER_LEVEL_4', 'MARKDOWN_HEADER_LEVEL_5', 'MARKDOWN_HEADER_LEVEL_6', 'MARKDOWN_CODE_SPAN', 'MARKDOWN_CODE_BLOCK', 'MARKDOWN_LINK_TEXT', 'MARKDOWN_LINK_DESTINATION']
            },
            'CSS_Selectors': {
                'scopes': 'entity.other.attribute-name.class.css,entity.other.attribute-name.id.css,entity.other.attribute-name.pseudo-class.css,entity.other.attribute-name.pseudo-element.css,support.type.property-name.css',
                'intellij_attrs': ['CSS.CLASS_NAME', 'CSS.ATTRIBUTE_NAME']
            },
            'RegExp': {
                'scopes': 'string.regexp,constant.character.character-class.regexp,constant.character.escape.regexp,keyword.operator.quantifier.regexp,punctuation.section.group.regexp,punctuation.section.character-class.regexp',
                'intellij_attrs': ['REGEXP.CHARACTER', 'REGEXP.CHAR_CLASS', 'REGEXP.ESC_CHARACTER']
            },
            'Errors_Invalid': {
                'scopes': 'invalid,invalid.illegal,invalid.deprecated,invalid.illegal.bad-character,invalid.deprecated.trailing-whitespace',
                'intellij_attrs': ['ERRORS_ATTRIBUTES', 'BAD_CHARACTER', 'GENERIC_SERVER_ERROR_OR_WARNING', 'DEPRECATED_ATTRIBUTES', 'DEFAULT_INVALID_STRING_ESCAPE']
            },
            'Documentation': {
                'scopes': 'comment.documentation,keyword.other.documentation,variable.parameter.documentation,markup.other.documentation',
                'intellij_attrs': ['DEFAULT_DOC_COMMENT_TAG', 'DEFAULT_DOC_COMMENT_TAG_VALUE', 'DEFAULT_DOC_MARKUP']
            }
        }

        # Create reverse mapping for quick lookup
        self.attribute_to_group = {}
        for group_name, group_data in self.semantic_groups.items():
            for attr in group_data['intellij_attrs']:
                self.attribute_to_group[attr] = group_name

        # Global theme settings mapping
        self.global_color_mapping = {
            'BACKGROUND': 'background',
            'FOREGROUND': 'foreground',
            'CARET_COLOR': 'caret',
            'CARET_ROW_COLOR': 'lineHighlight',
            'SELECTION_BACKGROUND': 'selection',
            'SELECTION_FOREGROUND': 'selectionForeground',
            'LINE_NUMBERS_COLOR': 'gutterForeground',
            'GUTTER_BACKGROUND': 'gutterBackground',
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

    def create_sublime_theme(self, colors: Dict, attributes: Dict, theme_name: str) -> str:
        """Create Sublime theme XML content from IntelliJ data using semantic grouping."""

        # Start building the theme
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
            '<plist version="1.0">',
            '<dict>',
            '\t<key>colorSpaceName</key>',
            '\t<string>sRGB</string>',
            '\t<key>comment</key>',
            f'\t<string>Converted from IntelliJ theme</string>',
            '\t<key>name</key>',
            f'\t<string>{theme_name}</string>',
            '\t<key>settings</key>',
            '\t<array>',
        ]

        # Add global settings using DEFAULT_TEXT colors
        lines.append('\t\t<dict>')
        lines.append('\t\t\t<key>settings</key>')
        lines.append('\t\t\t<dict>')

        for intellij_color, sublime_key in self.global_color_mapping.items():
            if intellij_color in colors:
                color_value = colors[intellij_color]
                lines.append(f'\t\t\t\t<key>{sublime_key}</key>')
                lines.append(f'\t\t\t\t<string>{color_value}</string>')

        # Add foreground and background from DEFAULT_TEXT
        if 'TEXT' in attributes:
            default_text = attributes['TEXT']
            if 'FOREGROUND' in default_text:
                lines.append('\t\t\t\t<key>foreground</key>')
                lines.append(f'\t\t\t\t<string>{default_text["FOREGROUND"]}</string>')
            if 'BACKGROUND' in default_text:
                lines.append('\t\t\t\t<key>background</key>')
                lines.append(f'\t\t\t\t<string>{default_text["BACKGROUND"]}</string>')

        lines.append('\t\t\t</dict>')
        lines.append('\t\t</dict>')

        # Group attributes by semantic meaning and create comprehensive scope rules
        group_colors = {}

        # First, collect colors for each semantic group
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

                if attr_name in priority_attrs or not group_colors[group_name]['colors']:
                    if 'FOREGROUND' in attr_data:
                        group_colors[group_name]['colors']['foreground'] = attr_data['FOREGROUND']
                    if 'BACKGROUND' in attr_data:
                        group_colors[group_name]['colors']['background'] = attr_data['BACKGROUND']
                    if 'FONT_TYPE' in attr_data:
                        font_style = self.map_font_type(attr_data['FONT_TYPE'])
                        if font_style:
                            group_colors[group_name]['colors']['fontStyle'] = font_style

        # Create theme entries for each semantic group with colors
        for group_name, group_info in group_colors.items():
            if group_name in self.semantic_groups and group_info['colors']:
                group_data = self.semantic_groups[group_name]

                lines.append('\t\t<dict>')
                lines.append('\t\t\t<key>name</key>')
                lines.append(f'\t\t\t<string>{group_name.replace("_", " ")}</string>')
                lines.append('\t\t\t<key>scope</key>')
                lines.append(f'\t\t\t<string>{group_data["scopes"]}</string>')
                lines.append('\t\t\t<key>settings</key>')
                lines.append('\t\t\t<dict>')

                for setting_key, setting_value in group_info['colors'].items():
                    lines.append(f'\t\t\t\t<key>{setting_key}</key>')
                    lines.append(f'\t\t\t\t<string>{setting_value}</string>')

                lines.append('\t\t\t</dict>')
                lines.append('\t\t</dict>')

        # Handle any unmapped attributes individually
        for attr_name, attr_data in attributes.items():
            if attr_name not in self.attribute_to_group and attr_data:
                # Generate a generic scope for unmapped attributes
                scope = f"source.{attr_name.lower().replace('_', '.')}"

                lines.append('\t\t<dict>')
                lines.append('\t\t\t<key>name</key>')
                lines.append(f'\t\t\t<string>{attr_name.replace("_", " ").title()}</string>')
                lines.append('\t\t\t<key>scope</key>')
                lines.append(f'\t\t\t<string>{scope}</string>')
                lines.append('\t\t\t<key>settings</key>')
                lines.append('\t\t\t<dict>')

                # Map IntelliJ attributes to Sublime settings
                if 'FOREGROUND' in attr_data:
                    lines.append('\t\t\t\t<key>foreground</key>')
                    lines.append(f'\t\t\t\t<string>{attr_data["FOREGROUND"]}</string>')

                if 'BACKGROUND' in attr_data:
                    lines.append('\t\t\t\t<key>background</key>')
                    lines.append(f'\t\t\t\t<string>{attr_data["BACKGROUND"]}</string>')

                # Handle font styles
                font_type = attr_data.get('FONT_TYPE')
                if font_type:
                    font_style = self.map_font_type(font_type)
                    if font_style:
                        lines.append('\t\t\t\t<key>fontStyle</key>')
                        lines.append(f'\t\t\t\t<string>{font_style}</string>')

                lines.append('\t\t\t</dict>')
                lines.append('\t\t</dict>')

        # Close the theme structure
        lines.extend([
            '\t</array>',
            '\t<key>uuid</key>',
            f'\t<string>{self.generate_uuid()}</string>',
            '</dict>',
            '</plist>'
        ])

        return '\n'.join(lines)

    def map_font_type(self, font_type: str) -> Optional[str]:
        """Map IntelliJ font type to Sublime font style."""
        font_type_mapping = {
            '1': 'bold',
            '2': 'italic',
            '3': 'bold italic',
        }
        return font_type_mapping.get(font_type)

    def generate_uuid(self) -> str:
        """Generate a simple UUID for the theme."""
        import uuid
        return str(uuid.uuid4())

    def convert(self, input_file: str, output_file: str) -> None:
        """Convert IntelliJ theme to Sublime theme."""
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        print(f"Converting {input_file} to {output_file}...")

        # Parse IntelliJ theme
        colors, attributes, theme_name = self.parse_intellij_theme(input_file)

        print(f"Found {len(colors)} colors and {len(attributes)} attributes")
        print(f"Theme name: {theme_name}")

        # Create Sublime theme content
        sublime_content = self.create_sublime_theme(colors, attributes, theme_name)

        # Write output file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sublime_content)

        print(f"✅ Successfully converted theme to {output_file}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Convert IntelliJ IDEA theme files to Sublime Text format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python theme_converter.py theme.xml theme.tmTheme
  python theme_converter.py /path/to/monokai.xml /path/to/monokai_sublime.tmTheme
        '''
    )

    parser.add_argument('input', help='Input IntelliJ theme file (.xml)')
    parser.add_argument('output', help='Output Sublime theme file (.tmTheme)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    converter = IntelliJToSublimeConverter()

    try:
        converter.convert(args.input, args.output)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
