# Dark-Themes — notes for agents

## Layout

- Themes are resources only: `src/main/resources/themes/<name>.theme.json` (UI colors) paired with
  `<name>.xml` (editor color scheme). Every theme must be registered as a `themeProvider` in
  `src/main/resources/META-INF/plugin.xml`.
- Kotlin sources live in `src/main/kotlin`. The Kotlin plugin is already applied in
  `build.gradle.kts`, so no build changes are needed to add code.
- Conversion scripts at the repo root (`intellij_to_zed.py`, `intellij_to_sublime_json.py`,
  `sublime_to_fleet.py`) port themes to other editors.

## Verification

```sh
./gradlew compileKotlin      # fast feedback on Kotlin changes
./gradlew buildPlugin        # full package, also runs verifyPluginConfiguration
```

`buildSearchableOptions` runs a headless IDE and prints `no ComponentUI class for: ...` errors plus
`JCEF is manually disabled in headless env` warnings. Both are noise from the indexing run and do
not indicate a failure — check the final `BUILD SUCCESSFUL` line.

Targets `pluginSinceBuild = 223` (2022.3) through `pluginUntilBuild = 262.*`, so avoid platform APIs
newer than 2022.3 (e.g. `ProjectActivity`, `AnAction.getActionUpdateThread`).

## Windsurf/Cascade sync

`src/main/kotlin/.../cascade/` makes the Windsurf plugin's Cascade chat panel follow the active
theme. All configuration is the `tokens()` map in `CascadeSync`, one line per CSS custom property,
fed by exactly two lookups — `getFromTheme(key)` for the `.theme.json` and
`getFromEditorScheme(key)` for the `.xml`:

```kotlin
"--bg-elevated" to getFromEditorScheme(EditorColors.CARET_ROW_COLOR),
"--tint-tertiary" to getFromTheme("HelpBrowser.UserMessage.background"),
```

`getFromTheme` reads any key from the `.theme.json` `ui` section, including keys no Swing component
uses, because the IDE loads them all into `UIManager` defaults. Missing or translucent colors
resolve against `JBColor.PanelBackground`. Never write a literal color here.

The second config map is `rules()`, selector to property and value, for what a panel-wide token
cannot express — use it when only some of the elements sharing a token should move. It goes into one
reused `<style id="darkthemes-cascade-sync">` instead of the inline style, since a rule cannot be
inlined:

```kotlin
""".chat-client-root .bg-tint-tertiary.mb-\[-24px\]""" to mapOf("background-color" to "transparent"),
```

The key is any CSS selector, written out in a raw string. Confine it to `.chat-client-root` and
name at least two classes: Cascade's own utilities are `.chat-client-root .<class>`, so one class
only ties and leaves the outcome to stylesheet order. Tailwind's `[`, `]`, `/` and `:` belong to the
class name and need a backslash (`.mb-\[-24px\]`, `.group\/message-wrapper`); `jsString` keeps those
backslashes intact on the way into the script. Values are plain CSS, not the channel triple tokens
need, so a theme color is `"rgb(${getFromTheme(key)})"`.

To inspect the panel, set the registry key `ide.browser.jcef.contextMenu.devTools.enabled` to true
(no restart), then right-click in Cascade → **Open DevTools**. Do this before writing a token or a
rule: reading the minified bundle tells you what Cascade *can* render, not what it does, and it
carries more than one implementation of the prompt box. With an element selected, `$0.className`
gives the selector to use and `getComputedStyle($0).backgroundImage` the layer that paints it.

Context that is expensive to rediscover:

- Cascade is a JCEF web view served by the Windsurf language server on `http://127.0.0.1:<port>`.
  Its CSS and its React bundle are embedded in the `language_server_macos_arm` binary under
  `~/Library/Application Support/JetBrains/<IDE>/plugins/codeium/<hash>/`, not on disk as files.
  `rg -a -o -b '<needle>' language_server_macos_arm` gives byte offsets to seek to: the stylesheet
  sits around 43.1-43.6 MB (search `.bg-<utility> {`) and the components after it (search a
  Tailwind class string). Read the class strings to learn the DOM; there is no devtools.
- Its design tokens (`--bg-elevated`, `--bg-page`, `--bg-wash`, …) are **hardcoded constants**
  chosen by a single light/dark switch. They are only regenerated from the active color theme on
  VS Code/Windsurf (`designTokenCss.ts`); JetBrains loads `jetbrains.css`, which does not do this.
- The Windsurf plugin injects ~35 theme-derived vars, all named `--codeium-*`, onto
  `document.documentElement`. `--codeium-chat-background` is `JBColor.PanelBackground`.
- Overrides must land on `.chat-client-root` itself (inline style) or on a `.chat-client-root.dark`
  rule. A `:root` / `<html>` override loses, because the bundled rule declares the property
  directly on `.chat-client-root` and that beats an inherited value.
- `--bg-elevated` is consumed as `rgb(var(--bg-elevated))`, so its value must be space-separated
  channel numbers (`"31 31 31"`), never a CSS color.
