param([switch]$SmokeTest, [string]$TestFolder, [string]$RenderPath, [int]$RenderTab=0)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms
$appRoot = $PSScriptRoot
$settingsFile = Join-Path $appRoot 'preferences.json'
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$venvPython = Join-Path $appRoot '.venv\Scripts\python.exe'
$workerPython = if (Test-Path -LiteralPath $venvPython) { $venvPython } elseif (Test-Path -LiteralPath $bundledPython) { $bundledPython } else { (Get-Command python -ErrorAction Stop).Source }
[xml]$markup = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Title="Prefab Drop" Width="780" Height="900" MinWidth="660" MinHeight="820" WindowStartupLocation="CenterScreen" Background="#F5F5F0" FontFamily="Segoe UI" Foreground="#25332D">
 <Window.Resources>
  <Style TargetType="Button"><Setter Property="Background" Value="#E2E9DC"/><Setter Property="Padding" Value="15,9"/><Setter Property="Cursor" Value="Hand"/><Setter Property="FontSize" Value="13"/><Setter Property="Template"><Setter.Value><ControlTemplate TargetType="Button"><Border x:Name="B" Background="{TemplateBinding Background}" CornerRadius="7" Padding="{TemplateBinding Padding}"><ContentPresenter HorizontalAlignment="Center"/></Border><ControlTemplate.Triggers><Trigger Property="IsMouseOver" Value="True"><Setter TargetName="B" Property="Opacity" Value="0.75"/></Trigger></ControlTemplate.Triggers></ControlTemplate></Setter.Value></Setter></Style>
  <Style TargetType="TextBox"><Setter Property="Padding" Value="9,7"/><Setter Property="BorderBrush" Value="#D7DED3"/><Setter Property="VerticalContentAlignment" Value="Center"/></Style>
  <Style TargetType="ComboBox"><Setter Property="Padding" Value="8,7"/></Style>
  <Style TargetType="TabItem"><Setter Property="Padding" Value="20,10"/><Setter Property="FontSize" Value="14"/></Style>
 </Window.Resources>
 <Grid Margin="30,24"><Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <StackPanel Margin="0,0,0,20"><TextBlock Text="PREFAB DROP" FontSize="12" Foreground="#63755F" FontWeight="SemiBold"/><TextBlock Text="Images into Radiant." FontSize="28" FontWeight="SemiBold" Margin="0,5,0,4"/><TextBlock Text="Brush prefabs and custom materials, in one place." Foreground="#69736B"/></StackPanel>
  <StackPanel Grid.Row="1" Margin="0,0,0,18"><TextBlock Text="COD4 MOD TOOLS FOLDER" Foreground="#63755F" FontSize="11" FontWeight="SemiBold" Margin="0,0,0,7"/><Grid><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><TextBox x:Name="Game" AutomationProperties.Name="CoD4 installation folder"/><Button x:Name="BrowseGame" Grid.Column="1" Content="Choose folder" Margin="10,0,0,0"/></Grid></StackPanel>
  <TabControl x:Name="Tabs" Grid.Row="2" Background="Transparent" BorderThickness="0">
   <TabItem Header="Prefabs"><ScrollViewer VerticalScrollBarVisibility="Auto"><StackPanel Margin="0,18,0,0">
    <TextBlock Text="PREFAB DESTINATION" FontSize="11" Foreground="#63755F" Margin="0,0,0,7"/><Grid Margin="0,0,0,16"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><TextBox x:Name="Folder" AutomationProperties.Name="Prefab destination folder"/><Button x:Name="Browse" Grid.Column="1" Content="Choose folder" Margin="10,0,0,0"/></Grid>
    <Border x:Name="DropZone" Background="#EAEFE5" BorderBrush="#BBCAB4" BorderThickness="1" CornerRadius="12" AllowDrop="True" Padding="24"><StackPanel HorizontalAlignment="Center"><TextBlock Text="⬡" Foreground="#758C68" FontSize="32" HorizontalAlignment="Center"/><TextBlock Text="Drop images here" FontSize="21" FontWeight="SemiBold" HorizontalAlignment="Center" Margin="0,4,0,6"/><TextBlock Text="Create .map prefabs from silhouettes" Foreground="#69736B" HorizontalAlignment="Center"/><Button x:Name="ChooseImages" Content="or choose images" Margin="0,14,0,0" HorizontalAlignment="Center"/></StackPanel></Border>
    <CheckBox x:Name="AutoTexture" IsChecked="True" Content="Automatically convert and apply the image as a texture" Margin="0,16,0,7"/>
    <TextBlock Text="Image fitted across front/back faces · tiled edges" FontSize="11" Foreground="#69736B" Margin="20,0,0,16"/>
    <Grid><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="14"/><ColumnDefinition Width="*"/><ColumnDefinition Width="14"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
     <StackPanel><TextBlock Text="Solid area" Margin="0,0,0,5"/><ComboBox x:Name="Mask" SelectedIndex="0"><ComboBoxItem Content="Dark pixels" Tag="dark"/><ComboBoxItem Content="Light pixels" Tag="light"/><ComboBoxItem Content="PNG transparency" Tag="alpha"/></ComboBox></StackPanel>
     <StackPanel Grid.Column="2"><TextBlock Text="Depth · units" Margin="0,0,0,5"/><TextBox x:Name="Depth" Text="32"/></StackPanel>
     <StackPanel Grid.Column="4"><TextBlock Text="Orientation" Margin="0,0,0,5"/><ComboBox x:Name="Orientation" SelectedIndex="0"><ComboBoxItem Content="Floor" Tag="floor"/><ComboBoxItem Content="Wall" Tag="wall"/></ComboBox></StackPanel>
    </Grid>
    <Expander Header="Size and detail" Margin="0,14,0,0"><Grid Margin="0,10,0,0"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="14"/><ColumnDefinition Width="*"/><ColumnDefinition Width="14"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions><StackPanel><TextBlock Text="Longest edge · cells"/><TextBox x:Name="Resolution" Text="96"/></StackPanel><StackPanel Grid.Column="2"><TextBlock Text="Units per cell"/><TextBox x:Name="Cell" Text="4"/></StackPanel><StackPanel Grid.Column="4"><TextBlock Text="Threshold · 0–255"/><TextBox x:Name="Threshold" Text="128"/></StackPanel></Grid></Expander>
    <Button x:Name="OpenFolder" Content="Open prefab folder ↗" HorizontalAlignment="Right" Background="Transparent" Margin="0,12,0,0"/>
   </StackPanel></ScrollViewer></TabItem>
   <TabItem Header="Single texture"><StackPanel Margin="0,24,0,0">
    <TextBlock Text="Add a texture to Radiant" FontSize="21" FontWeight="SemiBold"/><TextBlock Text="Import one image as a world material. No prefab is created." TextWrapping="Wrap" Foreground="#69736B" Margin="0,7,0,22"/>
    <TextBlock Text="Material label (optional)" Margin="0,0,0,7"/><TextBox x:Name="MaterialName" ToolTip="The final name includes pd_ and a content hash to avoid collisions." Margin="0,0,0,18"/>
    <Border x:Name="TextureDrop" Background="#EAEFE5" BorderBrush="#BBCAB4" BorderThickness="1" CornerRadius="12" AllowDrop="True" Padding="30"><StackPanel HorizontalAlignment="Center"><TextBlock Text="Drop one texture image" FontSize="21" FontWeight="SemiBold" HorizontalAlignment="Center"/><TextBlock Text="PNG, JPG, WEBP, BMP or TIFF" Foreground="#69736B" HorizontalAlignment="Center" Margin="0,8,0,16"/><Button x:Name="ChooseTexture" Content="Choose image and import" HorizontalAlignment="Center"/></StackPanel></Border>
    <TextBlock Text="Creates an opaque metal material. Transparent pixels use a dark background. Images are resized to power-of-two dimensions, up to 1024 pixels per axis." Foreground="#69736B" TextWrapping="Wrap" Margin="0,18,0,12"/>
    <TextBlock Text="After import, reload textures or restart Radiant and search for the material name shown below." TextWrapping="Wrap" Foreground="#69736B"/>
   </StackPanel></TabItem>
   <TabItem Header="3D asset"><ScrollViewer VerticalScrollBarVisibility="Auto"><StackPanel Margin="0,18,0,0">
    <TextBlock Text="Stable Fast 3D" FontSize="21" FontWeight="SemiBold"/><TextBlock Text="Turn one object image into a textured Radiant mesh prefab." TextWrapping="Wrap" Foreground="#69736B" Margin="0,7,0,20"/>
    <TextBlock Text="3D PREFAB DESTINATION" FontSize="11" Foreground="#63755F" Margin="0,0,0,7"/><Grid Margin="0,0,0,16"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><TextBox x:Name="MeshFolder" AutomationProperties.Name="3D prefab destination folder"/><Button x:Name="BrowseMeshFolder" Grid.Column="1" Content="Choose folder" Margin="10,0,0,0"/></Grid>
    <Border x:Name="SF3DDrop" Background="#EAEFE5" BorderBrush="#BBCAB4" BorderThickness="1" CornerRadius="12" AllowDrop="True" Padding="27"><StackPanel HorizontalAlignment="Center"><TextBlock Text="⬡" Foreground="#758C68" FontSize="32" HorizontalAlignment="Center"/><TextBlock Text="Drop one object image" FontSize="21" FontWeight="SemiBold" HorizontalAlignment="Center" Margin="0,4,0,6"/><TextBlock Text="Generate a textured mesh and .map prefab" Foreground="#69736B" HorizontalAlignment="Center"/><Button x:Name="ChooseSF3D" Content="or choose an image" Margin="0,14,0,0" HorizontalAlignment="Center"/></StackPanel></Border>
    <Grid Margin="0,18,0,0"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="14"/><ColumnDefinition Width="*"/><ColumnDefinition Width="14"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
     <StackPanel><TextBlock Text="Longest edge · units" Margin="0,0,0,5"/><TextBox x:Name="MeshSize" Text="256"/></StackPanel>
     <StackPanel Grid.Column="2"><TextBlock Text="Target vertices" Margin="0,0,0,5"/><TextBox x:Name="MeshVertices" Text="1500"/></StackPanel>
     <StackPanel Grid.Column="4"><TextBlock Text="Texture" Margin="0,0,0,5"/><ComboBox x:Name="MeshTexture" SelectedIndex="1"><ComboBoxItem Content="512 px" Tag="512"/><ComboBoxItem Content="1024 px" Tag="1024"/><ComboBoxItem Content="2048 px" Tag="2048"/></ComboBox></StackPanel>
    </Grid>
    <TextBlock Text="The model runs locally in a separate Python environment. First use requires the Stable Fast 3D setup and approved Hugging Face model access." TextWrapping="Wrap" Foreground="#69736B" Margin="0,18,0,0"/>
   </StackPanel></ScrollViewer></TabItem>
  </TabControl>
  <Border Grid.Row="3" BorderBrush="#DDE3D8" BorderThickness="0,1,0,0" Padding="0,14,0,0" Margin="0,18,0,0"><StackPanel><TextBlock x:Name="Status" Text="Ready. Choose your folders, then drop an image." TextWrapping="Wrap"/>
   <ListBox x:Name="Results" MaxHeight="90" BorderThickness="0" Background="Transparent" ScrollViewer.HorizontalScrollBarVisibility="Disabled"><ListBox.ItemTemplate><DataTemplate><TextBlock Text="{Binding}" TextWrapping="Wrap" FontSize="12" Margin="0,5"/></DataTemplate></ListBox.ItemTemplate></ListBox>
   <StackPanel Orientation="Horizontal" HorizontalAlignment="Right" Margin="0,5,0,0"><Button x:Name="CopyMaterial" Content="Copy material name" Background="Transparent"/><Button x:Name="OpenLogs" Content="Conversion logs ↗" Background="Transparent"/></StackPanel>
  </StackPanel></Border>
 </Grid>
