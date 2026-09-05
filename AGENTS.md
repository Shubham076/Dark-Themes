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

## AI Assistant chat input

`src/main/kotlin/.../aiassistant/` gives the AI Assistant's chat input box its own background.
A theme opts in by defining `AIAssistantInput.background` in its `ui` section; with the key absent
nothing happens. Only `aura.theme.json` has it so far.

The IDE-side inspection tool is the **UI Inspector** (`idea.is.internal=true` in Help → Edit Custom
Properties, then Ctrl+Alt+Click), whose Color Key Picker names the color's source — that is how the
box was traced to the editor's `TEXT` attribute background.

- The box is `AIAssistantNewToolbarInput` in `com.intellij.ml.llm.core.chat.ui.chat.input`, which
  lives in `ml-llm/lib/modules/intellij.ml.llm.chat.jar` (not `ml-llm.jar`, despite the package).
- It cannot be recolored from outside: `setBackground` is compiled to a bare `return`, and
  `getBackground()` returns `editorTextField.editor.colorsScheme.defaultBackground`.
  `AIAssistantInputBorder.paintBorder` fills from that same `EditorEx.colorsScheme` too.
- Both read the *editor's* scheme, not the global one, so the lever is a `DelegateColorScheme` on
  that single editor overriding `getDefaultBackground()`. One wrap moves the text area, the strip
  behind the toolbar and the border fill together, and affects no other editor.
- The theme JSON alone cannot reach it. All of `ml-llm.jar` contains exactly one named UI key,
  `Editor.SearchField.background`, and that belongs to the inline code-generation popup.
- Identify the editor by walking its `contentComponent` parents for
  `AIAssistantInputEditorTextField`, and do it in an `invokeLater` from
  `EditorFactoryListener.editorCreated` — at creation time the editor is not in the component tree
  yet. File type is no use: the field is built with `FileTypes.PLAIN_TEXT`, even though the plugin
  ships a whole `ChatInputLanguage` (`ChatInput`) for the box's completion and folding.
- The delegate reads `UIManager` on every call, so the color itself needs no re-wrapping — but
  **the assistant throws the wrapper away on every theme change**, so re-wrapping is mandatory:
  `AIAssistantInputEditorLifecycleController.updateTheme` calls
  `AIAssistantInputEditorTextField.applyIdeThemeColorScheme`, which is
  `editor.setColorsScheme(editor.createBoundColorSchemeDelegate(schemeForCurrentUITheme))`. It runs
  from their own `LafManagerListener` (subscribed through `launchOnShow`, so only while the panel is
  showing) and from `initEditor`.
- Because both listeners hear the same event and message bus order is not ours to choose, our
  re-wrap must be deferred with `invokeLater`; anything synchronous can be overwritten. Symptom of
  getting this wrong: the box keeps the old editor background after a theme switch and only turns
  the right color once a message is sent — sending recreates the document, which recreates the
  editor, which fires `editorCreated` again.
- Re-wrap over whatever scheme is there, unwrapping our own first (`DelegateColorScheme.getDelegate`)
  rather than rebuilding the bound delegate: theirs carries the editor font name/size and line
  spacing that `applyIdeThemeColorScheme` sets right after creating it.
- The same `updateTheme` runs `UIUtil.setBackgroundRecursively(toolbar, editorTextField.background)`
  over every `ActionToolbar` in the input, and `ActionButtonLook.getStateBackground` returns
  `component.isBackgroundSet() ? component.getBackground() : null` for the idle state (with
  `paintBorder` adding a hover border on top). So an explicit background makes every toolbar button
  paint a filled rounded slab — the `+`, the mode selector, the context-usage circle and the send
  `ToolbarSplitButton` all showed as boxes of the *editor* background over our box color, since the
  sweep runs before we re-wrap. `clearToolbarBackgrounds` unsets it instead of recoloring it, which
  leaves nothing painted at rest and `ActionButton.hoverBackground` in charge of hover/pressed.
- **A forced background beats the scheme, and a cold start sets one.** `EditorTextField`'s
  `initOneLineMode` ends every editor it builds with `editor.setBackgroundColor(getBackground())`,
  and `EditorImpl.getBackgroundColor()` returns that forced color ahead of
  `myScheme.getDefaultBackground()` (the scroll pane is a `JBColor.lazy` over it, so it is never
  stale — the forced value simply wins). The assistant's `getBackground()` override reads the
  *editor's* scheme, so it only works once an editor exists; while `myEditor` is still null it falls
  through to `UIUtil.getTextFieldBackground()`. Net effect on a cold start: the box turns our color
  but the text area stays `TextField.background`. Sending a message hides it, because the
  replacement editor is built while `myEditor` still points at the previous, wrapped editor — which
  is why this looked fixed. `dropForcedBackground` clears it by passing *our* color:
  `EditorImpl.setBackgroundColor` drops the override when the color equals what the scheme would
  have returned anyway.