- The `--tint-*` tokens are **translucent washes**, which is why they appear to follow the theme
  even though nothing reads it: `--tint-tertiary` is `255 255 255 / 0.03` in dark and
  `0 0 0 / 0.04` in light, layered over `var(--codeium-chat-background)`, so the chat bubble is
  always "panel background plus 3% white". No JS ever writes `--tint-*` and no `--tint-*` value
  references a `--codeium-*` var, so those are the only two possible values. Consequence: an
  arbitrary theme color usually is **not** reachable by any alpha over the panel background
  (e.g. Aura's `#454A5E` over `#293152` would need per-channel alphas 0.131/0.121/0.069), so the
  override has to emit opaque channels. We drive `--tint-tertiary` from
  `HelpBrowser.UserMessage.background` (`user_message_background` in every theme here).
- Tokens are declared twice, mirrored: `.chat-client-root.dark, .chat-client-root.light
  .theme-inverse` and `.chat-client-root.light, .chat-client-root.dark .theme-inverse`. That is
  what keeps `.theme-inverse` subtrees inverted despite an inline override on the root — the
  descendant rule beats an inherited inline value.
- `--tint-tertiary` is not just the chat bubble: it also paints `hover:bg-tint-tertiary` on
  buttons/rows/menu items, avatar circles, attachment chips, the message-action toolbar and
  settings cards. Overriding the token changes all of them.
- **A tint is not a `background-color`.** `bg-tint-*` paints a `background-image:
  linear-gradient(tint, tint)` over `background-color: var(--codeium-chat-background)`, so the tint
  composites over the panel background wherever the element sits. Confirmed in devtools on the
  beard row: `backgroundColor` is `rgb(248, 248, 248)` while `backgroundImage` is
  `linear-gradient(rgb(206, 225, 240), rgb(206, 225, 240))`. Clearing one needs the `background`
  shorthand, which is what `NO_BACKGROUND` in `CascadeSync` uses; `transparent` alone only removes
  the layer underneath. Tints also arrive via `.before\:bg-tint-tertiary::before` and
  `.hover\:bg-tint-tertiary:hover`.
- **Rules need `!important`; specificity is not enough.** A `.chat-client-root
  .bg-tint-tertiary.mt-\[-24px\]` rule (0,3,0) that verifiably matched (`$0.matches(…)` true, the
  `<style>` present with the right text) still lost to Cascade. Its utilities appear to be built
  with Tailwind's `important: true`, and its prompt-box rows are framer-motion `div`s that write
  inline styles — a stylesheet `!important` is the only thing that beats both. Note an inline
  `$0.style.background = 'none'` in devtools proves nothing about a rule: inline outranks every
  stylesheet declaration anyway.
- The stylesheet inside the on-disk `language_server_macos_arm` can be a different build from the
  server actually running (its `.bg-tint-tertiary` is a plain `background-color`), so treat the
  binary as a lead and devtools as the truth.
- The worst of those are the prompt box's **eyebrow and beard rows**, which Cascade hangs out from
  behind the box with a negative margin, so an opaque `--tint-tertiary` reads as a slab:
  `cn("bg-tint-tertiary relative mb-[-24px] …")` above and `mt-[-24px]` below. `rules()` clears
  both to `background-color: transparent`, keyed on the wash's class plus the margin's. Prefer
  that over touching the token; do not try to reach these rows by adding a class in JS, React
  re-renders wipe it.
- Do not confuse those rows with the `group/beard-band` overlay (`absolute inset-0`,
  `bg-bg-elevated-wax backdrop-blur`) that fades in when the beard opens. Its `bg-tint-tertiary`
  variants are all `light:`-prefixed, so under a dark theme that overlay is `--bg-elevated-wax`
  only.
- The browser is reached reflectively: `JBCefBrowser$MyPanel.getJBCefBrowser()` →
  `getCefBrowser()` → `executeJavaScript`. `MyPanel` is not open API, so keep every hop in
  `runCatching` and expect it to break on Windsurf plugin updates.
- **`executeJavaScript` succeeding does not mean the script ran.** Before the language server has
  booted, the browser sits on `about:blank`; the call returns normally and the script context is
  then discarded on navigation. This is why the colors applied on a theme change but not after an
  IDE restart. Always gate on `CefBrowser.getURL().startsWith("http")` plus `hasDocument()` and
  `!isLoading()`, and keep polling (~2 min) until that gate passes — a cold start with indexing
  needs far longer than a few seconds.
- `org.cef.browser.CefBrowser` lives in
  `plugins/jcef-plugin/lib/modules/intellij.libraries.jcef.jar`, not in the JBR. Confirmed members:
  `getURL()`, `hasDocument()`, `isLoading()`, `executeJavaScript(String, String, int)`.
- There is **no startup hook usable across 223-262**: `postStartupActivity` takes `StartupActivity`
  in 2022.3, but every bundled 2026.2 implementation uses `ProjectActivity`, which does not exist
  in 2022.3. `ToolWindowManagerListener` via `<projectListeners>` is the portable substitute —
  wire `toolWindowShown`, `toolWindowsRegistered` and `stateChanged`, since which one fires on a
  restore depends on the saved layout.
- Toggle at runtime with the registry key `darkthemes.cascade.sync`.
