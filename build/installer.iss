; Inno Setup skript pre inštalátor aplikácie Voľby dekana TF SPU v Nitre.
; Vyžaduje Inno Setup 6+. Spúšťa sa po PyInstaller builde (dist/VolbyDekana.exe).

#define MyAppName "Voľby dekana TF SPU"
#define MyAppVersion "0.4.0"
#define MyAppPublisher "TF SPU v Nitre"
#define MyAppExeName "VolbyDekana.exe"

[Setup]
AppId={{B6A2C8E1-4F3D-4E9A-9C7B-3A1D2E5F6A70}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\VolbyDekana
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=VolbyDekana-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\src\volby_dekana\assets\logo.ico

[Languages]
Name: "slovak"; MessagesFile: "compiler:Languages\Slovak.isl"

[Tasks]
Name: "desktopicon"; Description: "Vytvoriť zástupcu na ploche"; GroupDescription: "Doplnkové úlohy:"

[Files]
Source: "..\dist\VolbyDekana\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\VolbyDekana\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Odinštalovať {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Spustiť {#MyAppName}"; Flags: nowait postinstall skipifsilent