- **Clearing the forced background is necessary but not sufficient — the text area is the scroll
  pane's viewport.** `AIAssistantInputEditorTextField.createEditor` calls
  `getContentComponent().setOpaque(false)`, and `EditorImpl` touches the viewport exactly once, via
  `setViewportView` — it never sets its background or its opacity (it only wraps the *scroll pane's*
  background in a `JBColor.lazy(this::getBackgroundColor)`). So the empty part of the box is painted
  by the LaF's `Viewport.background`, which a theme's `"*": { "background": ... }` wildcard sets to
  the panel color. Hence `editor.scrollPane.viewport.background = ours` alongside the forced-color
  clear. Diagnostics from a cold start, one editor, before and after our pass:
  `before: editorBg=#FAFAFA viewport=#FAFAFA/opaque=true` → `after: editorBg=#DEDEDE
  viewport=#DEDEDE`. Fixing only the forced color leaves the viewport painting over it, which is
  exactly what "the box is right but the text area is white" looks like.
- **`editor.colorsScheme` never returns our wrapper.** `EditorImpl.setColorsScheme` re-wraps
  whatever you hand it in its own `EditorColorSchemeDelegate` (it logs "Will wrap it with
  MyColorSchemeDelegate" for unexpected types), so `scheme is ThemedInputScheme` is always false and
  any code branching on it is dead. Walk the chain with `DelegateColorScheme.getDelegate()` instead.
  Colors are unaffected — the outer delegate forwards `getDefaultBackground()` — but re-wrapping
  blindly nests a new pair of delegates on every pass, and a theme switch triggers two passes
  (`LafManagerListener` *and* `EditorColorsListener`).
- **`setBackground(null)` fires the *inherited* color as the event's new value.** `Component`:
  ```java
  background = c;
  if (peer != null) { c = getBackground(); ... }   // field is null now, so this inherits
  firePropertyChange("background", oldColor, c);   // fires the parent's color, not null
  ```
  So a `PropertyChangeListener("background")` that re-clears whenever `newValue != null` recurses
  until the stack dies — a `StackOverflowError` through `PropertyChangeSupport.fire`, and only on
  components that already have a peer. Ask `isBackgroundSet()` instead: it reads the component's own
  field and does not inherit, so it goes false as soon as the clear lands and the second hop stops.
  Verified on the JBR: after `setBackground(null)` on a realized child of a red panel, the event
  says `newValue=red` while `isBackgroundSet()` is `false`.
- **Re-wrapping the editor's scheme on every pass is not free.** `EditorImpl.setColorsScheme` keeps
  what it is handed inside a *new* `EditorColorSchemeDelegate` and then calls `reinitSettings()`, so
  a pass that runs often (ours runs on editor creation, both theme-change listeners, and every
  re-show) nests two delegates each time — lengthening the chain every attribute lookup walks while
  painting — and re-inits the editor. Wrap once, guarded by a chain walk, and write the forced color
  and the viewport only when they differ. Symptom of getting this wrong: the panel gets slower the
  longer the session runs, with no freeze in the log to point at.
- **When two suspects share a color value, stop measuring and instrument.** `Viewport.background`
  and `TextField.background` both resolve through the `*` wildcard to the same panel color, so no
  screenshot could separate them; two rounds of inference were wasted before a temporary
  `Logger.getInstance("darkthemes.aiassistant").warn(...)` dump of every color source (scheme class
  and default, `getBackgroundColor()`, scroll pane, viewport + opacity, content component + opacity,
  and each component under the input with its background) settled it in one restart. `idea.log` is
  readable directly at `~/Library/Logs/JetBrains/<IDE>/idea.log`; log at WARN so it is never
  filtered, and dump `before`/`after` plus a `javax.swing.Timer` pass a few seconds later to catch
  the async toolbar build.
- **Verify what is actually running before believing a test result.** Plugin jars are read at
  startup, so an install cannot take effect in the running session: compare the session's
  `AppStarter - Loaded custom plugins` timestamp against the jar's mtime. That line also prints the
  version from the jar's `plugin.xml`, which is *not* the filename — a renamed jar reports its old
  version, and rebuilding without bumping `pluginVersion` in `gradle.properties` makes the log
  useless for telling builds apart. When in doubt, grep the installed jar for a string only the new
  build contains.
- `editorTextField.getEditor(true)` returns null while the field is outside the Swing hierarchy —
  it refuses to build one. The controller's `initEditor` tolerates that (its editor block is
  null-guarded) and still runs `updateTheme`, so on a cold start the toolbar sweep spreads
  `TextField.background`, not any editor color. Don't assume an editor exists just because their
  init ran.
