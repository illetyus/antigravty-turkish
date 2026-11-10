' Antigravity Turkish On-Demand Launcher (Zero background service)
' Verifies app.asar stamp in ~10ms, patches only if needed, launches Antigravity.exe and exits.
Option Explicit

Dim WshShell, fso, scriptDir, localAppData, exePath, asarPath, stampPath, ensurePs
Dim needsCheck, asarFile, curStamp, ts, savedStamp, rc, i, arg, argLine, cmdLine

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
localAppData = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
exePath = localAppData & "\Programs\antigravity\Antigravity.exe"
asarPath = localAppData & "\Programs\antigravity\resources\app.asar"
stampPath = fso.BuildPath(scriptDir, ".last_patched_stamp")
ensurePs = fso.BuildPath(scriptDir, "Ensure-AntigravityTR.ps1")

needsCheck = True
If fso.FileExists(asarPath) And fso.FileExists(stampPath) Then
    On Error Resume Next
    Set asarFile = fso.GetFile(asarPath)
    curStamp = CStr(asarFile.Size) & "|" & CStr(asarFile.DateLastModified)
    Set ts = fso.OpenTextFile(stampPath, 1)
    savedStamp = ""
    If Not ts.AtEndOfStream Then
        savedStamp = Trim(ts.ReadAll)
    End If
    ts.Close
    If Err.Number = 0 And savedStamp = curStamp Then
        needsCheck = False
    End If
    On Error GoTo 0
End If

If needsCheck And fso.FileExists(ensurePs) Then
    rc = WshShell.Run("powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File """ & ensurePs & """", 0, True)
    If rc = 0 And fso.FileExists(asarPath) Then
        On Error Resume Next
        Set asarFile = fso.GetFile(asarPath)
        curStamp = CStr(asarFile.Size) & "|" & CStr(asarFile.DateLastModified)
        Set ts = fso.OpenTextFile(stampPath, 2, True)
        ts.Write curStamp
        ts.Close
        On Error GoTo 0
    End If
End If

argLine = ""
For i = 0 To WScript.Arguments.Count - 1
    arg = WScript.Arguments(i)
    argLine = argLine & " """ & Replace(arg, """", """""") & """"
Next

If fso.FileExists(exePath) Then
    cmdLine = """" & exePath & """" & argLine
    WshShell.Run cmdLine, 1, False
End If
