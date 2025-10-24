package com.github.shubham076.themes

import com.intellij.ide.highlighter.XmlFileType
import com.intellij.openapi.components.service
import com.intellij.psi.xml.XmlFile
import com.intellij.testFramework.TestDataPath
import com.intellij.testFramework.fixtures.BasePlatformTestCase
import com.intellij.util.PsiErrorElementUtil
import com.github.shubham076.themes.services.MyProjectService

@TestDataPath("\$CONTENT_ROOT/src/test/testData")
class MyPluginTest : BasePlatformTestCase() {
    
    fun testProjectServiceIsAvailable() {
        val service = project.service<MyProjectService>()
        assertNotNull("MyProjectService should be available", service)
    }
}
