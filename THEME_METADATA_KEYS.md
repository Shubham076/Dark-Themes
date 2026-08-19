# Discovering Every Valid Theme Key (`*.themeMetadata.json`)

IntelliJ ships a machine-readable registry of **every** UI key a `*.theme.json` may set,
each with a human-readable description. This is the authoritative list — if a key is not in
there, the platform does not read it and setting it is a silent no-op.

## Where the metadata lives

Two files, both inside `intellij.platform.ide.impl.jar`:

| File | Registry | Key count |
|------|----------|-----------|
| `themes/metadata/IntelliJPlatform.themeMetadata.json` | IntelliJ Platform keys (`EditorTabs.*`, `ToolWindow.*`, `HelpBrowser.*`, …) | ~854 |
| `themes/metadata/JDK.themeMetadata.json` | Swing/JDK component keys (`Component.*`, `Button.*`, `Tree.*`, …) | ~402 |

macOS path:

```bash
/Applications/IntelliJ\ IDEA\ CE.app/Contents/lib/intellij.platform.ide.impl.jar
```

> **Note:** older docs (including `EXTRACT_INTELLIJ_THEMES.md`) point at `app-client.jar`.
> That jar no longer exists in recent builds — the theme JSONs and the metadata both moved
> into `intellij.platform.ide.impl.jar`. Locate it yourself with:
>
> ```bash
> for j in /Applications/IntelliJ\ IDEA\ CE.app/Contents/lib/*.jar; do
>   unzip -l "$j" 2>/dev/null | grep -q "themeMetadata.json" && echo "$j"
> done
> ```

## Extracting

```bash
mkdir -p ~/intellij-theme-metadata && cd ~/intellij-theme-metadata

jar xf "/Applications/IntelliJ IDEA CE.app/Contents/lib/intellij.platform.ide.impl.jar" \
    themes/metadata/IntelliJPlatform.themeMetadata.json \
    themes/metadata/JDK.themeMetadata.json
```

Each file has the shape:

```json
{
  "name": "IntelliJ Platform",
  "fixed": false,
  "ui": [
    { "key": "ActionButton.focusedBorderColor", "description": "ActionButton border color when focused" }
  ]
}
```

## Querying without extracting

Dump every key + description, sorted:

```bash
python3 - <<'EOF'
import zipfile, json
JAR = "/Applications/IntelliJ IDEA CE.app/Contents/lib/intellij.platform.ide.impl.jar"
z = zipfile.ZipFile(JAR)
for name in ("themes/metadata/IntelliJPlatform.themeMetadata.json",
             "themes/metadata/JDK.themeMetadata.json"):
    for entry in json.loads(z.read(name))["ui"]:
        print(f'{entry["key"]:60} {entry.get("description","")}')
EOF
```

Search for a key prefix (e.g. everything under `Component.`):

```bash
python3 - <<'EOF'
import zipfile, json
PREFIX = "Component."          # change me
JAR = "/Applications/IntelliJ IDEA CE.app/Contents/lib/intellij.platform.ide.impl.jar"
z = zipfile.ZipFile(JAR)
for name in ("themes/metadata/IntelliJPlatform.themeMetadata.json",
             "themes/metadata/JDK.themeMetadata.json"):
    for entry in json.loads(z.read(name))["ui"]:
        if entry["key"].startswith(PREFIX):
            print(f'{entry["key"]:55} {entry.get("description","")}')
EOF
```

Once extracted, `jq` works too:

```bash
jq -r '.ui[] | "\(.key)\t\(.description)"' themes/metadata/JDK.themeMetadata.json \
  | grep -i '^ToolWindow'
```

## Verifying a key actually exists

Before adding a key to a theme, confirm it is registered. A key absent from **both**
metadata files is not applied by the IDE (and the theme JSON schema will flag it).

```bash
python3 - <<'EOF'
import zipfile, json
KEY = "Component.foreground"   # change me
JAR = "/Applications/IntelliJ IDEA CE.app/Contents/lib/intellij.platform.ide.impl.jar"
z = zipfile.ZipFile(JAR)
found = [
    e for n in ("themes/metadata/IntelliJPlatform.themeMetadata.json",
                "themes/metadata/JDK.themeMetadata.json")
    for e in json.loads(z.read(n))["ui"] if e["key"] == KEY
]
print(found or f"{KEY!r} is NOT a valid theme key")
EOF
```

`Component.foreground` is a real example of an **invalid** key — it does not exist in either
registry. Use the wildcard `"*": { "foreground": ... }` or per-component keys such as
`TextField.foreground` instead.

## Keys used by this plugin (reference)

Verified descriptions for the less obvious keys the themes in `src/main/resources/themes/` set:

### AI Assistant / help chat (`HelpBrowser.*`)

| Key | Description |
|-----|-------------|
| `HelpBrowser.UserMessage.background` | Background color of user messages in the help browser |
| `HelpBrowser.UserMessage.Snippet.border` | Border color of code snippets in user messages |
| `HelpBrowser.UserMessage.Snippet.MoreLines.background` | Background of the "more lines" indicator in user messages |
| `HelpBrowser.UserMessage.Snippet.MoreLines.hoverBackground` | …same, on hover |
| `HelpBrowser.UserMessage.Snippet.MoreLines.foreground` / `.hoverForeground` | Text color of the indicator |
| `HelpBrowser.HelpBrowserMessage.Snippet.border` | Border of code snippets in **assistant** messages |
| `HelpBrowser.HelpBrowserMessage.Snippet.MoreLines.*` | Assistant-side "more lines" indicator |
| `HelpBrowser.titleHighlightForeground` | Foreground of highlighted titles in the help browser |

Syntax highlighting *inside* chat code blocks comes from the editor scheme XML, not these keys.

### Input focus (`Component.*`, JDK registry)

| Key | Description |
|-----|-------------|
| `Component.focusColor` | Outer border for a button, text field, combo box, or spinner when focused |
| `Component.focusedBorderColor` | Inner 1 px-wide border for a text field, combo box, or spinner when focused |
| `Component.focusWidth` | Border width when focused |
| `Component.borderColor` / `Component.disabledBorderColor` | Resting / disabled border for text field, combo box, spinner |
| `Component.infoForeground` | Gray info text in fields, combo boxes, lists, trees, tables, empty areas |
| `Component.iconColor` / `Component.hoverIconColor` | Hardcoded (non-SVG) icon inside a component |
| `Component.errorFocusColor` / `Component.inactiveErrorFocusColor` | Validation error state (focused / unfocused) |
| `Component.warningFocusColor` / `Component.inactiveWarningFocusColor` | Validation warning state (focused / unfocused) |

Every theme here defines a `focus_color` palette entry sourced from its editor scheme's
`DEFAULT_KEYWORD` foreground, wired to `focusColor` + `focusedBorderColor` with
`focusWidth: 1`.

## Related docs

- `EXTRACT_INTELLIJ_THEMES.md` — extracting the built-in `*.theme.json` files themselves
- `Conversion.md` — converting schemes to other editors
