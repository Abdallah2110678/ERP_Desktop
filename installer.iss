[Setup]
; Fixed id so future versions upgrade this install instead of installing side by side.
AppId={{B7E3C5A2-4D1F-4E8A-9C60-ABAD0A7A0001}
AppName=مكتب عباد الرحمان
AppVersion=1.0
AppPublisher=CompuMarts
; Folder / exe file names stay ASCII on purpose (safe for every Windows setup); users only see the Arabic name.
DefaultDirName={autopf}\ErpPharmacy
DefaultGroupName=مكتب عباد الرحمان
UninstallDisplayName=مكتب عباد الرحمان
UninstallDisplayIcon={app}\ErpPharmacy.exe
OutputDir=installer_output
OutputBaseFilename=ErpPharmacy_Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Dirs]
; The app keeps pharmacy.db (and import backups) next to the exe, so every user must be able to write here.
Name: "{app}"; Permissions: users-modify

[Files]
; pharmacy.db is deliberately NOT shipped: a fresh install starts empty and re-installing never overwrites your data.
Source: "dist\ErpPharmacy\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\مكتب عباد الرحمان"; Filename: "{app}\ErpPharmacy.exe"
Name: "{group}\إلغاء تثبيت مكتب عباد الرحمان"; Filename: "{uninstallexe}"
Name: "{commondesktop}\مكتب عباد الرحمان"; Filename: "{app}\ErpPharmacy.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ErpPharmacy.exe"; Description: "Launch مكتب عباد الرحمان"; Flags: nowait postinstall skipifsilent
