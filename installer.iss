#define AppName "ErpPharmacy"
#define AppNameAr "مكتب عباد الرحمان"
#define AppVersion "1.0"
#define AppPublisher "عباد الرحمان"
#define AppExeName "ErpPharmacy.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppName={#AppNameAr}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppNameAr}
OutputDir=installer_output
OutputBaseFilename=ErpPharmacy_Setup
SetupIconFile=icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\ErpPharmacy\ErpPharmacy.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\ErpPharmacy\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppNameAr}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppNameAr}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch application"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\pharmacy.db"
