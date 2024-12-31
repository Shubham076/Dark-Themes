package com.github.shubham076.themes.listeners

import com.github.shubham076.themes.CheckLicense
import com.intellij.ide.ui.LafManager
import com.intellij.ide.ui.LafManagerListener
import com.intellij.openapi.editor.colors.EditorColorsManager
import javax.swing.JOptionPane
import com.intellij.openapi.options.ShowSettingsUtil
import com.intellij.openapi.application.ApplicationManager


class ThemeChangeListener : LafManagerListener {
    private val editorColorsManager = EditorColorsManager.getInstance()
    private var TITLE = "Dark Themes";
    val proThemes = listOf(
        "Gruvbox"
    )
    private var previousUI = LafManager.getInstance().currentLookAndFeel?.name

    override fun lookAndFeelChanged(lafManager: LafManager) {
        val currentUI = lafManager.currentLookAndFeel?.name
        if (previousUI != currentUI && proThemes.contains(currentUI)) {
            val isLicensed = CheckLicense.isLicensed()
            if (isLicensed == false) {
                lafManager.installedLookAndFeels.firstOrNull { it.name == previousUI }?.let {
                    lafManager.setCurrentLookAndFeel(
                        it
                    )
                }
                lafManager.updateUI()
                val message = "Pro license is required to use this theme. Please contact JetBrains for a pro license."
                JOptionPane.showMessageDialog(JOptionPane.getRootFrame(), message, TITLE, JOptionPane.INFORMATION_MESSAGE);
            }
        }
        previousUI = currentUI
    }
}