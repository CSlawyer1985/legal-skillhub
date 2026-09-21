on run {input, parameters}
    -- 获取剪贴板内容
    set theClipboard to get the clipboard as text

    -- 检查剪贴板是否有内容
    if theClipboard is "" then
        display dialog "剪贴板中没有文本内容！" buttons {"OK"} default button 1
        return
    end if

    -- 获取当前时间并格式化
    set currentDate to current date

    -- 日期补零处理
    set theYear to year of currentDate
    set theMonth to month of currentDate as number
    set theDay to day of currentDate
    if theMonth < 10 then set theMonth to "0" & theMonth
    if theDay < 10 then set theDay to "0" & theDay
    set timeStamp to theYear & "-" & theMonth & "-" & theDay & " " & (time string of currentDate)

    -- 构建要写入的内容
    set contentToWrite to "# " & timeStamp & linefeed & theClipboard & linefeed & linefeed & linefeed

    -- 设置文件路径（请修改为你自己的路径）
    set filePath to "~/你的Obsidian库/Work record.md"

    try
        -- 检查文件是否存在
        set fileExists to false
        try
            do shell script "test -f " & quoted form of filePath
            set fileExists to true
        on error
            set fileExists to false
        end try

            -- 读取文件内容（paragraphs 自动处理 CR/LF/CRLF）
            set fileContent to do shell script "export LANG=en_US.UTF-8; cat " & quoted form of filePath
            set linesList to paragraphs of fileContent

            -- 找第二个 ---（frontmatter 结束位置）
            set fmEndLine to 0
            set dashCount to 0
            repeat with i from 1 to (count of linesList)
                if item i of linesList is "---" then
                    set dashCount to dashCount + 1
                    if dashCount is 2 then
                        set fmEndLine to i
                        exit repeat
                    end if
                end if
            end repeat

            if fmEndLine > 0 then
                -- 有 frontmatter：提取 header（含两个 ---），新内容插在其后
                set headerLines to {}
                repeat with i from 1 to fmEndLine
                    set end of headerLines to item i of linesList
                end repeat

                set bodyLines to {}
                repeat with i from (fmEndLine + 1) to (count of linesList)
                    set end of bodyLines to item i of linesList
                end repeat

                set headerText to ""
                repeat with i from 1 to (count of headerLines)
                    set headerText to headerText & item i of headerLines
                    if i < (count of headerLines) then
                        set headerText to headerText & linefeed
                    end if
                end repeat

                set bodyText to ""
                if (count of bodyLines) > 0 then
                    repeat with i from 1 to (count of bodyLines)
                        set bodyText to bodyText & item i of bodyLines
                        if i < (count of bodyLines) then
                            set bodyText to bodyText & linefeed
                        end if
                    end repeat
                end if

                set finalContent to headerText & linefeed & linefeed & contentToWrite & bodyText
            else
                -- 没有 frontmatter：简单前置追加
                set finalContent to contentToWrite & fileContent
            end if

            -- 写入整个文件
            set escapedContent to quoted form of finalContent
            do shell script "export LANG=en_US.UTF-8; printf '%s' " & escapedContent & " > " & quoted form of filePath
        else
            -- 文件不存在，直接创建（包含属性行）
            set defaultHeader to "---" & linefeed & "title: Work Record" & linefeed & "created: " & timeStamp & linefeed & "updated: " & timeStamp & linefeed & "tags: []" & linefeed & "---" & linefeed & linefeed
            set finalContent to defaultHeader & contentToWrite
            set escapedContent to quoted form of finalContent
            do shell script "export LANG=en_US.UTF-8; printf '%s' " & escapedContent & " > " & quoted form of filePath
        end if

        display notification "内容已成功添加到 Work record.md" with title "操作成功"
    on error errMsg
        display dialog "写入文件时出错: " & errMsg buttons {"OK"} default button 1
    end try

    return input
end run