- `Component.isBackgroundSet()` is a plain null check on the component's own field; only
  `getBackground()` inherits from the parent. So unsetting a button's background really does stop
  `ActionButtonLook` from filling it — verified with a two-line Swing program on the JBR.
- **The toolbars are rebuilt asynchronously, so one clearing pass is never enough.**
  `AiChatInputToolbarFactory.watchControlsAndRebuild` follows a flow: it fires well after a cold
  start as models and agents resolve, and again when a request starts and send becomes stop. New
  children arrive after our pass, and the `CustomComponentAction` ones (mode selector,
  context-usage circle) are `JPanel`s whose constructor installs `Panel.background` — a slab again.
  Hence the `ContainerListener`, installed on *every* container under the input rather than only on
  the toolbars, since a rebuild can bring a new `ActionToolbar` with it. Do not remove it: it is
  what keeps the backgrounds clear, and deleting it once already regressed this.
- `AiChatInputActionButtonStyle.apply` sets only the foreground and the cursor — it is not a
  background source. `ActionToolbarImpl`, `ActionButton` and `ActionButtonWithText` never touch
  backgrounds either, and `setBackgroundRecursively` appears exactly once in the whole chat jar
  (that one sweep), so any slab you see is either that sweep or a component coloring itself.
- To tell these apart, **measure the screenshot** instead of guessing: `python3` with Pillow is
  available, and a `Counter` over the pixels plus a coarse grid dump names every surface. The
  theme's `background`, `TextField.background` and the `.xml` `TEXT` background are often within a
  couple of RGB points of each other (ayuLight: `#FAFAFA` vs `#F8F9FA`), and which one shows tells
  you which code path ran. Absence is evidence too — no `#F8F9FA` pixel anywhere proved the editor
  scheme was not involved.
- Scope that sweep to `ActionToolbar` subtrees, as they do. The agent/model row below the box is
  `getBottomToolbarPanel()`: the input builds it but `AIAssistantChatPanel` re-parents it, so it is
  outside the input's hierarchy and no sweep — theirs or ours — reaches it.
- To read their code: `unzip` the package out of `intellij.ml.llm.chat.jar` and run the IDE's own
  Fernflower with the IDE's JBR (a system `java` is too old for those class files):
  `"/Applications/IntelliJ IDEA CE.app/Contents/jbr/Contents/Home/bin/java" -cp ".../plugins/java-decompiler/lib/java-decompiler.jar" org.jetbrains.java.decompiler.main.decompiler.ConsoleDecompiler -hdc=0 -dgs=1 <classes> <outdir>`.

## AI Assistant chat messages (Compose)

The message area around the input is **not Swing** — it is Compose/Jewel, in
`intellij.ml.llm.agents.frontend.jar`, so the UI Inspector cannot reach it and only the keys that
plugin asks for exist. `AIAColors.Companion.getColor` builds them as
`"AIAssistant.Chat" + <component> + <"Default"|ForceColor prefix> + <colorName>`, e.g.
`AIAssistant.Chat.StepCard.Default.background.color` (see the nested `AIAssistant.Chat.StepCard`
block in `aura.theme.json`). There are exactly three component names — `StepCard`,
`AgentEventBlock`, `ChatHistory` — plus the standalone
`AIAssistant.Chat.AssistantMessage.inlineCodeBackground` for inline `` `code` `` spans (default
`#FFFFFF10`). Anything not in that list is not themeable.

- **A fenced code block's fill is the editor background and cannot be overridden.**
  `CodeBlockRenderer` takes only its *border* from a key (`stepCard.borderColor`); the fill comes
  from `MarkdownStyling.Code.Fenced.background`, and `ProvideAIAssistantMarkdownStyling` passes
  `code = null`, so Jewel's default applies:
  `BridgeMarkdownStylingKt.getBlockBackgroundColor()` = `retrieveEditorColorScheme()
  .getDefaultBackground()`, i.e. the *globally active* scheme's `TEXT` background. Investigated and
  rejected: mutating the remembered styling (5+ hops of Compose-desktop internals into
  `CompositionImpl.slotTable` after every LaF change), a bytecode agent (needs
  `-Djdk.attach.allowAttachSelf`), and lying about the global scheme's default background (leaks to
  every non-editor consumer, and `setAttributes` can persist into the user's saved
  `colors.scheme.xml`). Treat the fill as fixed: either match the card to it or accept the inset
  look. Note the code text is highlighted from the same scheme, so a card-colored fill would also
  cost token contrast.
- There is no way back to a Swing message area: none of `ml-llm`'s 451 registry keys switch the
  renderer (`llm.chat.history.new.enabled` is the history view only,
  `llm.chat.detached.compose.panel.*` are just panel caches).
- `AIAColors` also carries `editorBackground`, `editorForeground` and `hoverBackground` from
  `JBColors`, but nothing reads `editorBackground` — do not mistake it for the code block's.
