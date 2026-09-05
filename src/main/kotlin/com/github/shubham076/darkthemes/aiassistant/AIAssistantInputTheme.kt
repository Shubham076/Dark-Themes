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
import javax.swing.JComponent
import javax.swing.UIManager

/**
 * Gives the AI Assistant's chat input its own background, instead of the editor's.
 *
 * The whole rounded box takes the editor background because
 * `AIAssistantNewToolbarInput.getBackground()` returns
 * `editorTextField.editor.colorsScheme.defaultBackground` — and its `setBackground` is an explicit
 * no-op, so a recolor cannot be pushed in from outside. `AIAssistantInputBorder` fills from the
 * same place. Both read the *editor's* scheme rather than the global one, which is the opening:
 * wrapping that one editor's scheme moves the text area, the row behind the toolbar and the border
 * fill together, and touches nothing else in the IDE.
 *
 * Opt-in per theme — with no [BACKGROUND_KEY] in the `.theme.json` this does nothing.
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

private fun theme(editor: EditorEx) {
    val scheme = editor.colorsScheme
    if (UIManager.getColor(BACKGROUND_KEY) == null) {
        // Only a chat input can be holding one of ours, so no need to identify the editor first.
        if (scheme is ThemedInputScheme) editor.colorsScheme = scheme.delegate
        return
    }
    val input = chatInput(editor) ?: return
    // Re-wrap even when the wrapper is still there: `applyIdeThemeColorScheme` hands the editor a
    // brand new scheme on every theme change, so what we find is either that or our own wrapper
    // around the previous theme's.
    editor.colorsScheme = ThemedInputScheme(if (scheme is ThemedInputScheme) scheme.delegate else scheme)
    clearToolbarBackgrounds(input)
    input.repaint()
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
 * Unsets the background the AI Assistant puts on the buttons in the input's toolbars.
 *
 * `AIAssistantInputEditorLifecycleController.updateTheme` runs `setBackgroundRecursively` over
 * every `ActionToolbar` in the input with the editor's background, and
 * `ActionButtonLook.getStateBackground` paints an idle button's background whenever one is set — so
 * each button becomes a filled slab of whatever color that sweep last saw. That is the editor
 * background rather than ours, since the sweep and the scheme replacement it follows both happen
 * before we get to re-wrap. Unsetting the color makes the buttons paint nothing at rest and leaves
 * `ActionButton.hoverBackground` in charge of hover and pressed states.
 */
private fun clearToolbarBackgrounds(component: Component, insideToolbar: Boolean = false) {
    val inToolbar = insideToolbar || component is ActionToolbar
    if (inToolbar) component.background = null
    if (component is Container) component.components.forEach { clearToolbarBackgrounds(it, inToolbar) }
}

private fun themeAll() = EditorFactory.getInstance().allEditors
    .filterIsInstance<EditorEx>()
    .forEach(::theme)

/**
 * Re-applies a beat after the current event.
 *
 * The AI Assistant's own theme updater listens to `LafManagerListener` too, and replaces the
 * editor's scheme and the toolbar backgrounds from there. Which of two message bus subscribers
 * runs first is not ours to pick, so this lands after both instead of racing.
 */
private fun themeAllLater() = ApplicationManager.getApplication().invokeLater(::themeAll)

/** Catches the input editor of every chat session, including ones opened later. */
internal class AIAssistantInputEditorListener : EditorFactoryListener {

    override fun editorCreated(event: EditorFactoryEvent) {
        val editor = event.editor as? EditorEx ?: return
        if (UIManager.getColor(BACKGROUND_KEY) == null) return
        // The editor is not in the component tree yet, and that tree is what identifies it — nor
        // has the assistant's own `initEditor`, which this has to follow, run.
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
