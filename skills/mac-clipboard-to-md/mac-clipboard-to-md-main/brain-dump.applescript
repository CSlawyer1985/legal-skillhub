on run
    try
        -- 获取剪贴板内容
        set theClipboard to get the clipboard as text
        if theClipboard is "" then
            display dialog "剪贴板为空" buttons {"OK"}
            return
        end if

        -- 生成更友好的时间戳
        set currentDate to current date
        set theYear to year of currentDate as string
        set theMonth to month of currentDate as number
        set theDay to day of currentDate
        set theHours to hours of currentDate
        set theMinutes to minutes of currentDate
        set theSeconds to seconds of currentDate

        -- 补零
        if theMonth < 10 then set theMonth to "0" & theMonth
        if theDay < 10 then set theDay to "0" & theDay
        if theHours < 10 then set theHours to "0" & theHours
        if theMinutes < 10 then set theMinutes to "0" & theMinutes
        if theSeconds < 10 then set theSeconds to "0" & theSeconds

        set dateString to theYear & "-" & theMonth & "-" & theDay
        set timeString to theHours & "." & theMinutes & "." & theSeconds

        -- 文件名输入对话框
        set nameDialog to display dialog "请输入文件名（可选，留空则只使用时间戳）：" default answer "" buttons {"取消", "确认"} default button "确认"

        if button returned of nameDialog is "取消" then
            display notification "用户取消操作" with title "已取消"
            return
        end if

        set userFileName to text returned of nameDialog
        set cleanFileName to my trim(userFileName)

        -- 构建最终文件名
        if cleanFileName is not "" then
            if cleanFileName ends with ".md" then
                set cleanFileName to text 1 thru -4 of cleanFileName
            end if
            set fileName to "记录_" & dateString & "_" & timeString & "_" & cleanFileName & ".md"
        else
            set fileName to "记录_" & dateString & "_" & timeString & ".md"
        end if

        -- 设置文件夹路径（请修改为你自己的路径）
        set folderPath to "/Users/你的用户名/Documents/brain dump/"
        set filePath to folderPath & fileName

        -- 确保文件夹存在
        set escapedFolderPath to quoted form of folderPath
        do shell script "mkdir -p " & escapedFolderPath

        -- 标签输入对话框
        set tagDialog to display dialog "请输入标签（多个标签用逗号分隔）：" default answer "" buttons {"取消", "确认"} default button "确认"
        set userTags to text returned of tagDialog

        if button returned of tagDialog is "取消" then
            display notification "用户取消操作" with title "已取消"
            return
        end if

        -- 处理标签格式，构建YAML frontmatter
        set yamlFrontmatter to "---" & return

        if userTags is not "" then
            set tagList to my splitString(userTags, ",")
            set yamlFrontmatter to yamlFrontmatter & "tags:" & return
            repeat with aTag in tagList
                set cleanTag to my trim(aTag)
                if cleanTag is not "" then
                    set yamlFrontmatter to yamlFrontmatter & "  - " & cleanTag & return
                end if
            end repeat
        end if

        -- 添加描述（可选）
        set descDialog to display dialog "请输入描述（可选）：" default answer "" buttons {"跳过", "确认"} default button "确认"
        set userDesc to text returned of descDialog

        if button returned of descDialog is "确认" and userDesc is not "" then
            set yamlFrontmatter to yamlFrontmatter & "description: " & userDesc & return
        end if

        set yamlFrontmatter to yamlFrontmatter & "---" & return & return

        -- 构建完整的文件内容
        set fileContent to yamlFrontmatter
        set fileContent to fileContent & "# "& dateString & " " & timeString & return & return
        set fileContent to fileContent & "**创建时间**: " & (time string of currentDate) & return & return
        set fileContent to fileContent & "## 内容" & return & theClipboard & return & return
        set fileContent to fileContent & "---" & return & "*自动生成*" & return

        -- 写入文件
        set escapedContent to quoted form of fileContent
        set escapedPath to quoted form of filePath
        do shell script "export LANG=en_US.UTF-8; echo " & escapedContent & " > " & escapedPath

        set successMsg to "已创建: " & fileName
        if userTags is not "" then
            set successMsg to successMsg & " | 标签: " & userTags
        end if
        display notification successMsg with title "保存成功"

    on error errMsg
        display dialog "错误: " & errMsg buttons {"OK"}
    end try
end run

-- 辅助函数：去除字符串前后空格
on trim(theText)
    set AppleScript's text item delimiters to {" "}
    set textItems to text items of theText
    set AppleScript's text item delimiters to {""}
    set theText to textItems as string

    set AppleScript's text item delimiters to {return}
    set textItems to text items of theText
    set AppleScript's text item delimiters to {""}
    set theText to textItems as string

    set AppleScript's text item delimiters to {tab}
    set textItems to text items of theText
    set AppleScript's text item delimiters to {""}
    return textItems as string
end trim

-- 辅助函数：分割字符串
on splitString(theText, theDelimiter)
    set AppleScript's text item delimiters to theDelimiter
    set textItems to text items of theText
    set AppleScript's text item delimiters to ""
    return textItems
end splitString
