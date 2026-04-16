; installer.iss
; Скрипт для создания установщика CarWash Admin Pro

#define AppName "CarWash Admin Pro"
#define AppVersion "3.0.1"
#define AppPublisher "CarWash"
#define AppURL "https://github.com/Kriva4991/CarWashAdmin"
#define AppExeName "CarWashAdmin.exe"

[Setup]
; Уникальный идентификатор приложения
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=Documentation\LICENSE.txt
OutputDir=installer
OutputBaseFilename=CarWashAdmin_Setup_{#AppVersion}
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Основной исполняемый файл
Source: "dist\CarWashAdmin\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Папка с данными (создаётся пустая)
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist

; Документация
Source: "Documentation\*.txt"; DestDir: "{app}\Documentation"; Flags: ignoreversion
Source: "Documentation\*.md"; DestDir: "{app}\Documentation"; Flags: ignoreversion

; Файл для начала работы
Source: "Start_Here.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Создание папки data при установке
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Создаём папку data если её нет
    ForceDirectories(ExpandConstant('{app}\data'));
    ForceDirectories(ExpandConstant('{app}\logs'));
    ForceDirectories(ExpandConstant('{app}\backups'));
  end;
end;