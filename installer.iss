[Setup]
AppName=ERP Pharmacy
AppVersion=1.0
AppPublisher=CompuMarts
DefaultDirName={autopf}\ErpPharmacy
DefaultGroupName=ERP Pharmacy
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

[Files]
Source: "dist\ErpPharmacy\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ERP Pharmacy"; Filename: "{app}\ErpPharmacy.exe"
Name: "{group}\Uninstall ERP Pharmacy"; Filename: "{uninstallexe}"
Name: "{commondesktop}\ERP Pharmacy"; Filename: "{app}\ErpPharmacy.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ErpPharmacy.exe"; Description: "Launch ERP Pharmacy"; Flags: nowait postinstall skipifsilent
