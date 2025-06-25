package com.github.shubham076.themes.listeners

import com.github.shubham076.themes.CheckLicense
import com.intellij.ide.ui.LafManager
import com.intellij.ide.ui.LafManagerListener
import javax.swing.JOptionPane

class ThemeChangeListener : LafManagerListener {
    private val TITLE = "Dark Themes"
    private val proThemes = listOf("Elements Pro")
    private var lastTheme = LafManager.getInstance().currentLookAndFeel?.name

    override fun lookAndFeelChanged(lafManager: LafManager) {
        val newTheme = lafManager.currentLookAndFeel?.name

        // Skip if no actual change or null
        if (newTheme == null || newTheme == lastTheme) return
        val isLicensed = CheckLicense.isLicensed();

        // Block access if trying to switch to a Pro theme without a license
        if (proThemes.contains(newTheme) && isLicensed == false) {
            if (lastTheme == null) {
                JOptionPane.showMessageDialog(
                    JOptionPane.getRootFrame(),
                    "Cannot revert to previous theme because it could not be determined.\n" +
                            "Please restart the IDE or manually change the theme.",
                    TITLE,
                    JOptionPane.WARNING_MESSAGE
                )
                return
            }

            // Try to find and apply fallback theme
            val previousTheme = lafManager.installedLookAndFeels
                .firstOrNull { it.name == lastTheme }

            if (previousTheme == null) {
                JOptionPane.showMessageDialog(
                    JOptionPane.getRootFrame(),
                    "The previous theme ($lastTheme) could not be found.\n" +
                            "Please restart the IDE or select a free theme manually.",
                    TITLE,
                    JOptionPane.WARNING_MESSAGE
                )
                return
            }

            lafManager.setCurrentLookAndFeel(previousTheme)
            lafManager.updateUI()

            val message = """
                Pro license is required to use this theme.

                Please go to Help → Register Plugins… to activate or purchase a license.
            """.trimIndent()

            JOptionPane.showMessageDialog(
                JOptionPane.getRootFrame(),
                message,
                TITLE,
                JOptionPane.INFORMATION_MESSAGE
            )
            return
        }

        // Theme is allowed — update tracking
        lastTheme = newTheme
    }
}
