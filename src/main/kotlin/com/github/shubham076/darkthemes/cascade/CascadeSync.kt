package com.github.shubham076.darkthemes.cascade

import com.intellij.openapi.Disposable
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.editor.colors.ColorKey
import com.intellij.openapi.editor.colors.EditorColors
import com.intellij.openapi.editor.colors.EditorColorsManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.util.registry.Registry
import com.intellij.openapi.wm.ToolWindowManager
import com.intellij.ui.JBColor
import com.intellij.util.Alarm
import java.awt.Color
import java.awt.Component
import java.awt.Container
import javax.swing.UIManager
import kotlin.math.roundToInt

/**
 * Recolors the Windsurf/Cascade chat panel to match the active theme.
 *
 * Cascade is a JCEF web view whose colors are hardcoded per light/dark and never derived from the
 * IDE theme on JetBrains, so it stays near-black under any theme. We inject the theme's colors as
 * inline CSS custom properties on `.chat-client-root`, which outrank Cascade's own stylesheet.
 *
 * [tokens] and [rules] are the whole configuration; everything below them is plumbing. `AGENTS.md`
 * has the findings behind all of this.
 */
class CascadeSync(private val project: Project) : Disposable {

    private val alarm = Alarm(Alarm.ThreadToUse.SWING_THREAD, this)

    /**
     * Cascade CSS custom property to the theme color it should take, one line per property.
     **/
    private fun tokens(): Map<String, String> = mapOf(
        "--bg-elevated" to getFromEditorScheme(EditorColors.CARET_ROW_COLOR),
        "--bg-elevated-wax" to getFromEditorScheme(EditorColors.CARET_ROW_COLOR),
        "--tint-tertiary" to getFromTheme("HelpBrowser.UserMessage.background"),
//        "--tint-tertiary" to getFromEditorScheme(EditorColors.CARET_ROW_COLOR),
    )

    /**
     *
     * Any selector works as a key, so write it as plain CSS in a raw string. Two conventions the
     * panel forces: confine it to `.chat-client-root`, since Cascade's own stylesheet does and an
     * unscoped rule would also hit the IDE's other web views; and name enough classes to identify
     * the element, since specificity alone does not win here — see [NO_BACKGROUND]. Tailwind's
     * `[`, `]`, `/` and `:` are part of the class name and need a backslash, hence `.mb-\[-24px\]`.
     *
     * Values are plain CSS too, not the channel triple tokens need, so a theme color reads
     * `"rgb(${getFromTheme(key)})"`.
     **/
    private fun rules(): Map<String, Map<String, String>> = mapOf(
        """.chat-client-root .bg-tint-tertiary.mb-\[-24px\]""" to NO_BACKGROUND,
        """.chat-client-root .bg-tint-tertiary.mt-\[-24px\]""" to NO_BACKGROUND,
    )

    /** Any key from the `ui` section of the active `<name>.theme.json`. */
    private fun getFromTheme(key: String) = cssChannels(UIManager.getColor(key))

    /** Any color from the active `<name>.xml` editor scheme. */
    private fun getFromEditorScheme(key: ColorKey) =
        cssChannels(EditorColorsManager.getInstance().schemeForCurrentUITheme.getColor(key))

    /**
     * Cascade reads these tokens as `rgb(var(--token))`, so a value has to be space-separated
     * channels (`"69 74 94"`) and not a CSS color. Translucent and missing colors are resolved
     * against `JBColor.PanelBackground`, the surface Cascade paints on.
     */
    private fun cssChannels(color: Color?): String {
        val panel = JBColor.PanelBackground
        val opaque = color?.let { blend(it, panel) } ?: panel
        return "${opaque.red} ${opaque.green} ${opaque.blue}"
    }

    private fun blend(color: Color, background: Color): Color {
        if (color.alpha == 255) return color
        val alpha = color.alpha / 255.0
        fun channel(front: Int, back: Int) =
            (front * alpha + back * (1 - alpha)).roundToInt().coerceIn(0, 255)
        return Color(
            channel(color.red, background.red),
            channel(color.green, background.green),
            channel(color.blue, background.blue),
        )
    }

    // --- plumbing --------------------------------------------------------------------------

    /**
     * Debounced sync that keeps polling until the web view actually serves the chat client.
     *
     * On a cold start the browser sits on `about:blank` while the language server boots, and
     * `executeJavaScript` there succeeds but is discarded on navigation. So we retry until
     * [isReady] passes, then apply once more in case the React root mounted late.
     */
    fun requestSync() {
        if (!isEnabled()) return
        alarm.cancelAllRequests()
        scheduleAttempt(MAX_ATTEMPTS, delayMs = 0)
    }

    private fun scheduleAttempt(attemptsLeft: Int, delayMs: Int) {
        if (attemptsLeft <= 0) return
        alarm.addRequest({
            if (syncNow() > 0) {
                alarm.addRequest({ syncNow() }, REAPPLY_DELAY_MS)
            } else {
                scheduleAttempt(attemptsLeft - 1, POLL_INTERVAL_MS)
            }
        }, delayMs)
    }

