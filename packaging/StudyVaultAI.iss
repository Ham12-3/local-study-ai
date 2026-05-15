#define MyAppName "StudyVault AI"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "StudyVault"
#define MyAppExeName "StudyVaultAI.exe"

[Setup]
AppId={{9A0D17B8-7C58-4662-9191-0B75E88A84A2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\StudyVault AI
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=StudyVaultAI-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\StudyVaultAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#ifexist "vendor\OllamaSetup.exe"
Source: "vendor\OllamaSetup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
#endif

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
#ifexist "vendor\OllamaSetup.exe"
Filename: "{tmp}\OllamaSetup.exe"; Description: "Install local AI runtime"; Flags: waituntilterminated skipifsilent; Check: ShouldInstallOllama
#endif
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function ShouldInstallOllama: Boolean;
var
  ResultCode: Integer;
begin
  Result := not Exec(ExpandConstant('{cmd}'), '/C where ollama', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  if not Result then
    Result := ResultCode <> 0;
end;

