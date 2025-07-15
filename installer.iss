[Setup]
AppName=Reels Downloader
AppVersion=1.0
DefaultDirName={pf}\ReelsDownloader
DefaultGroupName=ReelsDownloader
OutputDir=dist
OutputBaseFilename=ReelsDownloader_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico
LicenseFile=license.txt
WizardImageFile=side_image.bmp

[Files]
Source: "dist\reels_downloader.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "ffmpeg\*"; DestDir: "{app}\ffmpeg"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\Reels Downloader"; Filename: "{app}\reels_downloader.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\reels_downloader.exe"; Description: "Uygulamayı Başlat"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Kısayol Seçenekleri"
