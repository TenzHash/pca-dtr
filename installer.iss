; Inno Setup script - produces DTR_Generator_Setup.exe (a normal Windows installer wizard).
#ifndef AppVersion
#define AppVersion "1.0.0"
#endif
[Setup]
AppId={{7B3E5C1A-4D2F-4A8B-9C61-0A1B2C3D4E5F}
AppName=DTR Generator
AppVersion={#AppVersion}
CloseApplications=yes
RestartApplications=yes
DefaultDirName={autopf}\DTR Generator
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=DTR_Generator_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\DTR_Generator.exe

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "dist\DTR_Generator\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "update_source.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\DTR Generator"; Filename: "{app}\DTR_Generator.exe"
Name: "{autodesktop}\DTR Generator"; Filename: "{app}\DTR_Generator.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DTR_Generator.exe"; Description: "Launch DTR Generator"; Flags: nowait postinstall skipifsilent
Filename: "{app}\DTR_Generator.exe"; Flags: nowait skipifnotsilent
