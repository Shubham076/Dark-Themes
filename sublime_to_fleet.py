#!/usr/bin/env python3
"""
Sublime Text to Fleet Theme Converter

This script converts Sublime Text theme files (.sublime-color-scheme) to Fleet theme files (.json).
It maps Sublime's TextMate scope-based syntax highlighting to Fleet's semantic token-based system.

Usage:
    python3 sublime_to_fleet.py <input-sublime-theme.json> <output-fleet-theme.json>
    
Example:
    python3 sublime_to_fleet.py sublime.json fleet-converted.json
"""

import json
import argparse
import re
from typing import Dict, List, Optional, Any
from pathlib import Path


class SublimeToFleetConverter:
    """Converts Sublime Text themes to Fleet theme format."""
    
    def __init__(self):
        # Map Sublime TextMate scopes to Fleet semantic identifiers
        self.scope_to_fleet_mapping = {
            # Comments
            'comment': 'comment',
            'comment.line': 'comment',
            'comment.block': 'comment',
            'comment.documentation': 'comment.doc',
            'punctuation.definition.comment': 'comment',
            
            # Keywords
            'keyword': 'keyword',
            'keyword.control': 'keyword',
            'keyword.operator': 'punctuation.operator',
            'keyword.operator.logical': 'punctuation.operator',
            'keyword.operator.comparison': 'punctuation.operator',
            'keyword.operator.assignment': 'punctuation.operator',
            'keyword.operator.arithmetic': 'punctuation.operator',
            'keyword.other': 'keyword',
            
            # Storage (classes, types)
            'storage': 'identifier.type',
            'storage.type': 'identifier.type',
            'storage.type.builtin': 'identifier.type',
            'storage.modifier': 'keyword.typeModifier',
            'entity.name': 'identifier.type',
            'entity.name.type': 'identifier.type',
            'entity.name.class': 'identifier.type.class',
            'support.class': 'identifier.type.class',
            
            # Functions
            'entity.name.function': 'identifier.function.declaration',
            'variable.function': 'identifier.function.call',
            'support.function': 'identifier.function.call',
            'meta.function-call': 'identifier.function.call',
            'support.function.builtin': 'identifier.function.call',
            
            # Variables
            'variable': 'identifier.variable',
            'variable.other': 'identifier.variable',
            'variable.other.readwrite': 'identifier.variable',
            'variable.other.member': 'identifier.field',
            'variable.parameter': 'identifier.parameter',
            'variable.other.constant': 'identifier.constant',
            
            # Constants
            'constant': 'identifier.constant',
            'constant.numeric': 'number',
            'constant.language': 'identifier.constant.predefined',
            'constant.character': 'identifier.constant',
            'constant.character.escape': 'string.escape',
            'support.constant': 'identifier.constant',
            
            # Strings
            'string': 'string',
            'string.quoted': 'string',
            'string.quoted.single': 'string',
            'string.quoted.double': 'string',
            'string.quoted.triple': 'string',
            'string.unquoted': 'string',
            'string.template': 'string',
            'string.regexp': 'string.regexp',
            
            # Numbers
            'constant.numeric': 'number',
            
            # Booleans
            'constant.language.boolean': 'boolean',
            
            # Tags (HTML/XML)
            'entity.name.tag': 'tagName.html',
            'entity.name.tag.html': 'tagName.html',
            'entity.name.tag.xml': 'tagName.html',
            'meta.tag': 'tag.html',
            
            # Attributes
            'entity.other.attribute-name': 'attributeName.html',
            'entity.other.attribute-name.html': 'attributeName.html',
            'entity.other.attribute-name.xml': 'attributeName.html',
            
            # CSS Selectors
            'entity.other.attribute-name.class.css': 'selector.class.css',
            'entity.other.attribute-name.id.css': 'selector.id.css',
            'entity.other.attribute-name.pseudo-class.css': 'selector.pseudo.css',
            'support.type.property-name.css': 'propertyName.css',
            
            # JSON/YAML Keys
            'meta.mapping.key.json string.quoted.double.json': 'key.json',
            'meta.mapping.key.yaml': 'key.yaml',
            
            # Operators
            'punctuation.operator': 'punctuation.operator',
            'keyword.operator': 'punctuation.operator',
            
            # Punctuation
            'punctuation': 'punctuation',
            'punctuation.definition': 'punctuation',
            
            # Markup (Markdown)
            'markup.bold': 'markup.bold',
            'markup.italic': 'markup.italic',
            'markup.heading': 'markup.heading',
            'markup.inserted': 'diff.added',
            'markup.deleted': 'diff.deleted',
            'markup.changed': 'diff.modified',
            
            # Diff scopes
            'diff.deleted': 'diff.deleted',
            'diff.deleted.char': 'diff.deleted.char',
            'diff.inserted': 'diff.inserted',
            'diff.inserted.char': 'diff.inserted.char',
            'diff.deleted.sbs-compare': 'sbs.compare.diff.deleted',
            'diff.deleted.char.sbs-compare': 'sbs.compare.diff.char.deleted',
            'diff.inserted.sbs-compare': 'sbs.compare.diff.inserted',
            'diff.inserted.char.sbs-compare': 'sbs.compare.diff.inserted.char',
            
            # Annotations
            'storage.type.annotation': 'comment.doc.tag',
            'variable.annotation': 'comment.doc.tag',
            
            # Links
            'markup.underline.link': 'link',
            'string.other.link': 'link',
        }
        
    def resolve_color_var(self, color_value: str, variables: Dict[str, str]) -> str:
        """Resolve var() references in color values."""
        if not color_value or not isinstance(color_value, str):
            return color_value
            
        # Handle var() references
        if color_value.startswith('var(') and color_value.endswith(')'):
            var_name = color_value[4:-1]  # Extract variable name
            if var_name in variables:
                return self.resolve_color_var(variables[var_name], variables)
        
        return color_value
    
    def normalize_color(self, color: str) -> str:
        """Normalize color to uppercase hex format."""
        if not color or not isinstance(color, str):
            return color
        
        color = color.strip()
        
        # Already a hex color
        if color.startswith('#'):
            return color.upper()
        
        return color
    
    def determine_theme_kind(self, background: str) -> str:
        """Determine if theme is Light or Dark based on background color."""
        if not background or not background.startswith('#'):
            return "Dark"
        
        # Convert hex to RGB and calculate brightness
        try:
            hex_color = background.lstrip('#')
            if len(hex_color) == 6:
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                return "Light" if brightness > 128 else "Dark"
        except:
            pass
        
        return "Dark"
    
    def create_palette_from_variables(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Create Fleet palette from Sublime variables - using ONLY colors from Sublime."""
        palette = {}
        
        # Map Sublime variable names to semantic Fleet palette names
        # Using ONLY what exists in Sublime theme
        var_to_palette = {
            'textcolor': 'Text',
            'background': 'Base',
            'popup_bg': 'Mantle',
            'selection_background': 'Selection',
            'line_highlight_color': 'LineHighlight',
            'gutter_foreground_color': 'GutterFg',
            
            # Semantic colors from Sublime
            'comment_color': 'Comment',
            'keyword_color': 'Keyword',
            'string_color': 'String',
            'function_color': 'Function',
            'constant_color': 'Constant',
            'operator_color': 'Operator',
            'variable_color': 'Variable',
            'storage_color': 'Storage',
            'annotation_color': 'Annotation',
            'doc_color': 'Documentation',
            'tag_color': 'Tag',
            'css_selector_color': 'CssSelector',
            'json_key_color': 'JsonKey',
            'yaml_key_color': 'YamlKey',
            
            # Named colors from Sublime
            '--redish': 'Red',
            '--greenish': 'Green',
            '--bluish': 'Blue',
            '--yellowish': 'Yellow',
            '--cyanish': 'Cyan',
            '--orangish': 'Orange',
            '--pinkish': 'Pink',
            '--purplish': 'Purple',
            
            # Diff colors
            'inserted': 'DiffInserted',
            'deleted': 'DiffDeleted',
            'modified': 'DiffModified',
        }
        
        # Add resolved colors to palette - ONLY from Sublime variables
        for var_name, palette_name in var_to_palette.items():
            if var_name in variables:
                color = self.resolve_color_var(variables[var_name], variables)
                if color and color.startswith('#'):
                    palette[palette_name] = self.normalize_color(color)
        
        # Add transparent color
        palette['Transparent'] = '#FFFFFF00'
        
        return palette
    
    def create_colors_from_globals(self, globals_dict: Dict[str, str], 
                                   variables: Dict[str, str], 
                                   palette: Dict[str, str],
                                   theme_kind: str = "Dark") -> Dict[str, str]:
        """Create Fleet colors section from Sublime globals - using ONLY palette colors."""
        colors = {}

        # Get resolved colors
        background = self.resolve_color_var(globals_dict.get('background', ''), variables)
        foreground = self.resolve_color_var(globals_dict.get('foreground', ''), variables)
        selection = self.resolve_color_var(globals_dict.get('selection', ''), variables)
        line_highlight = self.resolve_color_var(globals_dict.get('line_highlight', ''), variables)
        caret = self.resolve_color_var(globals_dict.get('caret', ''), variables)

        # Smart palette lookup with fallbacks
        def get_palette_color(preferred_names: List[str], fallback: str = 'Text') -> str:
            """Get first available color from preferred names, or fallback."""
            for name in preferred_names:
                if name in palette:
                    return name
            return fallback if fallback in palette else list(palette.keys())[0]

        # Find exact palette match for a color value
        def find_palette_name(color: str, fallback: str = 'Text') -> str:
            if not color:
                return fallback
            color = self.normalize_color(color)
            for name, palette_color in palette.items():
                if self.normalize_color(palette_color) == color:
                    return name
            return fallback

        # Define common colors early
        bg = get_palette_color(['Base', 'Text'])
        text_color = get_palette_color(['Text', 'Variable'])

        # === Core Editor Colors ===
        colors['editor.text'] = text_color
        colors['editor.caret.background'] = text_color
        colors['editor.whitespace.text'] = get_palette_color(['Comment', 'GutterFg', 'Text'])

        # Line highlighting
        line_hl = find_palette_name(line_highlight, 'LineHighlight')
        colors['editor.currentLine.background.default'] = line_hl
        colors['editor.currentLine.background.focused'] = line_hl

        # Line numbers
        colors['editor.lineNumber.default'] = get_palette_color(['GutterFg', 'Comment', 'Text'])
        colors['editor.lineNumber.current'] = get_palette_color(['Keyword', 'Purple', 'Blue', 'Text'])

        # Editor folding and interline (IMPORTANT for panels/terminal area)
        colors['editor.foldedMark.background'] = get_palette_color(['Mantle', 'Base'])
        colors['editor.foldedMark.text'] = text_color
        colors['editor.foldIndicator.icon.default'] = get_palette_color(['GutterFg', 'Comment'])
        colors['editor.foldIndicator.icon.hovered'] = get_palette_color(['Keyword', 'Purple', 'Blue'])
        colors['editor.foldIndicator.background.hovered'] = get_palette_color(['Mantle', 'Base'])
        colors['editor.interline.background'] = bg  # Terminal/console area background
        colors['editor.interline.match.background'] = get_palette_color(['Yellow', 'Orange', 'Selection'])
        colors['editor.interline.match.background.secondary'] = get_palette_color(['Yellow', 'Orange', 'Selection'])
        colors['editor.interline.match.text'] = text_color  # Text color for inline matches like "Git Pull"
        colors['editor.interline.match.text.secondary'] = text_color
        colors['editor.interline.preview.background'] = bg
        colors['editor.interline.preview.border'] = 'Transparent'

        # === Background Colors ===
        # Use selection color for background.primary
        sel = find_palette_name(selection, 'Selection')
        colors['background.primary'] = sel
        colors['background.secondary'] = bg
        colors['island.background'] = bg
        colors['background.hovered'] = get_palette_color(['LineHighlight', 'Selection', 'Base'])
        colors['background.selected'] = get_palette_color(['Selection', 'LineHighlight', 'Base'])

        # Selection is handled in textAttributes, not colors

        # === Borders ===
        colors['border'] = bg
        colors['border.focused'] = get_palette_color(['Keyword', 'Purple', 'Blue', 'Function'])
        colors['shadow.border'] = get_palette_color(['Mantle', 'Base'])

        # === Text Colors ===
        colors['text.default'] = text_color
        colors['text.primary'] = text_color
        colors['text.secondary'] = get_palette_color(['Comment', 'GutterFg', 'Text'])
        colors['text.tertiary'] = get_palette_color(['GutterFg', 'Comment', 'Text'])
        colors['text.disabled'] = get_palette_color(['Comment', 'GutterFg', 'Text'])
        colors['text.bright'] = text_color
        colors['text.dangerous'] = get_palette_color(['Red', 'Operator', 'Keyword'])

        # === Git Diff Colors ===
        # Use actual diff colors from palette or defaults for background
        colors['editor.gitDiff.background.added'] = get_palette_color(['DiffInserted', 'Green', 'String'])
        colors['editor.gitDiff.background.deleted'] = get_palette_color(['DiffDeleted', 'Red', 'Operator'])
        colors['editor.gitDiff.background.modified'] = get_palette_color(['DiffModified', 'Blue', 'Function'])
        colors['editor.gitDiff.background.conflict'] = get_palette_color(['DiffDeleted', 'Red', 'Operator'])

        # Use specific hex values for text colors based on theme kind
        if theme_kind == "Light":
            # Light theme colors from Atom One Light
            colors['editor.gitDiff.text.added'] = "#50A14F"    # Green
            colors['editor.gitDiff.text.conflict'] = "#DC1212"  # Error (Red)
            colors['editor.gitDiff.text.deleted'] = "#E45649"   # Coral
            colors['editor.gitDiff.text.modified'] = "#C18401"  # Orange
        else:
            # Dark theme colors from Fleet Dark
            colors['editor.gitDiff.text.added'] = "#3EA17F"    # Green
            colors['editor.gitDiff.text.conflict'] = "#FAD075"  # Yellow
            colors['editor.gitDiff.text.deleted'] = "#EB4056"   # Red
            colors['editor.gitDiff.text.modified'] = "#F8AB17"  # Orange/Yellow

        # === Links ===
        colors['link.focusOutline'] = get_palette_color(['Blue', 'Cyan', 'Function'])
        colors['link.text'] = get_palette_color(['Blue', 'Cyan', 'Function', 'Documentation'])

        # === Search & Completion ===
        colors['completion.match.background'] = 'Transparent'
        colors['completion.match.text'] = get_palette_color(['Orange', 'Yellow', 'Constant'])
        colors['search.match.background'] = get_palette_color(['Yellow', 'Orange', 'Selection'])
        colors['search.match.text'] = get_palette_color(['Base', 'Text'])

        # === Popups & Tooltips ===
        popup_bg = get_palette_color(['Mantle', 'Base'])
        colors['popup.background'] = popup_bg
        colors['popup.editor.background'] = bg
        colors['popup.goto.background'] = popup_bg
        colors['popup.text'] = text_color  # Add explicit popup text color
        colors['popup.foreground'] = text_color  # Add popup foreground
        colors['tooltip.background'] = popup_bg
        colors['tooltip.border'] = 'Transparent'
        colors['tooltip.text.primary'] = text_color
        colors['tooltip.text'] = text_color  # Add tooltip text
        colors['tooltip.text.secondary'] = text_color
        colors['tooltip.text.tertiary'] = text_color

        # === Notifications ===
        colors['notification.background.default'] = bg
        colors['notification.background.unread'] = get_palette_color(['Selection', 'LineHighlight'])
        colors['notification.separator'] = get_palette_color(['Mantle', 'Base'])
        colors['notification.text'] = text_color
        colors['notification.timestamp'] = text_color

        # === AI Properties ===
        colors['ai.snippet.border'] = 'Transparent'
        colors['ai.snippet.header.background'] = get_palette_color(['Mantle', 'Base'])
        colors['ai.snippet.editor.background'] = bg
        colors['ai.icon.background'] = get_palette_color(['Purple', 'Keyword', 'Blue'])
        colors['ai.icon.background.secondary'] = get_palette_color(['Selection', 'LineHighlight'])
        colors['ai.user.icon.text'] = get_palette_color(['Blue', 'Cyan', 'Function'])
        colors['ai.user.icon.background'] = get_palette_color(['Blue', 'Cyan', 'Function'])
        colors['ai.user.icon.background.secondary'] = get_palette_color(['Selection', 'LineHighlight'])
        colors['ai.error.border'] = get_palette_color(['Red', 'Operator'])

        # === List Items (for popup menus) ===
        colors['listItem.text.default'] = text_color
        colors['listItem.text.hovered'] = text_color
        colors['listItem.text.focused'] = text_color
        colors['listItem.text.selected'] = text_color
        colors['listItem.text.secondary'] = get_palette_color(['Comment', 'GutterFg'])
        colors['listItem.border.default'] = 'Transparent'
        colors['listItem.border.hovered'] = 'Transparent'
        colors['listItem.border.focused'] = 'Transparent'
        colors['listItem.border.selected'] = 'Transparent'
        colors['listItem.background.default'] = 'Transparent'
        colors['listItem.background.hovered'] = get_palette_color(['LineHighlight', 'Selection'])
        colors['listItem.background.focused'] = get_palette_color(['Selection', 'LineHighlight'])
        colors['listItem.background.selected'] = get_palette_color(['Selection', 'LineHighlight'])
        colors['listItem.background.dnd'] = get_palette_color(['Selection', 'LineHighlight'])

        # === Tree (file explorer) ===
        colors['tree.focusBorder'] = get_palette_color(['Keyword', 'Purple', 'Blue'])
        colors['tree.compactFolder.selector.default'] = text_color
        colors['tree.compactFolder.selector.focused'] = text_color
        colors['tree.compactFolder.separator'] = get_palette_color(['Comment', 'GutterFg'])

        # === Tabs ===
        # Use selection color for better contrast in editor tabs (no borders)
        colors['tab.background.default'] = 'Transparent'
        colors['tab.background.selected'] = sel
        colors['tab.background.hovered'] = get_palette_color(['LineHighlight', 'Selection'])
        colors['tab.background.selectedFocused'] = sel
        colors['tab.border.default'] = 'Transparent'
        colors['tab.border.hovered'] = 'Transparent'
        colors['tab.border.selected'] = 'Transparent'
        colors['tab.border.selectedFocused'] = 'Transparent'
        colors['tab.text'] = text_color

        # === Terminal ===
        # Terminal background = editor background (Base)
        colors['terminal.background'] = bg
        colors['terminal.foreground'] = text_color

        # Terminal ANSI colors using palette
        colors['terminal.ansiColors.background.ansiBlack'] = bg
        colors['terminal.ansiColors.foreground.ansiBlack'] = text_color
        colors['terminal.ansiColors.background.ansiRed'] = get_palette_color(['Red', 'Operator'])
        colors['terminal.ansiColors.foreground.ansiRed'] = get_palette_color(['Red', 'Operator'])
        colors['terminal.ansiColors.background.ansiGreen'] = get_palette_color(['Green', 'String'])
        colors['terminal.ansiColors.foreground.ansiGreen'] = get_palette_color(['Green', 'String'])
        colors['terminal.ansiColors.background.ansiYellow'] = get_palette_color(['Yellow', 'Constant'])
        colors['terminal.ansiColors.foreground.ansiYellow'] = get_palette_color(['Yellow', 'Constant'])
        colors['terminal.ansiColors.background.ansiBlue'] = get_palette_color(['Blue', 'Function'])
        colors['terminal.ansiColors.foreground.ansiBlue'] = get_palette_color(['Blue', 'Function'])
        colors['terminal.ansiColors.background.ansiMagenta'] = get_palette_color(['Purple', 'Pink', 'Keyword'])
        colors['terminal.ansiColors.foreground.ansiMagenta'] = get_palette_color(['Purple', 'Pink', 'Keyword'])
        colors['terminal.ansiColors.background.ansiCyan'] = get_palette_color(['Cyan', 'Blue'])
        colors['terminal.ansiColors.foreground.ansiCyan'] = get_palette_color(['Cyan', 'Blue'])
        colors['terminal.ansiColors.background.ansiWhite'] = text_color
        colors['terminal.ansiColors.foreground.ansiWhite'] = text_color

        # Bright ANSI colors (ansiBrightWhite controls terminal background!)
        colors['terminal.ansiColors.background.ansiBrightBlack'] = get_palette_color(['LineHighlight', 'Selection'])
        colors['terminal.ansiColors.foreground.ansiBrightBlack'] = get_palette_color(['Comment', 'GutterFg'])
        colors['terminal.ansiColors.background.ansiBrightRed'] = get_palette_color(['Red', 'Operator'])
        colors['terminal.ansiColors.foreground.ansiBrightRed'] = get_palette_color(['Red', 'Operator'])
        colors['terminal.ansiColors.background.ansiBrightGreen'] = get_palette_color(['Green', 'String'])
        colors['terminal.ansiColors.foreground.ansiBrightGreen'] = get_palette_color(['Green', 'String'])
        colors['terminal.ansiColors.background.ansiBrightYellow'] = get_palette_color(['Yellow', 'Constant'])
        colors['terminal.ansiColors.foreground.ansiBrightYellow'] = get_palette_color(['Yellow', 'Constant'])
        colors['terminal.ansiColors.background.ansiBrightBlue'] = get_palette_color(['Blue', 'Function'])
        colors['terminal.ansiColors.foreground.ansiBrightBlue'] = get_palette_color(['Blue', 'Function'])
        colors['terminal.ansiColors.background.ansiBrightMagenta'] = get_palette_color(['Purple', 'Pink', 'Keyword'])
        colors['terminal.ansiColors.foreground.ansiBrightMagenta'] = get_palette_color(['Purple', 'Pink', 'Keyword'])
        colors['terminal.ansiColors.background.ansiBrightCyan'] = get_palette_color(['Cyan', 'Blue'])
        colors['terminal.ansiColors.foreground.ansiBrightCyan'] = get_palette_color(['Cyan', 'Blue'])
        colors['terminal.ansiColors.background.ansiBrightWhite'] = bg  # Editor background for terminal
        colors['terminal.ansiColors.foreground.ansiBrightWhite'] = text_color

        # === Buttons ===
        # Regular buttons
        colors['button.background.default'] = get_palette_color(['LineHighlight', 'Selection'])
        colors['button.background.hovered'] = get_palette_color(['Selection', 'LineHighlight'])
        colors['button.text.default'] = text_color
        colors['button.text.hovered'] = text_color
        colors['button.border.default'] = get_palette_color(['Selection', 'LineHighlight'])
        colors['button.focusBorder'] = 'Transparent'
        colors['button.focusOutline'] = 'Transparent'

        # Secondary buttons
        colors['button.secondary.background.default'] = get_palette_color(['LineHighlight', 'Selection'])
        colors['button.secondary.background.hovered'] = get_palette_color(['Selection', 'LineHighlight'])
        colors['button.secondary.text.default'] = text_color
        colors['button.secondary.text.hovered'] = text_color
        colors['button.secondary.border.default'] = 'Transparent'

        # Tile buttons (like Git Pull)
        colors['button.tile.background.default'] = get_palette_color(['Mantle', 'LineHighlight', 'Base'])
        colors['button.tile.background.hovered'] = get_palette_color(['LineHighlight', 'Selection'])
        colors['button.tile.text.default'] = text_color
        colors['button.tile.text.hovered'] = text_color
        colors['button.tile.border.default'] = 'Transparent'

        # === Misc UI ===
        colors['disabled'] = 'Transparent'
        colors['focusOutline'] = get_palette_color(['Keyword', 'Purple', 'Blue'])

        return colors

    def map_scope_to_fleet(self, scope: str) -> Optional[str]:
        """Map a Sublime scope to a Fleet semantic identifier."""
        # Try exact match first
        if scope in self.scope_to_fleet_mapping:
            return self.scope_to_fleet_mapping[scope]

        # Try partial matches (longer matches first)
        scopes = scope.split(',')
        for s in scopes:
            s = s.strip()
            # Try progressively shorter prefixes
            parts = s.split('.')
            for i in range(len(parts), 0, -1):
                prefix = '.'.join(parts[:i])
                if prefix in self.scope_to_fleet_mapping:
                    return self.scope_to_fleet_mapping[prefix]

        return None

    def create_text_attributes(self, rules: List[Dict], variables: Dict[str, str],
                               palette: Dict[str, str], globals_dict: Dict[str, str] = None) -> Dict[str, Dict]:
        """Create Fleet textAttributes from Sublime rules - using ONLY palette colors."""
        text_attributes = {}
        if globals_dict is None:
            globals_dict = {}

        # Smart palette lookup with fallbacks
        def get_palette_color(preferred_names: List[str], fallback: str = 'Text') -> str:
            """Get first available color from preferred names, or fallback."""
            for name in preferred_names:
                if name in palette:
                    return name
            return fallback if fallback in palette else list(palette.keys())[0]

        # Find palette name for a color value
        def find_palette_name(color: str, fallback: str = 'Text') -> str:
            if not color:
                return fallback
            color = self.normalize_color(self.resolve_color_var(color, variables))
            for name, palette_color in palette.items():
                if self.normalize_color(palette_color) == color:
                    return name
            # If not found, don't return the hex - return fallback
            return get_palette_color([fallback], 'Text')

        # Add all common text attributes directly (based on Fleet.json structure)
        # No need to process rules - just define what we need

        # Comments
        text_attributes['comment'] = {
            'foregroundColor': get_palette_color(['Comment', 'GutterFg'], 'Text'),
            'fontModifier': {'italic': True}
        }
        text_attributes['comment.doc'] = {
            'foregroundColor': get_palette_color(['Documentation', 'Comment'], 'Text')
        }
        text_attributes['comment.doc.tag'] = {
            'foregroundColor': get_palette_color(['Annotation', 'Documentation', 'Comment'], 'Text')
        }

        # Keywords
        text_attributes['keyword'] = {
            'foregroundColor': get_palette_color(['Keyword', 'Purple', 'Blue'], 'Text')
        }
        text_attributes['keyword.control'] = {
            'foregroundColor': get_palette_color(['Keyword', 'Purple', 'Blue'], 'Text')
        }
        text_attributes['keyword.typeModifier'] = {
            'foregroundColor': get_palette_color(['Storage', 'Yellow', 'Blue'], 'Text')
        }

        # Strings
        text_attributes['string'] = {
            'foregroundColor': get_palette_color(['String', 'Green', 'Constant'], 'Text')
        }
        text_attributes['string.regexp'] = {
            'foregroundColor': get_palette_color(['String', 'Green'], 'Text')
        }

        # Numbers and constants
        text_attributes['number'] = {
            'foregroundColor': get_palette_color(['Constant', 'Orange', 'Yellow'], 'Text')
        }
        text_attributes['boolean'] = {
            'foregroundColor': get_palette_color(['Keyword', 'Purple', 'Constant'], 'Text')
        }

        # Identifiers
        text_attributes['identifier'] = {
            'foregroundColor': get_palette_color(['Variable', 'Text'], 'Text')
        }
        text_attributes['identifier.function.call'] = {
            'foregroundColor': get_palette_color(['Function', 'Blue', 'Cyan'], 'Text')
        }
        text_attributes['identifier.function.declaration'] = {
            'foregroundColor': get_palette_color(['Function', 'Blue', 'Cyan'], 'Text')
        }
        text_attributes['identifier.type'] = {
            'foregroundColor': get_palette_color(['Storage', 'Yellow', 'Blue'], 'Text')
        }
        text_attributes['identifier.type.class'] = {
            'foregroundColor': get_palette_color(['Storage', 'Yellow', 'Blue'], 'Text')
        }
        text_attributes['identifier.type.enum'] = {
            'foregroundColor': get_palette_color(['Storage', 'Yellow', 'Blue'], 'Text')
        }
        text_attributes['identifier.type.struct'] = {
            'foregroundColor': get_palette_color(['Storage', 'Yellow', 'Blue'], 'Text')
        }
        text_attributes['identifier.interface'] = {
            'foregroundColor': get_palette_color(['Storage', 'Yellow', 'Blue'], 'Text')
        }
        text_attributes['identifier.typeReference'] = {
            'foregroundColor': get_palette_color(['Storage', 'Yellow', 'Blue'], 'Text')
        }
        text_attributes['identifier.constant'] = {
            'foregroundColor': get_palette_color(['Constant', 'Orange', 'Yellow'], 'Text')
        }
        text_attributes['identifier.parameter'] = {
            'foregroundColor': get_palette_color(['Variable', 'Text'], 'Text')  # Use Variable color instead of Annotation
        }
        text_attributes['identifier.variable'] = {
            'foregroundColor': get_palette_color(['Variable', 'Text'], 'Text')
        }
        text_attributes['identifier.field'] = {
            'foregroundColor': get_palette_color(['Variable', 'Text'], 'Text')
        }

        # Operators and punctuation
        text_attributes['punctuation'] = {
            'foregroundColor': get_palette_color(['Operator', 'Cyan', 'Text'], 'Text')
        }
        text_attributes['punctuation.operator'] = {
            'foregroundColor': get_palette_color(['Operator', 'Cyan', 'Keyword'], 'Text')
        }

        # HTML/XML
        text_attributes['tagName.html'] = {
            'foregroundColor': get_palette_color(['Tag', 'Red', 'Keyword'], 'Text')
        }
        text_attributes['tag.html'] = {
            'foregroundColor': get_palette_color(['Tag', 'Text'], 'Text'),
            'backgroundColor': get_palette_color(['Base'], 'Base')
        }
        text_attributes['attributeName.html'] = {
            'foregroundColor': get_palette_color(['Annotation', 'Yellow', 'Function'], 'Text')
        }

        # JSON
        text_attributes['json.keys'] = {
            'foregroundColor': get_palette_color(['Text', 'Variable'], 'Text')
        }

        # Markup
        text_attributes['markup.bold'] = {
            'fontModifier': {'bold': True}
        }
        text_attributes['markup.italic'] = {
            'fontModifier': {'italic': True}
        }
        text_attributes['markup.heading'] = {
            'foregroundColor': get_palette_color(['Keyword', 'Purple', 'Blue'], 'Text'),
            'fontModifier': {'bold': True}
        }

        # Links
        text_attributes['link'] = {
            'foregroundColor': get_palette_color(['Blue', 'Cyan', 'Function'], 'Text')
        }

        # Regions (for highlighting)
        for color in ['red', 'blue', 'orange', 'yellow', 'green', 'purple', 'pink']:
            text_attributes[f'region.{color}.color'] = {
                'backgroundColor': get_palette_color(['Base'], 'Base')
            }

        # LSP diagnostics
        text_attributes['lsp.info.color'] = {
            'foregroundColor': get_palette_color(['Blue', 'Function'], 'Text'),
            'backgroundColor': get_palette_color(['Base'], 'Base')
        }
        text_attributes['lsp.hint.color'] = {
            'foregroundColor': get_palette_color(['Green', 'String'], 'Text'),
            'backgroundColor': get_palette_color(['Base'], 'Base')
        }
        text_attributes['lsp.warning.color'] = {
            'foregroundColor': get_palette_color(['Yellow', 'Constant'], 'Text'),
            'backgroundColor': get_palette_color(['Base'], 'Base')
        }
        text_attributes['lsp.error.color'] = {
            'foregroundColor': get_palette_color(['Red', 'Operator'], 'Text'),
            'backgroundColor': get_palette_color(['Base'], 'Base')
        }

        # Add editor selection (CRITICAL for Fleet) - must be in textAttributes
        selection_color = globals_dict.get('selection', '')
        if selection_color:
            sel_resolved = find_palette_name(self.resolve_color_var(selection_color, variables), 'Selection')
        else:
            sel_resolved = get_palette_color(['Selection', 'LineHighlight', 'Base'])

        if 'editor.selection' not in text_attributes:
            text_attributes['editor.selection'] = {
                'backgroundColor': sel_resolved
            }
        if 'editor.selection.focused' not in text_attributes:
            text_attributes['editor.selection.focused'] = {
                'backgroundColor': sel_resolved
            }

        # Add indentation guides using selection color
        selection_color = globals_dict.get('selection', '')
        if selection_color:
            indent_guide_color = find_palette_name(self.resolve_color_var(selection_color, variables), 'Selection')
        else:
            indent_guide_color = get_palette_color(['Selection', 'LineHighlight', 'Base'])

        if 'editor.indentGuide' not in text_attributes:
            text_attributes['editor.indentGuide'] = {
                'foregroundColor': indent_guide_color
            }
        if 'editor.indentGuide.current' not in text_attributes:
            text_attributes['editor.indentGuide.current'] = {
                'foregroundColor': indent_guide_color
            }

        # Add bracket matching background using selection color
        if 'editor.brace.match' not in text_attributes:
            text_attributes['editor.brace.match'] = {
                'backgroundColor': sel_resolved
            }

        # Add only the required diff properties
        deleted_color = get_palette_color(['DiffDeleted', 'Red'])
        added_color = get_palette_color(['DiffInserted', 'Green'])
        modified_color = get_palette_color(['DiffModified', 'Blue'])

        # Only add the 6 required diff properties
        text_attributes['diff.added'] = {
            'backgroundColor': added_color
        }
        text_attributes['diff.added.word'] = {
            'backgroundColor': added_color
        }
        text_attributes['diff.deleted'] = {
            'backgroundColor': deleted_color
        }
        text_attributes['diff.deleted.word'] = {
            'backgroundColor': deleted_color
        }
        text_attributes['diff.modified'] = {
            'backgroundColor': modified_color
        }
        text_attributes['diff.modified.word'] = {
            'backgroundColor': modified_color
        }

        return text_attributes

    def convert(self, sublime_theme: Dict) -> Dict:
        """Convert a Sublime theme to Fleet format."""
        # Extract components
        name = sublime_theme.get('name', 'Converted Theme')
        variables = sublime_theme.get('variables', {})
        globals_dict = sublime_theme.get('globals', {})
        rules = sublime_theme.get('rules', [])

        # Create palette
        palette = self.create_palette_from_variables(variables)

        # Determine theme kind
        background = self.resolve_color_var(globals_dict.get('background', ''), variables)
        theme_kind = self.determine_theme_kind(background)

        # Create Fleet theme
        fleet_theme = {
            'meta': {
                'theme.name': name,
                'theme.kind': theme_kind,
                'theme.version': 1
            },
            'colors': self.create_colors_from_globals(globals_dict, variables, palette, theme_kind),
            'textAttributes': self.create_text_attributes(rules, variables, palette, globals_dict),
            'palette': palette
        }
        
        return fleet_theme
    
    def convert_file(self, input_path: str, output_path: str):
        """Convert a Sublime theme file to Fleet format."""
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            sublime_theme = json.load(f)
        
        # Convert
        fleet_theme = self.convert(sublime_theme)
        
        # Write output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(fleet_theme, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Converted: {input_path} -> {output_path}")
        print(f"  Theme: {fleet_theme['meta']['theme.name']}")
        print(f"  Kind: {fleet_theme['meta']['theme.kind']}")
        print(f"  Palette colors: {len(fleet_theme['palette'])}")
        print(f"  Text attributes: {len(fleet_theme['textAttributes'])}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert Sublime Text themes to Fleet theme format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 sublime_to_fleet.py sublime.json fleet.json
  python3 sublime_to_fleet.py my-theme.sublime-color-scheme my-theme-fleet.json
        """
    )
    
    parser.add_argument('input', help='Input Sublime theme file (.sublime-color-scheme or .json)')
    parser.add_argument('output', help='Output Fleet theme file (.json)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    # Convert
    try:
        converter = SublimeToFleetConverter()
        converter.convert_file(args.input, args.output)
        return 0
    except Exception as e:
        print(f"Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
