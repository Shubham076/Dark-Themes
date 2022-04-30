package com.github.shubham076.darkthemes.services

import com.intellij.openapi.project.Project
import com.github.shubham076.darkthemes.MyBundle

class MyProjectService(project: Project) {

    init {
        println(MyBundle.message("projectService", project.name))
    }
}