</Window>
'@
$window = [Windows.Markup.XamlReader]::Load((New-Object System.Xml.XmlNodeReader $markup))
$ui = @{}
foreach ($name in @('Game','BrowseGame','Tabs','Folder','Browse','DropZone','ChooseImages','AutoTexture','Mask','Depth','Orientation','Resolution','Cell','Threshold','OpenFolder','MaterialName','TextureDrop','ChooseTexture','MeshFolder','BrowseMeshFolder','SF3DDrop','ChooseSF3D','MeshSize','MeshVertices','MeshTexture','Status','Results','CopyMaterial','OpenLogs')) { $ui[$name] = $window.FindName($name) }
$ui.Game.Text = 'C:\Code\Cod4\Call of Duty 4'
$state = @{ Queue=New-Object System.Collections.Queue; Process=$null; Job=$null; Request=$null; Response=$null; Done=0; Failed=0; Material='' }
function Save-Preferences {
 if ($SmokeTest) { return }
 try { @{game=$ui.Game.Text; folder=$ui.Folder.Text; mesh_folder=$ui.MeshFolder.Text; mesh_size=$ui.MeshSize.Text; mesh_vertices=$ui.MeshVertices.Text; mesh_texture=$ui.MeshTexture.SelectedIndex; auto_texture=[bool]$ui.AutoTexture.IsChecked; depth=$ui.Depth.Text; resolution=$ui.Resolution.Text; cell=$ui.Cell.Text; threshold=$ui.Threshold.Text; mask=$ui.Mask.SelectedIndex; orientation=$ui.Orientation.SelectedIndex} | ConvertTo-Json | Set-Content -LiteralPath $settingsFile -Encoding UTF8 } catch { $ui.Status.Text='Could not remember settings.' }
}
if ((Test-Path -LiteralPath $settingsFile) -and -not $SmokeTest) {
 try { $saved=Get-Content -LiteralPath $settingsFile -Raw | ConvertFrom-Json
  foreach ($pair in @(@('Game','game'),@('Folder','folder'),@('MeshFolder','mesh_folder'),@('MeshSize','mesh_size'),@('MeshVertices','mesh_vertices'),@('Depth','depth'),@('Resolution','resolution'),@('Cell','cell'),@('Threshold','threshold'))) { if ($null -ne $saved.($pair[1])) { $ui[$pair[0]].Text=[string]$saved.($pair[1]) } }
  if ($saved.mask -in 0,1,2) { $ui.Mask.SelectedIndex=$saved.mask }; if ($saved.orientation -in 0,1) { $ui.Orientation.SelectedIndex=$saved.orientation }; if ($null -ne $saved.auto_texture) { $ui.AutoTexture.IsChecked=[bool]$saved.auto_texture }
  if ($saved.mesh_texture -in 0,1,2) { $ui.MeshTexture.SelectedIndex=$saved.mesh_texture }
 } catch { }
}
function Pick-Folder($control) {
 $dialog=New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.SelectedPath=$control.Text
 try { if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $control.Text=$dialog.SelectedPath; Save-Preferences } } finally { $dialog.Dispose() }
}
function Add-Images([string[]]$paths, [string]$kind='prefab') {
 try {
  $meshSize=$null; $meshVertices=$null
  if ($kind -in 'texture','sf3d' -and $paths.Count -ne 1) { throw 'Drop exactly one image in this tab.' }
  $game=$ui.Game.Text.Trim().Trim('"'); $folder=if ($kind -eq 'sf3d') {$ui.MeshFolder.Text.Trim().Trim('"')} else {$ui.Folder.Text.Trim().Trim('"')}
  if (($kind -eq 'texture' -or $ui.AutoTexture.IsChecked) -and -not (Test-Path -LiteralPath (Join-Path $game 'bin\converter.exe') -PathType Leaf)) { throw 'Choose the CoD4 folder containing bin\converter.exe.' }
  $settings=@{}
  if ($kind -eq 'prefab') {
   if (-not (Test-Path -LiteralPath $folder -PathType Container)) { throw 'Choose an existing prefab destination folder.' }
   $culture=[Globalization.CultureInfo]::InvariantCulture
   $depth=[double]::Parse($ui.Depth.Text,$culture); $cell=[double]::Parse($ui.Cell.Text,$culture); $resolution=[int]::Parse($ui.Resolution.Text,$culture); $threshold=[int]::Parse($ui.Threshold.Text,$culture)
   if ([double]::IsNaN($depth) -or [double]::IsInfinity($depth) -or $depth -lt 0.125 -or $depth -gt 8192) { throw 'Depth must be 0.125 to 8192.' }
   if ([double]::IsNaN($cell) -or [double]::IsInfinity($cell) -or $cell -lt 0.125 -or $cell -gt 8192) { throw 'Units per cell must be 0.125 to 8192.' }
   if ($resolution -lt 4 -or $resolution -gt 512 -or $threshold -lt 0 -or $threshold -gt 255) { throw 'Resolution must be 4–512; threshold must be 0–255.' }
   $settings=@{depth=$depth;cell=$cell;resolution=$resolution;threshold=$threshold;mode=[string]$ui.Mask.SelectedItem.Tag;orientation=[string]$ui.Orientation.SelectedItem.Tag}
  }
  if ($kind -eq 'sf3d') {
   if (-not (Test-Path -LiteralPath $folder -PathType Container)) { throw 'Choose an existing 3D prefab destination folder.' }
   $culture=[Globalization.CultureInfo]::InvariantCulture; $meshSize=[double]::Parse($ui.MeshSize.Text,$culture); $meshVertices=[int]::Parse($ui.MeshVertices.Text,$culture)
   if ([double]::IsNaN($meshSize) -or [double]::IsInfinity($meshSize) -or $meshSize -lt 1 -or $meshSize -gt 32768) { throw 'Longest edge must be 1–32768 units.' }
   if ($meshVertices -lt 100 -or $meshVertices -gt 10000) { throw 'Target vertices must be 100–10000.' }
  }
  foreach ($path in $paths) {
   if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or [IO.Path]::GetExtension($path).ToLowerInvariant() -notin '.png','.jpg','.jpeg','.webp','.bmp','.tif','.tiff') { throw 'Choose PNG, JPG, WEBP, BMP or TIFF images.' }
  }
  foreach ($path in $paths) { $state.Queue.Enqueue(@{kind=$kind;source=$path;folder=$folder;game=$game;auto_texture=[bool]$ui.AutoTexture.IsChecked;settings=$settings;name=$ui.MaterialName.Text;longest_edge=$meshSize;target_vertices=$meshVertices;texture_resolution=[int]$ui.MeshTexture.SelectedItem.Tag}) }
  Save-Preferences; $ui.Status.Text="$($paths.Count) image(s) queued."
 } catch { $ui.Status.Text=$_.Exception.Message }
}
function Pick-Images([string]$kind) {
 $dialog=New-Object Microsoft.Win32.OpenFileDialog; $dialog.Multiselect=$kind -eq 'prefab'; $dialog.Filter='Images|*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tif;*.tiff'
 if ($dialog.ShowDialog($window)) { Add-Images $dialog.FileNames $kind }
}
$ui.BrowseGame.Add_Click({ Pick-Folder $ui.Game }); $ui.Browse.Add_Click({ Pick-Folder $ui.Folder }); $ui.BrowseMeshFolder.Add_Click({ Pick-Folder $ui.MeshFolder })
$ui.ChooseImages.Add_Click({ Pick-Images 'prefab' }); $ui.ChooseTexture.Add_Click({ Pick-Images 'texture' }); $ui.ChooseSF3D.Add_Click({ Pick-Images 'sf3d' })
foreach ($zone in @($ui.DropZone,$ui.TextureDrop,$ui.SF3DDrop)) {
 $zone.Add_PreviewDragOver({param($sender,$eventArgs); $eventArgs.Effects=if ($eventArgs.Data.GetDataPresent([Windows.DataFormats]::FileDrop)) {[Windows.DragDropEffects]::Copy} else {[Windows.DragDropEffects]::None}; $eventArgs.Handled=$true })
 $zone.Add_Drop({param($sender,$eventArgs); if ($eventArgs.Data.GetDataPresent([Windows.DataFormats]::FileDrop)) { $kind=if ($sender.Name -eq 'TextureDrop') {'texture'} elseif ($sender.Name -eq 'SF3DDrop') {'sf3d'} else {'prefab'}; Add-Images $eventArgs.Data.GetData([Windows.DataFormats]::FileDrop) $kind }; $eventArgs.Handled=$true })
}
$ui.OpenFolder.Add_Click({if (Test-Path -LiteralPath $ui.Folder.Text -PathType Container) { Start-Process explorer.exe -ArgumentList ('"'+$ui.Folder.Text+'"') }})
$ui.OpenLogs.Add_Click({$path=Join-Path $appRoot '.prefabdrop\logs'; if (Test-Path -LiteralPath $path) { Start-Process explorer.exe -ArgumentList ('"'+$path+'"') } else { $ui.Status.Text='No material conversions have run yet.' }})
$ui.CopyMaterial.Add_Click({if ($state.Material) { [Windows.Clipboard]::SetText($state.Material); $ui.Status.Text='Copied '+$state.Material }})
function Tick-Queue {
 if ($null -ne $state.Process -and $state.Process.HasExited) {
  try {
   if (-not (Test-Path -LiteralPath $state.Response)) { throw 'The converter worker stopped before returning a result. Check Python and Pillow installation.' }
   $report=Get-Content -LiteralPath $state.Response -Raw -Encoding UTF8 | ConvertFrom-Json
   if (-not $report.ok) { throw $report.error }
   $state.Material=[string]$report.result.material; $state.Done++
   $message=if ($state.Job.kind -eq 'texture') {"Imported $($state.Material) - reload textures in Radiant."} elseif ($state.Job.kind -eq 'sf3d') {"Saved $([IO.Path]::GetFileName($report.result.output)) - $($report.result.patches) mesh patches - $($state.Material)"} else {"Saved $([IO.Path]::GetFileName($report.result.output)) - $($report.result.brushes) brushes - $($state.Material)"}
   [void]$ui.Results.Items.Insert(0,$message)
  } catch { $state.Failed++; [void]$ui.Results.Items.Insert(0,"Failed: $([IO.Path]::GetFileName($state.Job.source)) - $($_.Exception.Message)") }
  finally { foreach ($path in @($state.Request,$state.Response)) { if ([IO.File]::Exists($path)) { [IO.File]::Delete($path) } }; $state.Process.Dispose(); $state.Process=$null; $ui.Status.Text="$($state.Done) completed | $($state.Failed) failed | $($state.Queue.Count) queued" }
 }
 if ($null -eq $state.Process -and $state.Queue.Count -gt 0) {
  $state.Job=$state.Queue.Dequeue(); $id=[Guid]::NewGuid().ToString(); $state.Request=Join-Path ([IO.Path]::GetTempPath()) ($id+'.request.json'); $state.Response=Join-Path ([IO.Path]::GetTempPath()) ($id+'.response.json')
  try {
   $state.Job | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $state.Request -Encoding UTF8
   $start=New-Object Diagnostics.ProcessStartInfo; $start.FileName=$workerPython
   $start.Arguments=(@((Join-Path $appRoot 'worker.py'),$state.Request,$state.Response) | ForEach-Object {'"'+$_+'"'}) -join ' '
   $start.UseShellExecute=$false; $start.CreateNoWindow=$true; $start.EnvironmentVariables['PYTHONIOENCODING']='utf-8'
   $state.Process=[Diagnostics.Process]::Start($start); $ui.Status.Text='Converting '+[IO.Path]::GetFileName($state.Job.source)+'...'
  } catch { $state.Process=$null; $state.Failed++; if ([IO.File]::Exists($state.Request)) { [IO.File]::Delete($state.Request) }; $ui.Status.Text=$_.Exception.Message }
 }
}
$timer=New-Object Windows.Threading.DispatcherTimer; $timer.Interval=[TimeSpan]::FromMilliseconds(150); $timer.Add_Tick({Tick-Queue})
$window.Add_Closing({param($sender,$eventArgs); if ($null -ne $state.Process -or $state.Queue.Count -gt 0) { $eventArgs.Cancel=$true; $ui.Status.Text='Finishing queued conversions. Close when they finish.' } else {Save-Preferences; $timer.Stop()}})
if ($SmokeTest) {
 $ui.Tabs.SelectedIndex=$RenderTab; $window.Measure([Windows.Size]::new(780,900)); $window.Arrange([Windows.Rect]::new(0,0,780,900)); $window.UpdateLayout()
 if ($RenderPath) {
  $surface=$window.Content; $surface.Measure([Windows.Size]::new(720,830)); $surface.Arrange([Windows.Rect]::new(0,0,720,830)); $surface.UpdateLayout()
  $bitmap=New-Object Windows.Media.Imaging.RenderTargetBitmap 780,900,96,96,([Windows.Media.PixelFormats]::Pbgra32); $visual=New-Object Windows.Media.DrawingVisual; $drawing=$visual.RenderOpen(); $drawing.DrawRectangle([Windows.Media.BrushConverter]::new().ConvertFromString('#F5F5F0'),$null,[Windows.Rect]::new(0,0,780,900)); $drawing.Close(); $bitmap.Render($visual); $bitmap.Render($surface)
  $encoder=New-Object Windows.Media.Imaging.PngBitmapEncoder; $encoder.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($bitmap)); $stream=[IO.File]::Create($RenderPath); try {$encoder.Save($stream)} finally {$stream.Dispose()}
 }
 if ($TestFolder) {
  $ui.Folder.Text=$TestFolder; $sample=Join-Path $appRoot 'examples\honeycomb.png'
  foreach ($zone in @($ui.DropZone,$ui.TextureDrop)) {
   $data=New-Object Windows.DataObject; $data.SetData([Windows.DataFormats]::FileDrop,[string[]]@($sample)); $constructor=[Windows.DragEventArgs].GetConstructors([Reflection.BindingFlags]'Instance,NonPublic,Public')[0]
   $drop=$constructor.Invoke([object[]]@($data.PSObject.BaseObject,[Windows.DragDropKeyStates]::None,[Windows.DragDropEffects]::Copy,$zone.PSObject.BaseObject,[Windows.Point]::new(10,10))); $drop.RoutedEvent=[Windows.DragDrop]::DropEvent; $zone.RaiseEvent($drop)
  }
  $deadline=[DateTime]::Now.AddSeconds(120)
  while (($state.Queue.Count -gt 0 -or $null -ne $state.Process) -and [DateTime]::Now -lt $deadline) {Tick-Queue; Start-Sleep -Milliseconds 100}
  if ($state.Done -ne 2 -or $state.Failed) {throw "Integration failed: $($ui.Results.Items -join ', ') $($ui.Status.Text)"}
  Write-Output 'PASS: both tab drop handlers and real auto-textured prefab / standalone material conversions.'
 }
 Write-Output "PASS: $($ui.Count) WPF controls loaded."; $window.Close()
} else {$timer.Start(); [void]$window.ShowDialog()}
