#!/usr/bin/env python3
"""
IntelliJ to Sublime Theme Converter (JSON Format)

This script converts IntelliJ IDEA theme files (.icls/.xml) to Sublime Text's modern
JSON theme format (.sublime-color-scheme).
It parses the IntelliJ scheme format and maps the colors and attributes to Sublime's
modern JSON format with variables, globals, and rules.

Usage:
    python intellij_to_sublime_json.py input_theme.icls output_theme.sublime-color-scheme


popup's uses css
<div class="mdpopups">
    <div class="bracket-highlighter"> // WRAPPER_CLASS given by plugins developer
        <div class="admonition panel-error">
            <p class="admonition-title">Matching bracket could not be found!</p>
            <ul>
                <li>...</li>
            </ul>
            <p><a href="100">(Match brackets without threshold)</a></p>
        </div>
    </div>
</div>
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
                'intellij_attrs': ['DEFAULT_KEYWORD'],
                'variable': 'keyword_color'
            },
            'Storage Types': {
                'scopes': 'storage, storage.type, storage.type.builtin, storage.modifier, meta.namespace, entity.name, support.class, entity.name.type, entity.name.class',
                'intellij_attrs': ['DEFAULT_CLASS_NAME'],
                'variable': 'storage_color'
            },
            'Strings': {
                'scopes': 'string, string.quoted, string.quoted.single, string.quoted.double, string.quoted.triple, string.unquoted, string.template, string.regexp, string.other.link, variable.annotation',
                'intellij_attrs': ['DEFAULT_STRING'],
                'variable': 'string_color'
            },
            'Functions': {
                'scopes': 'entity.name.function, variable.function, support.function, meta.function-call, keyword.other.special-method, support.function.builtin',
                'intellij_attrs': ['DEFAULT_FUNCTION_DECLARATION', ],
                'variable': 'function_color'
            },
            'Variables': {
                'scopes': 'variable, variable.other, variable.other.readwrite, variable.other.member, variable.other.global, variable.other.local, variable.other.constant, meta.block variable.other, variable.language.anonymous, meta.function.declaration variable.parameter, variable.other.readwrite.declaration, variable.parameter',
                'intellij_attrs': ['DEFAULT_IDENTIFIER',],
                'variable': 'variable_color'
            },
            'Constants': {
                'scopes': 'constant, constant.numeric, constant.language, constant.character, constant.character.escape, constant.other, variable.other.constant, support.constant, keyword.other.unit',
                'intellij_attrs': ['DEFAULT_CONSTANT', 'DEFAULT_NUMBER'],
                'variable': 'constant_color'
            },
            'Comments': {
                'scopes': 'comment, comment.line, comment.block, comment.documentation, punctuation.definition.comment, comment.line.shebang',
                'intellij_attrs': ['DEFAULT_LINE_COMMENT'],
                'variable': 'comment_color'
            },
            'Operators': {
                'scopes': 'keyword.operator, keyword.operator.logical, keyword.operator.comparison, keyword.operator.assignment, keyword.operator.arithmetic, keyword.operator.regexp',
                'intellij_attrs': ['DEFAULT_OPERATION_SIGN'],
                'variable': 'operator_color'
            },
            'Punctuation': {
                'scopes': 'punctuation, punctuation.separator, punctuation.separator.comma, punctuation.terminator, punctuation.terminator.semicolon, punctuation.section, punctuation.section.braces, punctuation.section.brackets, punctuation.section.parens, punctuation.accessor.dot, punctuation.separator.colon, punctuation.definition',
                'intellij_attrs': ['DEFAULT_BRACKETS'],
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
                'intellij_attrs': ['HTML_TAG'],
                'variable': 'tag_color'
            },
            'Annotations': {
                'scopes': 'variable.annotation, punctuation.definition.annotation, meta.annotation, storage.type.annotation, entity.name.function.annotation, keyword.other.annotation, support.type.annotation, meta.declaration.annotation, punctuation.definition.annotation.java, storage.modifier.annotation, entity.other.attribute-name.annotation',
                'intellij_attrs': ['DEFAULT_METADATA'],
                'variable': 'annotation_color'
            },
            'Markup/Markdown': {
                'scopes': 'markup.heading, markup.heading.1, markup.heading.2, markup.heading.3, markup.heading.4, markup.heading.5, markup.heading.6, markup.raw.inline, markup.raw.block, markup.underline.link, markup.bold, markup.italic, string.other.link.destination, punctuation.definition.heading.markdown, punctuation.definition.bold.markdown, punctuation.definition.italic.markdown',
                'intellij_attrs': ['MARKDOWN_HEADER_LEVEL_1', 'MARKDOWN_HEADER_LEVEL_2', 'MARKDOWN_HEADER_LEVEL_3', 'MARKDOWN_HEADER_LEVEL_4', 'MARKDOWN_HEADER_LEVEL_5', 'MARKDOWN_HEADER_LEVEL_6', 'MARKDOWN_CODE_SPAN', 'MARKDOWN_CODE_BLOCK', 'MARKDOWN_LINK_TEXT', 'MARKDOWN_LINK_DESTINATION'],
                'variable': 'markup_color'
            },
            'CSS Selectors': {
                'scopes': 'entity.other.attribute-name.class.css, entity.other.attribute-name.id.css, entity.other.attribute-name.pseudo-class.css, entity.other.attribute-name.pseudo-element.css, support.type.property-name.css',
                'intellij_attrs': ['CSS.CLASS_NAME'],
                'variable': 'css_selector_color'
            },
            'RegExp': {
                'scopes': 'string.regexp, constant.character.character-class.regexp, constant.character.escape.regexp, keyword.operator.quantifier.regexp, punctuation.section.group.regexp, punctuation.section.character-class.regexp',
                'intellij_attrs': ['REGEXP.CHARACTER'],
                'variable': 'regexp_color'
            },
            'Errors/Invalid': {
                'scopes': 'invalid, invalid.illegal, invalid.deprecated, invalid.illegal.bad-character, invalid.deprecated.trailing-whitespace',
                'intellij_attrs': ['ERRORS_ATTRIBUTES'],
                'variable': 'error_color'
            },
            'Documentation': {
                'scopes': 'comment.documentation, keyword.other.documentation, variable.parameter.documentation, markup.other.documentation',
                'intellij_attrs': ['DEFAULT_DOC_COMMENT_TAG'],
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

    def json_to_css_variables(self, json_obj):
        css_vars = []

        # Start with the root selector
        css_vars.append(" html {")

        # Convert each key-value pair to a CSS variable
        for var_name, var_value in json_obj.items():
            # Make sure the variable name has -- prefix
            if not var_name.startswith('--'):
                var_name = f"--{var_name}"

            css_vars.append(f"  {var_name}: {var_value};")

        # Close the CSS rule
        css_vars.append("}")

        # Join with newlines
        return "\n".join(css_vars)

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
            "--bluish": "#343e5e",
            "--cyanish": "#316a6a",
            "--greenish": "#22863a",
            "--orangish": "#F78D8C",
            "--pinkish": "#D3859A",
            "--purplish": "#e5bb00",
            "--redish": "#9b362b",
            "--yellowish": "#B28C00"
        }

        dark_theme_colors = {
            "--cyanish": "#9acd87",
            "--bluish": "#85dacc",
            "--greenish": "#b8bb26",
            "--orangish": "#ebdbb2",
            "--pinkish": "#d3859a",
            "--purplish": "#ebdbb2",
            "--redish": "#dd7b70",
            "--yellowish": "#fabd2f"
        }

        git_diff_colors_light = {
            "inserted":"#BEE6BE" ,
            "deleted":"#e4bbb2" ,
            "modified":"#C2D8F2" ,
        }

        git_diff_colors_dark = {
            "inserted":"#334f40" ,
            "deleted":"#774F51" ,
            "modified":"#43607c" ,
        }

        popup_colors_light = {
            "popup_redish": "#cc6b61",
            "popup_yellowish": "#B28C00",
            "popup_greenish": "#BEE6BE",
            "popup_bluish": "#C2D8F2",
            "popup_cyanish": "#316a6a",
        }

        popup_colors_dark = {
            "popup_redish": "#ff6d62",
            "popup_bluish": "#43607c",
            "popup_greenish": "#334f40",
            "popup_yellowish": "#fabd2f",
            "popup_cyanish": "#9acd87",
        }

        generic_popup_background_light = "#fff1cc"


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

        # Create better popup backgrounds for contrast - opposite of main background
        main_bg = base_colors.get('background', '#ffffff')
        if is_light_theme:
            # popup_bg = "#e8eaec"
            # Light theme (light background) -> use dark popup background for contrast
            # Darken the background significantly for good contrast

            if main_bg.startswith('#') and len(main_bg) == 7:
                r = max(0, int(main_bg[1:3], 16) - 17)
                g = max(0, int(main_bg[3:5], 16) - 17)
                b = max(0, int(main_bg[5:7], 16) - 17)
                popup_bg = f"#{r:02x}{g:02x}{b:02x}"
            else:
                popup_bg = "#404040"  # Fallback dark color

        else:
            # Dark theme (dark background) -> use light popup background for contrast
            if main_bg.startswith('#') and len(main_bg) == 7:
                # Lighten the background significantly for good contrast
                r = min(255, int(main_bg[1:3], 16) + 20)
                g = min(255, int(main_bg[3:5], 16) + 20)
                b = min(255, int(main_bg[5:7], 16) + 20)
                popup_bg = f"#{r:02x}{g:02x}{b:02x}"
            else:
                popup_bg = "#c0c0c0"

        # Add popup background as a variable
        variables['popup_bg'] = popup_bg

        # Use appropriate color palette
        chosen_colors = light_theme_colors if is_light_theme else dark_theme_colors
        chosen_git_colors = git_diff_colors_light if is_light_theme else git_diff_colors_dark
        chosen_popup_colors = popup_colors_light if is_light_theme else popup_colors_dark
        generic_popup_bg = generic_popup_background_light if is_light_theme else popup_bg
        chosen_popup_colors["mdpopups_background"] = popup_bg
        chosen_popup_colors["popups_background"] = generic_popup_bg

        css_variables_string = self.json_to_css_variables(chosen_popup_colors)
        print(css_variables_string)

        variables.update(chosen_colors)
        variables.update(chosen_git_colors)
        # Add base colors as variables
        if 'foreground' in base_colors:
            variables['textcolor'] = base_colors['foreground']
        if 'background' in base_colors:
            variables['background'] = base_colors['background']

        # Add selection background as variable if available
        if 'SELECTION_BACKGROUND' in colors:
            variables['selection_background'] = colors['SELECTION_BACKGROUND']

        # Add fallback colors for JSON and YAML keys (not values) if they don't have specific colors
        key_fallback_groups = ['JSON Keys', 'YAML Keys']

        for fallback_group in key_fallback_groups:
            if fallback_group in self.semantic_groups:
                if fallback_group not in group_colors or not group_colors[fallback_group]['colors']:
                    # Create the group with fallback foreground color
                    if fallback_group not in group_colors:
                        group_colors[fallback_group] = {'attrs': [], 'colors': {}, 'font_style': None}
                    # Use actual color value, not variable reference for internal processing
                    group_colors[fallback_group]['colors']['foreground'] = variables.get('textcolor', '#000000')

        # Add group colors as variables
        for group_name, group_info in group_colors.items():
            if group_name in self.semantic_groups and group_info['colors']:
                group_data = self.semantic_groups[group_name]
                var_name = group_data['variable']

                if 'foreground' in group_info['colors']:
                    variables[var_name] = group_info['colors']['foreground']

        # Add additional variables for globals
        if 'CARET_ROW_COLOR' in colors:
            variables['line_highlight_color'] = colors['CARET_ROW_COLOR']
        if 'LINE_NUMBERS_COLOR' in colors:
            variables['gutter_foreground_color'] = colors['LINE_NUMBERS_COLOR']

        # Set variables after we've added all of them
        theme['variables'] = variables

        # Create globals section - simple direct assignment using variables
        globals_dict = {}
        globals_dict['background'] = 'var(background)'
        globals_dict['foreground'] = 'var(textcolor)'
        globals_dict['find_highlight_foreground'] = 'var(textcolor)'
        globals_dict['caret'] = 'var(textcolor)'
        globals_dict['line_highlight'] = 'var(line_highlight_color)' if 'line_highlight_color' in variables else 'var(background)'
        globals_dict['active_guide'] = 'var(line_highlight_color)' if 'line_highlight_color' in variables else 'var(background)'
        globals_dict['selection'] = 'var(selection_background)'
        globals_dict['inactive_selection'] = 'var(selection_background)'
        globals_dict['find_highlight'] = 'var(selection_background)'
        globals_dict['selection_foreground'] = 'var(textcolor)'
        globals_dict['gutter_foreground'] = 'var(gutter_foreground_color)' if 'gutter_foreground_color' in variables else 'var(textcolor)'
        globals_dict['gutter_background'] = 'var(background)'

        globals_dict["line_diff_width"] = "10"
        globals_dict["line_diff_added"] = "var(--greenish)"
        globals_dict["line_diff_modified"] = "var(selection_background)"
        globals_dict["line_diff_deleted"] = "var(--redish)"

        # popup_css = f"* {{--mdpopups-bg: {popup_bg}; --mdpopups-hl-bg: {popup_bg}; --mdpopups-hl-border: none;}} a {{text-decoration: none; color: var(--bluish);}}  .info {{--bluish: {popup_bg};}} .hints {{--bluish: {popup_bg};}} .errors {{--redish: {popup_bg};}} .warnings {{--yellowish: {popup_bg};}}"
        # popup_css = f"* {{--mdpopups-bg: {popup_bg}; --mdpopups-hl-bg: {popup_bg}; --mdpopups-hl-border: none;}} a {{text-decoration: none; color: var(--bluish);}}  .info {{--bluish: {popup_bg};}} .hints {{--bluish: {popup_bg};}} .errors {{--redish: {popup_bg};}} .warnings {{--yellowish: {popup_bg};}} .mdpopups .bracket-highlighter {{--redish: {popup_bg}; --bluish: {popup_bg}; --orangish: {popup_bg}; --greenish: {popup_bg}; --mdpopups-admon-error-accent: {popup_bg}; --mdpopups-admon-info-accent: {popup_bg}; --mdpopups-admon-warning-accent: {popup_bg}; --mdpopups-admon-success-accent: {popup_bg}; --mdpopups-admon-info-bg: {popup_bg}; --mdpopups-admon-warning-bg: {popup_bg}; --mdpopups-admon-warning-bg: {popup_bg}; --mdpopups-admon-success-bg: {popup_bg};  --mdpopups-admon-error-bg: {popup_bg}; --mdpopups-link: {link_color};}}"

        # popup_css = f"""
        # html, body {{--background: {chosen_linter_popup_colors}; border-radius: 2px;}}
        # .mdpopups {{--mdpopups-bg: {popup_bg}; --mdpopups-hl-bg: {popup_bg}; --mdpopups-hl-border: none; --mdpopups-link: {link_color};}}
        # a {{text-decoration: none; color: var(--cyanish);}}
        # .mdpopups .lsp_popup {{--redish: {popup_bg}; --greenish: {popup_bg}; --yellowish: {popup_bg};}}
        # .mdpopups .lsp_popup a {{color: var(--cyanish);}}
        # .mdpopups .bracket-highlighter .admonition.panel-error {{--mdpopups-admon-error-accent: {popup_bg}; --mdpopups-admon-info-accent: {popup_bg}; --mdpopups-admon-warning-accent: {popup_bg}; --mdpopups-admon-success-accent: {popup_bg};}}
        # .mdpopups .bracket-highlighter .admonition.panel-error .admonition-title {{--mdpopups-admon-error-accent: {chosen_git_colors["deleted"]}; --mdpopups-admon-info-accent: {chosen_git_colors["modified"]}; --mdpopups-admon-warning-accent: {chosen_colors['--yellowish']}; --mdpopups-admon-success-accent: {chosen_git_colors["inserted"]};}}
        # .mdpopups .bracket-highlighter {{ --mdpopups-admon-info-bg: {popup_bg}; --mdpopups-admon-warning-bg: {popup_bg}; --mdpopups-admon-warning-bg: {popup_bg}; --mdpopups-admon-success-bg: {popup_bg};  --mdpopups-admon-error-bg: {popup_bg}; --mdpopups-link: {link_color};}}"""


        popup_css = f"""
        {css_variables_string}
        html, body {{--background: var(--popups_background); border-radius: 2px;}}
        .mdpopups {{--mdpopups-bg: var(--mdpopups_background); --mdpopups-hl-bg: var(--mdpopups_background); --mdpopups-hl-border: none; --mdpopups-link: var(--popup_cyanish);}}
        a {{text-decoration: none; color: var(--popup_cyanish);}}
        .mdpopups .lsp_popup {{--redish: var(--popup_redish); --yellowish: var(--popup_redish); --greenish: var(--popup_greenish); }}
        .mdpopups .lsp_popup a {{color: var(--popup_cyanish);}}
        .mdpopups .bracket-highlighter .admonition.panel-error {{--mdpopups-admon-error-accent: var(--mdpopups_background); --mdpopups-admon-info-accent: var(--mdpopups_background); --mdpopups-admon-warning-accent: var(--mdpopups_background); --mdpopups-admon-success-accent: var(--mdpopups_background);}}
        .mdpopups .bracket-highlighter .admonition.panel-error .admonition-title {{--mdpopups-admon-error-accent: color(var(--popup_redish) alpha(0.25)); --mdpopups-admon-info-accent: color(var(--popup_cyanish) alpha(0.25)); --mdpopups-admon-warning-accent: color(var(--popup_yellowish) alpha(0.25)); --mdpopups-admon-success-accent: color(var(--popup_greenish) alpha(0.25));}}
        .mdpopups .bracket-highlighter {{ --mdpopups-admon-info-bg: var(--mdpopups_background); --mdpopups-admon-warning-bg: var(--mdpopups_background); --mdpopups-admon-warning-bg: var(--mdpopups_background); --mdpopups-admon-success-bg: var(--mdpopups_background);  --mdpopups-admon-error-bg: var(--mdpopups_background); --mdpopups-link: var(--cyanish);}}
        """


        globals_dict["popup_css"] = popup_css
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

        # Skip unmapped attributes to avoid noise in rules section

        # Add bracket highlighter rule using SELECTION_BACKGROUND color
        if 'SELECTION_BACKGROUND' in colors:
            bracket_rule = {
                "scope": "brackethighlighter",
                "background": "var(selection_background)"
            }
            rules.append(bracket_rule)

         # Add default region color rules based on theme brightness
        theme_background = variables.get('background', base_colors.get('background', '#ffffff'))

        # Create region rules with appropriate colors for light/dark themes
        region_rules = [
            {
                "name": "region red color",
                "scope": "region.redish",
                "background": "var(background)"
            },
            {
                "name": "region blue color",
                "scope": "region.bluish",
                "background": "var(background)"
            },
            {
                "scope": "debugger.selection",
                "background": "var(selection_background)"
            },
            {
                "name": "region orange color",
                "scope": "region.orangish",
                # "foreground": "var(--orangish)",
                "background": "var(background)"
            },
            {
                "name": "region yellow color",
                "scope": "region.yellowish",
                # "foreground": "var(--yellowish)",
                "background": "var(background)"
            },
            {
                "name": "region green color",
                "scope": "region.greenish",
                # "foreground":"var(--greenish)",
                "background": "var(background)"
            },
            {
                "name": "region purple color",
                "scope": "region.purplish",
                # "foreground": "var(--purplish)",
                "background": "var(background)"
            },
            {
                "name": "region pink color",
                "scope": "region.pinkish",
                # "foreground": "var(--pinkish)",
                "background": "var(background)"
            }
        ]

        git_diff_rules = [
            {
                "name": "Inserted",
                "scope": "markup.inserted",
                "foreground": "var(textcolor)",
                "background": "var(inserted)"
            },
            {
                "name": "Changed",
                "scope": "markup.changed",
                "foreground": "var(textcolor)",
                "background": "var(modified)"
            },
            {
                "name": "Deleted",
                "scope": "markup.deleted",
                "foreground": "var(textcolor)",
                "background": "var(deleted)"
            },
            {
                "name": "Diff Deleted",
                "scope": "diff.deleted",
                "foreground": "var(textcolor)",
                "background": "var(modified)"
            },
            {
                "name": "Diff deleted char",
                "scope": "diff.deleted.char",
                "foreground": "var(textcolor)",
                "background": "var(modified)"
            },
            {
                "name": "Diff inserted",
                "scope": "diff.inserted",
                "foreground": "var(textcolor)",
                "background": "var(modified)"
            },
            {
                "name": "Diff inserted char",
                "scope": "diff.inserted.char",
                "foreground": "var(textcolor)",
                "background": "var(modified)"
            }
        ]

        lsp_markup_colors = [
            {
                "name": "lsp info color",
                "scope": "markup.info.lsp",
                "foreground": "var(--bluish)",
                "background": "var(background)"
            },
            {
                "name": "lsp hint color",
                "scope": "markup.info.hint.lsp",
                "foreground": "var(--greenish)",
                "background": "var(background)"
            },
            {
                "name": "lsp warning color",
                "scope": "markup.warning.lsp",
                "foreground": "var(--yellowish)",
                "background": "var(background)"
            },
            {
                "name": "lsp error color",
                "scope": "markup.error.lsp",
                "foreground": "var(--redish)",
                "background": "var(background)"

            }
        ]

        side_by_side_compare_colors = [
            {
                "name": "Sbs compare diff deleted",
                "scope": "diff.deleted.sbs-compare",
                "foreground": "var(textcolor)",
                "background": "var(deleted)"
            },
            {
                "name": "Sbs compare diff char deleted",
                "scope": "diff.deleted.char.sbs-compare",
                "foreground": "var(textcolor)",
                "background": "var(modified)"
            },
            {
                "name": "Sbs compare diff inserted",
                "scope": "diff.inserted.sbs-compare",
                "foreground": "var(textcolor)",
                "background": "var(inserted)"
            },
            {
                "name": "Sbs compare diff inserted char",
                "scope": "diff.inserted.char.sbs-compare",
                "foreground": "var(textcolor)",
                "background": "var(modified)"
            }
        ]

        # Add region rules to the main rules list
        rules.extend(region_rules)
        rules.extend(git_diff_rules)
        rules.extend(lsp_markup_colors)
        rules.extend(side_by_side_compare_colors)
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
