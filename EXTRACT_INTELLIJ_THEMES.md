# How to Extract Built-in IntelliJ Theme Files

This guide shows how to extract and examine IntelliJ IDEA's built-in theme files.

## Prerequisites
- IntelliJ IDEA installed (Community or Ultimate Edition)
- `jar` command available (comes with Java JDK)

## Finding IntelliJ Installation

### macOS
```bash
# IntelliJ IDEA Community Edition
/Applications/IntelliJ\ IDEA\ CE.app/Contents/lib/

# IntelliJ IDEA Ultimate
/Applications/IntelliJ\ IDEA.app/Contents/lib/
```

### Windows
```bash
# Usually located at:
C:\Program Files\JetBrains\IntelliJ IDEA Community Edition\lib\
# or
C:\Program Files\JetBrains\IntelliJ IDEA\lib\
```

### Linux
```bash
# Usually located at:
/opt/idea/lib/
# or
~/idea/lib/
```

## Commands to Extract Theme Files

### 1. List All Available Themes
```bash
# List all theme files in the jar
jar tf "/Applications/IntelliJ IDEA CE.app/Contents/lib/app-client.jar" | grep -i "theme.*\.json"
```

### 2. Extract Specific Theme Files

```bash
# Create a temporary directory for extraction
mkdir ~/intellij-themes
cd ~/intellij-themes

# Extract main themes
jar xf "/Applications/IntelliJ IDEA CE.app/Contents/lib/app-client.jar" \
    themes/darcula.theme.json \
    themes/Light.theme.json \
    themes/intellijlaf.theme.json \
    themes/HighContrast.theme.json

# Extract experimental UI themes
jar xf "/Applications/IntelliJ IDEA CE.app/Contents/lib/app-client.jar" \
    themes/expUI/expUI_dark.theme.json \
    themes/expUI/expUI_light.theme.json \
    themes/expUI/expUI_light_with_light_header.theme.json

# Extract island themes (newer UI)
jar xf "/Applications/IntelliJ IDEA CE.app/Contents/lib/app-client.jar" \
    themes/islands/ManyIslandsDark.theme.json \
    themes/islands/ManyIslandsLight.theme.json
```

### 3. Extract All Theme Files at Once
```bash
# Extract all theme-related files
cd ~/intellij-themes
jar xf "/Applications/IntelliJ IDEA CE.app/Contents/lib/app-client.jar" "themes/*"
```

### 4. Extract Editor Schemes (XML)
```bash
# Editor schemes define syntax highlighting
jar xf "/Applications/IntelliJ IDEA CE.app/Contents/lib/app-client.jar" \
    themes/Light.xml \
    themes/highContrastScheme.xml \
    themes/expUI/expUI_darculaContrastScheme.xml \
    themes/expUI/expUI_darkScheme.xml \
    themes/expUI/expUI_lightScheme.xml
```

## Available Built-in Themes

| Theme Name | File Path | Parent Theme | Description |
|------------|-----------|--------------|-------------|
| Darcula | `themes/darcula.theme.json` | None | Classic dark theme |
| IntelliJ Light | `themes/Light.theme.json` | IntelliJ | Standard light theme |
| IntelliJ | `themes/intellijlaf.theme.json` | Darcula | Base light theme |
| Light with Light Header | `themes/expUI/expUI_light_with_light_header.theme.json` | ExperimentalLight | New UI light theme |
| Light (Experimental) | `themes/expUI/expUI_light.theme.json` | IntelliJ | Experimental light base |
| Dark (Experimental) | `themes/expUI/expUI_dark.theme.json` | - | Experimental dark theme |
| High Contrast | `themes/HighContrast.theme.json` | - | High contrast theme |

## Theme Hierarchy

```
Darcula (base dark)
  └── IntelliJ (base light, despite parent)
      ├── Light (IntelliJ Light)
      └── ExperimentalLight
          └── Light with Light Header
```

## Parent Theme References in Custom Themes

When creating custom themes, you can reference these parent themes:

```json
{
  "parentTheme": "IntelliJ",              // Base light theme
  "parentTheme": "Darcula",               // Base dark theme
  "parentTheme": "ExperimentalLight",     // New UI light base
  "parentTheme": "ExperimentalLightWithLightHeader", // Internal name for expUI_light_with_light_header
}
```

## Important Properties from Parent Themes

Parent themes provide:
- Icon color palettes (`icons.ColorPalette`)
- UI component styles (buttons, scrollbars, tabs)
- Progress indicators and spinner colors
- Default color definitions
- Platform-specific adjustments

## Examining Theme Contents

```bash
# View theme structure
cat ~/intellij-themes/themes/Light.theme.json | jq '.'

# Check specific properties
cat ~/intellij-themes/themes/Light.theme.json | jq '.ui.ProgressBar'

# Find icon definitions
cat ~/intellij-themes/themes/intellijlaf.theme.json | jq '.icons'
```

## Notes

1. **Theme files location**: The main themes are in `app-client.jar`, not in separate files
2. **Parent themes**: Using a parent theme inherits all its properties, which you can then override
3. **Icon colors**: Critical for UI elements like loading spinners - inherited from parent themes
4. **Version differences**: Theme structure may vary between IntelliJ versions

## Tips for Custom Theme Development

1. Always specify a `parentTheme` for light themes to inherit proper icon colors
2. Use `"parentTheme": "ExperimentalLightWithLightHeader"` for modern light themes
3. Use `"parentTheme": "Darcula"` for dark themes
4. Check parent theme properties before defining custom ones to avoid redundancy
