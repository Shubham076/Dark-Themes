package com.github.shubham076.darkthemes.aiassistant

import com.intellij.ide.ui.LafManager
import com.intellij.ide.ui.LafManagerListener
import com.intellij.openapi.actionSystem.ActionToolbar
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.editor.EditorFactory
import com.intellij.openapi.editor.colors.EditorColorsListener
import com.intellij.openapi.editor.colors.EditorColorsScheme
import com.intellij.openapi.editor.colors.impl.DelegateColorScheme
import com.intellij.openapi.editor.event.EditorFactoryEvent
import com.intellij.openapi.editor.event.EditorFactoryListener
import com.intellij.openapi.editor.ex.EditorEx
import java.awt.Color
import java.awt.Component
import java.awt.Container
import java.awt.event.ContainerAdapter
import java.awt.event.ContainerEvent
import java.awt.event.HierarchyEvent
import javax.swing.JComponent
import javax.swing.UIManager

/**
 * Gives the AI Assistant's chat input its own background, instead of the editor's.
 *
 * `AIAssistantNewToolbarInput.getBackground()` and `AIAssistantInputBorder` both read
 * `editorTextField.editor.colorsScheme.defaultBackground`, and its `setBackground` is a no-op, so
 * wrapping that one editor's scheme is the only lever — and it moves the text area, the toolbar row
 * and the border fill together without touching any other editor.
 *
 * Opt-in per theme: with no [BACKGROUND_KEY] in the `.theme.json` this does nothing. `AGENTS.md`
 * carries the evidence behind each step.
 */
private const val BACKGROUND_KEY = "AIAssistantInput.background"

/** The chat input's `EditorTextField`, which is how its editor is told apart from every other. */
private const val INPUT_TEXT_FIELD =
    "com.intellij.ml.llm.core.chat.ui.chat.input.AIAssistantInputEditorTextField"

/** Everything the input is built from, the text field included, lives in this one package. */
private const val INPUT_PACKAGE = "com.intellij.ml.llm.core.chat.ui.chat.input."

/** Reads the theme on every call, so a theme switch needs no re-wrapping. */
private class ThemedInputScheme(delegate: EditorColorsScheme) : DelegateColorScheme(delegate) {
    override fun getDefaultBackground(): Color =
        UIManager.getColor(BACKGROUND_KEY) ?: super.getDefaultBackground()
}

/**
 * Whether ours is already in the chain.
 *
 * Never compare against `editor.colorsScheme` directly: `EditorImpl.setColorsScheme` keeps what it
 * is handed inside an `EditorColorSchemeDelegate` of its own, so the scheme that comes back out is
 * never the one that went in.
 */
private fun EditorColorsScheme.isThemed(): Boolean {
    var scheme: EditorColorsScheme? = this
    while (scheme != null) {
        if (scheme is ThemedInputScheme) return true
        scheme = (scheme as? DelegateColorScheme)?.delegate
    }
    return false
}

private fun theme(editor: EditorEx) {
    val background = UIManager.getColor(BACKGROUND_KEY) ?: return
    val input = chatInput(editor) ?: return
    // Wrap once, and only once. `setColorsScheme` nests another `EditorColorSchemeDelegate` around
    // whatever it is given and then runs `reinitSettings`, so re-wrapping on every pass would
    // lengthen the chain that every attribute lookup walks *and* re-init the editor — cheap once,
    // but this runs again on each theme change and each time the panel is shown. Their
    // `applyIdeThemeColorScheme` throws ours away on a theme change; this puts it back.
    var changed = false
    if (!editor.colorsScheme.isThemed()) {
        editor.colorsScheme = ThemedInputScheme(editor.colorsScheme)
        changed = true
    }
    // A *forced* background outranks the scheme, and `EditorTextField` forces one on every editor
    // it builds — `TextField.background` on a cold start, when it has no editor to read a color
    // from yet. Passing our own color clears the override instead of adding to it, since
    // `EditorImpl` drops a forced color that matches the scheme's.
    if (editor.backgroundColor != background) {
        editor.backgroundColor = background
        changed = true
    }
    // The text area is the scroll pane's viewport: the assistant makes the editor's content
    // component non-opaque and `EditorImpl` only ever calls `setViewportView`, so nothing colors
    // the viewport and it keeps painting `Viewport.background` from the LaF.
    val viewport = editor.scrollPane?.viewport
    if (viewport != null && viewport.background != background) {
        viewport.background = background
        changed = true
    }
    clearToolbarBackgrounds(input)
    followShowing(input)
    // Only when something moved: `setBackgroundColor` just stores the color, so a repaint is ours
    // to ask for, but an unconditional one would fire on every show and every theme change.
    if (changed) input.repaint()
}

/** The input panel this editor belongs to, or null for every other editor in the IDE. */
private fun chatInput(editor: EditorEx): JComponent? {
    var candidate: Component? = editor.contentComponent
    var isChatInput = false
    var input: JComponent? = null
    while (candidate != null) {
        if (candidate.javaClass.name == INPUT_TEXT_FIELD) isChatInput = true
        // The outermost component of the package is `AIAssistantNewToolbarInput`, which owns both
        // the editor and the toolbars drawn on top of the box.
        if (candidate is JComponent && candidate.javaClass.name.startsWith(INPUT_PACKAGE)) input = candidate
        candidate = candidate.parent
    }
    return if (isChatInput) input else null
}

