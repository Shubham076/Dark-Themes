package com.github.shubham076.darkthemes.cascade

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.project.DumbAware

/**
 * Tools menu action that re-runs [CascadeSync] by hand.
 *
 * Mainly a troubleshooting aid: it reports whether a Cascade web view was reachable at all, which
 * is the part most likely to break when the Windsurf plugin updates.
 */
internal class SyncCascadeColorsAction : AnAction(), DumbAware {

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val reached = CascadeSync.getInstance(project).syncNow()
        val (text, type) = if (reached > 0) {
            "Cascade colors synced with the current theme." to NotificationType.INFORMATION
        } else {
            "No Cascade web view found. Open the Cascade tool window and try again." to NotificationType.WARNING
        }
        NotificationGroupManager.getInstance()
            .getNotificationGroup("Dark-Themes")
            .createNotification(text, type)
            .notify(project)
    }
}
