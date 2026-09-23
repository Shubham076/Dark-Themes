#!/usr/bin/env python3
"""
IntelliJ to Fleet Theme Converter

Reads an IntelliJ color scheme (.icls / .xml) and maps its attribute keys straight to Fleet
textAttributes keys. Each Fleet key lists IntelliJ sources in priority order; the first one the
scheme defines wins, following `baseAttributes` inheritance. A foreground key with no source falls
back to its Fleet parent (`identifier.variable` -> `identifier` -> `editor.text.scheme`), so nothing
is left to Fleet's built-in defaults.

Usage:
    python3 intellij_to_fleet.py <input.icls|input.xml> <output-fleet-theme.json>

Example:
    python3 intellij_to_fleet.py src/main/resources/themes/vitesseLight.xml vitesse-light-soft.json
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sublime_to_fleet import SublimeToFleetConverter

# Sources prefixed with '@' come from the scheme's <colors> section, others from <attributes>.
FG, BG, WAVY = 'FOREGROUND', 'BACKGROUND', 'EFFECT_COLOR'

TEXT_ATTRIBUTES: Dict[str, Tuple[str, List[str]]] = {
    'editor.text.scheme': (FG, ['TEXT']),

    'comment': (FG, ['DEFAULT_LINE_COMMENT', 'DEFAULT_BLOCK_COMMENT']),
    'comment.doc': (FG, ['DEFAULT_DOC_COMMENT', 'DEFAULT_BLOCK_COMMENT']),
    'comment.doc.tag': (FG, ['DEFAULT_DOC_COMMENT_TAG']),
    'comment.doc.value': (FG, ['DEFAULT_DOC_COMMENT_TAG_VALUE', 'DEFAULT_DOC_COMMENT_TAG']),
    'comment.todo': (FG, ['TODO_DEFAULT_ATTRIBUTES']),

    'keyword': (FG, ['DEFAULT_KEYWORD']),
    'keyword.typeModifier': (FG, ['DEFAULT_KEYWORD']),
    'metadata': (FG, ['DEFAULT_METADATA']),
    'number': (FG, ['DEFAULT_NUMBER']),
    'boolean': (FG, ['DEFAULT_KEYWORD']),

    'string': (FG, ['DEFAULT_STRING']),
    'string.escape': (FG, ['DEFAULT_VALID_STRING_ESCAPE']),
    'string.regexp': (FG, ['REGEXP.CHARACTER', 'DEFAULT_STRING']),

    'identifier': (FG, ['DEFAULT_IDENTIFIER']),
    'identifier.this': (FG, ['DEFAULT_KEYWORD']),
    'identifier.constant': (FG, ['DEFAULT_CONSTANT']),
    'identifier.constant.predefined': (FG, ['DEFAULT_PREDEFINED_SYMBOL', 'DEFAULT_CONSTANT']),
    'identifier.variable': (FG, ['DEFAULT_LOCAL_VARIABLE', 'DEFAULT_IDENTIFIER']),
    'identifier.variable.mutable': (FG, ['DEFAULT_REASSIGNED_LOCAL_VARIABLE', 'DEFAULT_LOCAL_VARIABLE']),
    'identifier.parameter': (FG, ['DEFAULT_PARAMETER']),
    'identifier.function.declaration': (FG, ['DEFAULT_FUNCTION_DECLARATION']),
    'identifier.function.call': (FG, ['DEFAULT_FUNCTION_CALL', 'DEFAULT_FUNCTION_DECLARATION']),
    'identifier.method.static': (FG, ['DEFAULT_STATIC_METHOD', 'DEFAULT_FUNCTION_DECLARATION']),
    'identifier.type': (FG, ['DEFAULT_CLASS_NAME']),
    'identifier.type.class': (FG, ['DEFAULT_CLASS_NAME']),
    'identifier.type.enum': (FG, ['DEFAULT_CLASS_NAME']),
    'identifier.type.struct': (FG, ['DEFAULT_CLASS_NAME']),
    'identifier.interface': (FG, ['DEFAULT_INTERFACE_NAME', 'DEFAULT_CLASS_NAME']),
    'identifier.typeParameter': (FG, ['TYPE_PARAMETER_NAME_ATTRIBUTES', 'DEFAULT_CLASS_NAME']),
    'identifier.field': (FG, ['DEFAULT_INSTANCE_FIELD']),
    'identifier.field.static': (FG, ['DEFAULT_STATIC_FIELD', 'DEFAULT_INSTANCE_FIELD']),

    'punctuation': (FG, ['DEFAULT_COMMA', 'DEFAULT_DOT', 'DEFAULT_SEMICOLON', 'DEFAULT_BRACES',
                         'DEFAULT_BRACKETS', 'DEFAULT_PARENTHS']),
    'punctuation.operator': (FG, ['DEFAULT_OPERATION_SIGN']),

    'tag.html': (FG, ['XML_TAG', 'HTML_TAG']),
    'tagName.html': (FG, ['XML_TAG_NAME', 'HTML_TAG_NAME']),
    'tagName.custom.html': (FG, ['HTML_CUSTOM_TAG_NAME', 'XML_CUSTOM_TAG_NAME', 'XML_TAG_NAME']),
    'attributeName.html': (FG, ['XML_ATTRIBUTE_NAME', 'HTML_ATTRIBUTE_NAME']),
    'attributeValue.html': (FG, ['XML_ATTRIBUTE_VALUE', 'HTML_ATTRIBUTE_VALUE', 'DEFAULT_STRING']),
    'entityReference.html': (FG, ['XML_ENTITY_REFERENCE', 'HTML_ENTITY_REFERENCE']),

    'key.json': (FG, ['JSON.PROPERTY_KEY', 'DEFAULT_INSTANCE_FIELD']),

    'key.yaml': (FG, ['YAML_SCALAR_KEY', 'DEFAULT_KEYWORD']),
    'schema.yaml': (FG, ['YAML_SCALAR_KEY', 'DEFAULT_KEYWORD']),
    'value.yaml': (FG, ['YAML_SCALAR_VALUE', 'YAML_TEXT', 'TEXT']),
    'identifier.anchor.yaml': (FG, ['YAML_ANCHOR']),
    'identifier.alias.yaml': (FG, ['YAML_ANCHOR']),
    'punctuation.operator.merge.yaml': (FG, ['YAML_SIGN']),

    'attributeName.css': (FG, ['CSS.ATTRIBUTE_NAME']),
    'hex.css': (FG, ['CSS.COLOR']),
    'identifier.css': (FG, ['CSS.IDENT']),
    'identifier.function.css': (FG, ['CSS.FUNCTION']),
    'keyword.css': (FG, ['CSS.KEYWORD']),
    'keyword.important.css': (FG, ['CSS.IMPORTANT']),
    'number.css': (FG, ['CSS.NUMBER']),
    'number.unit.css': (FG, ['CSS.UNIT', 'CSS.NUMBER']),
    'propertyName.css': (FG, ['CSS.PROPERTY_NAME']),
    'propertyValue.css': (FG, ['CSS.PROPERTY_VALUE']),
    'punctuation.css': (FG, ['CSS.BRACES', 'CSS.COLON']),
    'selector.class.css': (FG, ['CSS.CLASS_NAME']),
    'selector.id.css': (FG, ['CSS.HASH']),
    'selector.pseudo.css': (FG, ['CSS.PSEUDO']),
    'selector.tag.css': (FG, ['CSS.TAG_NAME']),
    'string.css': (FG, ['CSS.STRING']),
    'url.css': (FG, ['CSS.URL']),

    'comment.buildConstraint.go': (FG, ['GO_BUILD_TAG']),
    'identifier.methodReceiver.go': (FG, ['GO_METHOD_RECEIVER']),
    'identifier.package.go': (FG, ['GO_PACKAGE']),
    'identifier.typeReference.go': (FG, ['GO_TYPE_REFERENCE']),
    'identifier.variable.shadowing.go': (FG, ['GO_SHADOWING_VARIABLE']),
    'metadata.structTag.key.go': (FG, ['GO_TAG_KEY']),

    'markup.heading': (FG, ['MARKDOWN_HEADER_LEVEL_1']),
    'markup.bold': (FG, ['MARKDOWN_BOLD']),
    'markup.italic': (FG, ['MARKDOWN_ITALIC']),
    'markup.code.block': (FG, ['MARKDOWN_CODE_BLOCK', 'MARKDOWN_CODE_SPAN']),
    'markup.href': (FG, ['MARKDOWN_LINK_DESTINATION', 'MARKDOWN_AUTO_LINK']),
    'link': (FG, ['HYPERLINK_ATTRIBUTES']),

    'problem.unused': (FG, ['NOT_USED_ELEMENT_ATTRIBUTES']),
    'problem.error': (WAVY, ['ERRORS_ATTRIBUTES']),
    'problem.warning': (WAVY, ['WARNING_ATTRIBUTES']),

    'editor.selection': (BG, ['@SELECTION_BACKGROUND']),
    'editor.selection.focused': (BG, ['@SELECTION_BACKGROUND']),
    'editor.search.results': (BG, ['TEXT_SEARCH_RESULT_ATTRIBUTES', 'SEARCH_RESULT_ATTRIBUTES']),
    'identifier.underCaret': (BG, ['IDENTIFIER_UNDER_CARET_ATTRIBUTES']),
    'editor.brace.match': (BG, ['MATCHED_BRACE_ATTRIBUTES', '@SELECTION_BACKGROUND']),
    'editor.indentGuide': (FG, ['@INDENT_GUIDE']),
    'editor.indentGuide.current': (FG, ['@SELECTED_INDENT_GUIDE', '@INDENT_GUIDE']),

    'diff.added': (BG, ['DIFF_INSERTED']),
    'diff.added.word': (BG, ['DIFF_INSERTED']),
    'diff.deleted': (BG, ['DIFF_DELETED']),
    'diff.deleted.word': (BG, ['DIFF_DELETED']),
    'diff.modified': (BG, ['DIFF_MODIFIED']),
    'diff.modified.word': (BG, ['DIFF_MODIFIED']),
    'diff.conflict': (BG, ['DIFF_CONFLICT']),
}

# Named palette roles consumed by SublimeToFleetConverter.create_colors_from_globals (UI chrome).
PALETTE_ROLES: Dict[str, Tuple[str, List[str]]] = {
    'Text': (FG, ['TEXT']),
    'Base': (BG, ['TEXT']),
    'Mantle': (BG, ['@LOOKUP_COLOR', '@DOCUMENTATION_COLOR']),
    'Selection': (BG, ['@SELECTION_BACKGROUND']),
    'LineHighlight': (BG, ['@CARET_ROW_COLOR']),
    'GutterFg': (FG, ['@LINE_NUMBERS_COLOR']),
    'Comment': (FG, ['DEFAULT_LINE_COMMENT', 'DEFAULT_BLOCK_COMMENT']),
    'Keyword': (FG, ['DEFAULT_KEYWORD']),
    'String': (FG, ['DEFAULT_STRING']),
    'Function': (FG, ['DEFAULT_FUNCTION_DECLARATION']),
    'Constant': (FG, ['DEFAULT_CONSTANT', 'DEFAULT_NUMBER']),
    'Operator': (FG, ['DEFAULT_OPERATION_SIGN']),
    'Variable': (FG, ['DEFAULT_IDENTIFIER', 'TEXT']),
    'Storage': (FG, ['DEFAULT_CLASS_NAME']),
    'Annotation': (FG, ['DEFAULT_METADATA']),
    'Documentation': (FG, ['DEFAULT_DOC_COMMENT_TAG', 'DEFAULT_DOC_COMMENT']),
    'Red': (FG, ['CONSOLE_RED_OUTPUT']),
    'Green': (FG, ['CONSOLE_GREEN_OUTPUT']),
    'Blue': (FG, ['CONSOLE_BLUE_OUTPUT']),
    'Yellow': (FG, ['CONSOLE_YELLOW_OUTPUT']),
    'Cyan': (FG, ['CONSOLE_CYAN_OUTPUT']),
    'Purple': (FG, ['CONSOLE_MAGENTA_OUTPUT']),
    'DiffInserted': (BG, ['DIFF_INSERTED']),
    'DiffDeleted': (BG, ['DIFF_DELETED']),
    'DiffModified': (BG, ['DIFF_MODIFIED']),
}


def normalize_hex(value: str) -> str:
    value = value.strip().lstrip('#')
    if len(value) <= 6:
        value = value.zfill(6)
    return '#' + value.upper()


class IntelliJScheme:
    def __init__(self, path: str):
        root = ET.parse(path).getroot()
        self.name = root.get('name', 'Converted Theme')
        self.colors: Dict[str, str] = {}
        for opt in root.findall('./colors/option'):
            if opt.get('value'):
                self.colors[opt.get('name')] = normalize_hex(opt.get('value'))
        self.attributes: Dict[str, Dict] = {}
        for opt in root.findall('./attributes/option'):
            entry: Dict = {'base': opt.get('baseAttributes')}
            value = opt.find('value')
            if value is not None:
                entry['props'] = {o.get('name'): o.get('value') for o in value.findall('option')
                                  if o.get('value')}
            self.attributes[opt.get('name')] = entry

    def attribute_props(self, name: str, depth: int = 0) -> Optional[Dict[str, str]]:
        """Own props if the attribute has a <value>, otherwise those of its baseAttributes."""
        entry = self.attributes.get(name)
        if entry is None or depth > 10:
            return None
        if 'props' in entry:
            return entry['props']
        return self.attribute_props(entry['base'], depth + 1) if entry['base'] else None

    def resolve(self, prop: str, sources: List[str]) -> Tuple[Optional[str], Dict[str, str]]:
        """First source defining `prop`: (hex color, that source's full props)."""
        for source in sources:
            if source.startswith('@'):
                if source[1:] in self.colors:
                    return self.colors[source[1:]], {}
                continue
            props = self.attribute_props(source)
            if props and props.get(prop):
                return normalize_hex(props[prop]), props
        return None, {}


class IntelliJToFleetConverter:
    def __init__(self, scheme: IntelliJScheme):
        self.scheme = scheme
        self.palette: Dict[str, str] = {}
        self.names_by_hex: Dict[str, str] = {}

    def add_to_palette(self, name: str, color: str) -> str:
        if color in self.names_by_hex:
            return self.names_by_hex[color]
        unique, n = name, 2
        while unique in self.palette:
            unique, n = f'{name}{n}', n + 1
        self.palette[unique] = color
        self.names_by_hex[color] = unique
        return unique

    def build_roles(self) -> None:
        resolved = {role: self.scheme.resolve(prop, sources)[0]
                    for role, (prop, sources) in PALETTE_ROLES.items()}
        base = resolved['Base'] or '#FFFFFF'
        resolved['Base'] = base
        resolved['Text'] = resolved['Text'] or ('#000000' if self.is_light(base) else '#FFFFFF')
        resolved['LineHighlight'] = resolved['LineHighlight'] or base
        resolved['Selection'] = resolved['Selection'] or resolved['LineHighlight']
        resolved['Mantle'] = resolved['Mantle'] or self.shift(base, -17 if self.is_light(base) else 20)
        # Roles are added by name even when colors repeat, since the UI mapping looks them up by name.
        for role, color in resolved.items():
            if color:
                self.palette[role] = color
                self.names_by_hex.setdefault(color, role)
        self.palette['Transparent'] = '#FFFFFF00'

    @staticmethod
    def is_light(color: str) -> bool:
        h = color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r * 299 + g * 587 + b * 114) / 1000 > 128

    @staticmethod
    def shift(color: str, amount: int) -> str:
        h = color.lstrip('#')
        return '#' + ''.join(f'{min(255, max(0, int(h[i:i + 2], 16) + amount)):02X}' for i in (0, 2, 4))

    @staticmethod
    def palette_name_for(fleet_key: str) -> str:
        return ''.join(part[:1].upper() + part[1:] for part in fleet_key.split('.'))

    def build_text_attributes(self) -> Dict[str, Dict]:
        base = self.palette['Base']
        resolved: Dict[str, Dict] = {}

        for key, (prop, sources) in TEXT_ATTRIBUTES.items():
            color, props = self.scheme.resolve(prop, sources)
            if color is None:
                continue
            ref = self.add_to_palette(self.palette_name_for(key), color)
            if prop == FG:
                attr: Dict = {'foregroundColor': ref}
                if props.get(BG) and normalize_hex(props[BG]) != base:
                    attr['backgroundColor'] = self.add_to_palette(
                        self.palette_name_for(key) + 'Background', normalize_hex(props[BG]))
                font_type = int(props.get('FONT_TYPE', '0') or 0)
                if font_type & 1:
                    attr['fontWeight'] = 'BOLD'
                if font_type & 2:
                    attr['fontStyle'] = 'ITALIC'
            elif prop == BG:
                attr = {'backgroundColor': ref}
            else:
                attr = {'scrollbarMarkColor': ref,
                        'textDecoration': {'color': ref, 'style': 'WAVY', 'type': 'UNDERLINE'}}
            resolved[key] = attr

        # Unresolved foreground keys inherit from their nearest resolved Fleet parent.
        for key, (prop, _) in TEXT_ATTRIBUTES.items():
            if key in resolved or prop != FG:
                continue
            parent = key
            while '.' in parent:
                parent = parent.rsplit('.', 1)[0]
                if parent in resolved:
                    break
            else:
                parent = 'editor.text.scheme'
            if parent in resolved:
                resolved[key] = {'foregroundColor': resolved[parent]['foregroundColor']}

        return {key: resolved[key] for key in TEXT_ATTRIBUTES if key in resolved}

    def convert(self) -> Dict:
        self.build_roles()
        text_attributes = self.build_text_attributes()
        ui = SublimeToFleetConverter()
        kind = ui.determine_theme_kind(self.palette['Base'])
        colors = ui.create_colors_from_globals({}, {}, self.palette, kind)
        return {
            'meta': {'theme.name': self.scheme.name, 'theme.kind': kind, 'theme.version': 1},
            'colors': colors,
            'textAttributes': text_attributes,
            'palette': self.palette,
        }


def main():
    parser = argparse.ArgumentParser(description='Convert IntelliJ color schemes to Fleet theme format')
    parser.add_argument('input', help='Input IntelliJ theme file (.icls or .xml)')
    parser.add_argument('output', help='Output Fleet theme file (.json)')
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1

    try:
        fleet_theme = IntelliJToFleetConverter(IntelliJScheme(args.input)).convert()
    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(fleet_theme, f, indent=2, ensure_ascii=False)

    print(f"✓ Converted: {args.input} -> {args.output}")
    print(f"  Theme: {fleet_theme['meta']['theme.name']}")
    print(f"  Kind: {fleet_theme['meta']['theme.kind']}")
    print(f"  Palette colors: {len(fleet_theme['palette'])}")
    print(f"  Text attributes: {len(fleet_theme['textAttributes'])}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
