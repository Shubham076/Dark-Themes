package com.github.shubham076.darkthemes.cascade

import com.intellij.ide.ui.LafManager
import com.intellij.ide.ui.LafManagerListener
import com.intellij.openapi.editor.colors.EditorColorsListener
import com.intellij.openapi.editor.colors.EditorColorsScheme
import com.intellij.openapi.project.Project
import com.intellij.openapi.project.ProjectManager
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowManager
import com.intellij.openapi.wm.ex.ToolWindowManagerListener

private const val CASCADE_TOOL_WINDOW_ID = "Cascade"

private fun syncAllProjects() {
    ProjectManager.getInstance().openProjects
        .filterNot { it.isDisposed }
        .forEach { CascadeSync.getInstance(it).requestSync() }
}

/**
 * Runs [CascadeSync] once the Cascade tool window is on screen, and doubles as the startup
 * trigger — the IDE has no startup hook usable across the 223-262 range we target.
 *
 * All three callbacks are wired because which one fires on a restore depends on the saved layout.
 * `requestSync` is debounced, so overlapping triggers are harmless.
 */
internal class CascadeToolWindowListener(private val project: Project) : ToolWindowManagerListener {

    override fun toolWindowShown(toolWindow: ToolWindow) {
        if (toolWindow.id == CASCADE_TOOL_WINDOW_ID) sync()
    }

    override fun toolWindowsRegistered(ids: MutableList<String>, toolWindowManager: ToolWindowManager) {
        if (CASCADE_TOOL_WINDOW_ID in ids) sync()
    }

    override fun stateChanged(toolWindowManager: ToolWindowManager) {
        if (!started) sync()
    }

    private var started = false

    private fun sync() {
        started = true
        CascadeSync.getInstance(project).requestSync()
    }
}

/** Runs [CascadeSync] when the UI theme changes, i.e. when `getFromTheme` values change. */
internal class CascadeLafListener : LafManagerListener {
    override fun lookAndFeelChanged(source: LafManager) = syncAllProjects()
}

/** Runs [CascadeSync] when the editor scheme changes, i.e. when `getFromEditorScheme` values do. */
internal class CascadeSchemeListener : EditorColorsListener {
    override fun globalSchemeChange(scheme: EditorColorsScheme?) = syncAllProjects()
}