    /** Applies the tokens immediately. Returns the number of loaded web views reached. */
    fun syncNow(): Int {
        if (project.isDisposed || !isEnabled()) return 0
        val ready = findCefBrowsers().filter(::isReady)
        if (ready.isEmpty()) return 0
        val script = buildScript(tokens(), rules())
        return ready.count { executeJs(it, script) }
    }

    override fun dispose() = Unit

    /**
     * Walks the Cascade tool window for JCEF panels. `JBCefBrowser$MyPanel.getJBCefBrowser()` is
     * public but not open API, so every hop is reflective and expected to break on plugin updates.
     */
    private fun findCefBrowsers(): List<Any> {
        val toolWindow = ToolWindowManager.getInstance(project).getToolWindow(CASCADE_TOOL_WINDOW_ID)
            ?: return emptyList()
        val contentManager = toolWindow.contentManagerIfCreated ?: return emptyList()

        val found = ArrayList<Any>()
        contentManager.contents.forEach { collectCefBrowsers(it.component, found) }
        return found
    }

    private fun collectCefBrowsers(component: Component?, sink: MutableList<Any>) {
        if (component == null) return
        runCatching { component.javaClass.getMethod("getJBCefBrowser").invoke(component) }
            .getOrNull()
            ?.let { jbBrowser ->
                runCatching { jbBrowser.javaClass.getMethod("getCefBrowser").invoke(jbBrowser) }
                    .getOrNull()
                    ?.let(sink::add)
            }
        if (component is Container) {
            component.components.forEach { collectCefBrowsers(it, sink) }
        }
    }

    /** True once the browser has left `about:blank` for the chat client and finished loading. */
    private fun isReady(cefBrowser: Any): Boolean {
        val url = invokeNoArg(cefBrowser, "getURL") as? String ?: return false
        if (!url.startsWith("http")) return false
        if (invokeNoArg(cefBrowser, "hasDocument") == false) return false
        return invokeNoArg(cefBrowser, "isLoading") != true
    }

    private fun invokeNoArg(cefBrowser: Any, name: String): Any? = runCatching {
        cefBrowserInterface(cefBrowser).getMethod(name).invoke(cefBrowser)
    }.getOrNull()

    private fun cefBrowserInterface(cefBrowser: Any): Class<*> =
        Class.forName("org.cef.browser.CefBrowser", false, cefBrowser.javaClass.classLoader)

    private fun executeJs(cefBrowser: Any, script: String): Boolean = runCatching {
        cefBrowserInterface(cefBrowser)
            .getMethod("executeJavaScript", String::class.java, String::class.java, Int::class.javaPrimitiveType)
            .invoke(cefBrowser, script, "", 0)
        true
    }.onFailure { thisLogger().debug("Cascade sync: injection failed", it) }.getOrDefault(false)

    /**
     * Setting the properties inline on `.chat-client-root` beats Cascade's `.chat-client-root.dark`
     * rule, while `.theme-inverse` subtrees keep their inverted values because a descendant rule
     * still outranks an inherited inline value. A `:root` override would lose outright.
     *
     * [rules] go into one reused `<style>` element instead, since a rule cannot be inlined.
     */
    private fun buildScript(tokens: Map<String, String>, rules: Map<String, Map<String, String>>): String {
        val entries = tokens.entries.joinToString(",") { (name, value) -> "\"$name\":\"$value\"" }
        val css = rules.entries.joinToString("\n") { (selector, declarations) ->
            declarations.entries.joinToString(
                separator = " ",
                prefix = "$selector { ",
                postfix = " }",
            ) { (property, value) -> "$property: $value;" }
        }
        return """
            (function () {
              var values = {$entries};
              var css = ${jsString(css)};
              function apply() {
                var root = document.querySelector('.chat-client-root');
                if (!root) return false;
                for (var name in values) root.style.setProperty(name, values[name]);
                var style = document.getElementById('$STYLE_ID');
                if (!style) {
                  style = document.createElement('style');
                  style.id = '$STYLE_ID';
                  document.head.appendChild(style);
                }
                style.textContent = css;
                return true;
              }
              var tries = 0;
              (function poll() {
                if (apply() || ++tries > $MAX_JS_POLLS) return;
                setTimeout(poll, $JS_POLL_INTERVAL_MS);
              })();
            })();
        """.trimIndent()
    }

    private fun isEnabled() = Registry.`is`(REGISTRY_KEY, true)

    /** Quotes a value for the injected script; the escaped selectors need the backslashes kept. */
    private fun jsString(value: String) =
        "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\""

    companion object {
        /** Kill switch, declared as a `registryKey` in `plugin.xml`. */
        const val REGISTRY_KEY = "darkthemes.cascade.sync"

        private const val CASCADE_TOOL_WINDOW_ID = "Cascade"

        private const val STYLE_ID = "darkthemes-cascade-sync"

        private val NO_BACKGROUND = mapOf("background" to "none !important")

        private const val MAX_JS_POLLS = 120
        private const val JS_POLL_INTERVAL_MS = 250

        /** ~2 minutes, because a cold start with indexing easily takes a minute. */
        private const val MAX_ATTEMPTS = 80
        private const val POLL_INTERVAL_MS = 1_500

        private const val REAPPLY_DELAY_MS = 4_000

        fun getInstance(project: Project): CascadeSync =
            project.getService(CascadeSync::class.java)
    }
}
