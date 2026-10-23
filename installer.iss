#define AppName      "ErpPharmacy"
#define AppNameAr    "مكتب عباد الرحمن"
#define AppVersion   "1.0.0"
#define AppPublisher "CompuMarts"
#define AppExeName   "ErpPharmacy.exe"
#define SourceDir    "dist"

[Setup]
AppId={{A3F2C1B4-7D8E-4F9A-B2C6-1E3D5F7A9B0C}
AppName={#AppNameAr}
AppVersion={#AppVersion}
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppNameAr}
AllowNoIcons=yes
LicenseFile=
OutputDir=installer_output
OutputBaseFilename=ErpPharmacy_v{#AppVersion}_Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; RTL comes from Arabic.isl ([LangOptions] RightToLeft=yes)
; Minimum Windows 10
MinVersion=10.0
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppNameAr}

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Single-file PyInstaller build (the database lives in %APPDATA%\ErpPharmacy, not here)
Source: "{#SourceDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppNameAr}";  Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppNameAr}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppNameAr}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppNameAr}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the app folder if empty after uninstall
Type: dirifempty; Name: "{app}"
