Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
psScript = fso.BuildPath(scriptDir, "PostUpdate-AntigravityTR.ps1")
oldPidArg = ""
If WScript.Arguments.Count > 0 Then
    oldPidArg = " -OldPid " & WScript.Arguments(0)
End If
WshShell.Run "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File """ & psScript & """" & oldPidArg, 0, False