/**
 * Unsets the background on the input's toolbar buttons, and keeps it unset.
 *
 * Their `updateTheme` sweeps `setBackgroundRecursively` over every `ActionToolbar` before we can
 * re-wrap — with `TextField.background` on a cold start, as it runs even before an editor exists —
 * and `ActionButtonLook` fills an idle button with whatever background is set, so each becomes a
 * slab. Unsetting stops the fill (`isBackgroundSet` reads the component's own field, it does not
 * inherit) and leaves `ActionButton.hoverBackground` in charge of hover and pressed.
 *
 * The listener is what keeps it unset: the toolbars are rebuilt asynchronously — as models resolve
 * after a cold start, and whenever send becomes stop — and the rebuilt `JPanel`-based custom
 * components (mode selector, context-usage circle) bring `Panel.background` with them. Follow every
 * container, not only the toolbars, since a rebuild can add a whole new `ActionToolbar`.
 */
private fun clearToolbarBackgrounds(component: Component, insideToolbar: Boolean = false) {
    val inToolbar = insideToolbar || component is ActionToolbar
    if (inToolbar) {
        if (component.isBackgroundSet) component.background = null
        // Hold it unset rather than only setting it once. Their sweep runs from `initEditor`, which
        // a tool window re-show reaches without building an editor — so neither `editorCreated` nor
        // a container event fires and nothing else of ours would notice the recolor.
        if (component is JComponent && component.getClientProperty(FOLLOWED_BACKGROUND) == null) {
            component.putClientProperty(FOLLOWED_BACKGROUND, true)
            component.addPropertyChangeListener("background") {
                // Never trust the event's new value. Once a component has a peer,
                // `Component.setBackground(null)` reassigns `c = getBackground()` before firing, so
                // it reports the color *inherited* from the parent rather than the null we passed —
                // and re-clearing on that recurses until the stack is gone. Only the component's
                // own field says whether anything is set, and `isBackgroundSet` reads just that.
                if (component.isBackgroundSet) component.background = null
            }
        }
    }
    if (component !is Container) return
    if (component is JComponent && component.getClientProperty(FOLLOWED_CHILDREN) == null) {
        component.putClientProperty(FOLLOWED_CHILDREN, true)
        component.addContainerListener(object : ContainerAdapter() {
            override fun componentAdded(event: ContainerEvent) {
                clearToolbarBackgrounds(event.child, inToolbar)
                // And again once settled, for children that color themselves from `addNotify`.
                ApplicationManager.getApplication().invokeLater {
                    clearToolbarBackgrounds(event.child, inToolbar)
                }
            }
        })
    }
    component.components.forEach { clearToolbarBackgrounds(it, inToolbar) }
}

/** Marks a container whose new children are already followed. */
private const val FOLLOWED_CHILDREN = "darkthemes.aiassistant.followed.children"

/** Marks a component whose background we hold unset. */
private const val FOLLOWED_BACKGROUND = "darkthemes.aiassistant.followed.background"

/**
 * Re-applies everything when the panel comes back into view.
 *
 * The same `updateTheme` that sweeps the toolbars also calls `applyIdeThemeColorScheme`, which
 * throws our scheme wrapper away — so a re-show can revert the box color too, not only the buttons,
 * and that one no invariant on a component can catch.
 */
private fun followShowing(input: JComponent) {
    if (input.getClientProperty(FOLLOWED_SHOWING) != null) return
    input.putClientProperty(FOLLOWED_SHOWING, true)
    input.addHierarchyListener {
        val shown = it.changeFlags and HierarchyEvent.SHOWING_CHANGED.toLong() != 0L
        // Whichever editor the input holds by then is the one to re-theme, so go through them all.
        if (shown && input.isShowing) ApplicationManager.getApplication().invokeLater(::themeAll)
    }
}

/** Marks an input we already re-theme on show. */
private const val FOLLOWED_SHOWING = "darkthemes.aiassistant.followed.showing"

private fun themeAll() = EditorFactory.getInstance().allEditors
    .filterIsInstance<EditorEx>()
    .forEach(::theme)

/**
 * Re-applies a beat after the current event: the assistant's own updater replaces the scheme and
 * the toolbar backgrounds from `LafManagerListener` too, and message bus order is not ours to pick.
 */
private fun themeAllLater() = ApplicationManager.getApplication().invokeLater(::themeAll)

/** Catches the input editor of every chat session, including ones opened later. */
internal class AIAssistantInputEditorListener : EditorFactoryListener {

    override fun editorCreated(event: EditorFactoryEvent) {
        val editor = event.editor as? EditorEx ?: return
        if (UIManager.getColor(BACKGROUND_KEY) == null) return
        // Deferred: the editor is not in the component tree yet, and that tree is what identifies
        // it — nor has the assistant's own `initEditor`, which this has to follow, run.
        ApplicationManager.getApplication().invokeLater {
            if (!editor.isDisposed) theme(editor)
        }
    }
}

/** Re-wraps after a theme change, since the assistant replaces the scheme on the same event. */
internal class AIAssistantInputLafListener : LafManagerListener {
    override fun lookAndFeelChanged(source: LafManager) = themeAllLater()
}

/** The same, for a change of editor color scheme. */
internal class AIAssistantInputSchemeListener : EditorColorsListener {
    override fun globalSchemeChange(scheme: EditorColorsScheme?) = themeAllLater()
}
