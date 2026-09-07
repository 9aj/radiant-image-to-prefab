param([switch]$SmokeTest, [string]$TestFolder, [string]$RenderPath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms
$appRoot = $PSScriptRoot
$settingsFile = Join-Path $appRoot 'preferences.json'
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$venvPython = Join-Path $appRoot '.venv\Scripts\python.exe'
$workerPython = if (Test-Path -LiteralPath $venvPython) { $venvPython } elseif (Test-Path -LiteralPath $bundledPython) { $bundledPython } else { (Get-Command python -ErrorAction Stop).Source }
[xml]$markup = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Title="Prefab Drop" Width="760" Height="780" MinWidth="620" MinHeight="740" WindowStartupLocation="CenterScreen" Background="#F5F5F0" FontFamily="Segoe UI" Foreground="#25332D">
 <Window.Resources>
  <Style TargetType="Button">
   <Setter Property="Background" Value="#E7EBE3"/><Setter Property="Foreground" Value="#25332D"/><Setter Property="Padding" Value="16,10"/><Setter Property="Cursor" Value="Hand"/><Setter Property="FontSize" Value="13"/>
   <Setter Property="Template"><Setter.Value><ControlTemplate TargetType="Button"><Border x:Name="B" Background="{TemplateBinding Background}" CornerRadius="7" Padding="{TemplateBinding Padding}"><ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/></Border><ControlTemplate.Triggers><Trigger Property="IsMouseOver" Value="True"><Setter TargetName="B" Property="Opacity" Value="0.8"/></Trigger><Trigger Property="IsEnabled" Value="False"><Setter TargetName="B" Property="Opacity" Value="0.4"/></Trigger></ControlTemplate.Triggers></ControlTemplate></Setter.Value></Setter>
  </Style>
  <Style TargetType="TextBox"><Setter Property="Padding" Value="10,8"/><Setter Property="BorderBrush" Value="#D7DED3"/><Setter Property="VerticalContentAlignment" Value="Center"/><Setter Property="Background" Value="White"/></Style>
  <Style TargetType="ComboBox"><Setter Property="Padding" Value="8,7"/><Setter Property="VerticalContentAlignment" Value="Center"/></Style>
 </Window.Resources>
 <Grid Margin="32,26">
  <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <Grid Margin="0,0,0,24">
   <StackPanel><TextBlock Text="PREFAB DROP" FontSize="12" FontWeight="SemiBold" Foreground="#63755F"/><TextBlock Text="Image in. Brushes out." FontSize="28" FontWeight="SemiBold" Margin="0,7,0,4"/><TextBlock Text="Drop a silhouette. Save it straight to your map source folder." FontSize="13" Foreground="#69736B"/></StackPanel>
   <Border HorizontalAlignment="Right" VerticalAlignment="Top" Background="#E7EBE3" Padding="10,5" CornerRadius="12"><TextBlock Text="COD4 / IW3XO" FontSize="10" FontWeight="SemiBold"/></Border>
  </Grid>
  <StackPanel Grid.Row="1" Margin="0,0,0,20"><TextBlock Text="PREFAB FOLDER" FontSize="11" FontWeight="SemiBold" Foreground="#63755F" Margin="0,0,0,8"/>
   <Grid><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><TextBox x:Name="Folder" ToolTip="Choose or paste the folder where .map prefabs should be saved" AutomationProperties.Name="Prefab destination folder"/><Button x:Name="Browse" Grid.Column="1" Content="Choose folder" Margin="10,0,0,0"/></Grid>
  </StackPanel>
  <Border x:Name="DropZone" Grid.Row="2" Background="#EAEFE5" BorderBrush="#BBCAB4" BorderThickness="1" CornerRadius="12" AllowDrop="True" MinHeight="180" Margin="0,0,0,18">
   <StackPanel VerticalAlignment="Center" HorizontalAlignment="Center" Margin="24"><TextBlock Text="⬡" FontSize="36" HorizontalAlignment="Center" Foreground="#758C68" Margin="0,0,0,5"/><TextBlock x:Name="DropTitle" Text="Drop images here" FontSize="21" FontWeight="SemiBold" HorizontalAlignment="Center"/><TextBlock Text="PNG, JPG, WEBP, BMP or TIFF" FontSize="12" Foreground="#69736B" HorizontalAlignment="Center" Margin="0,7,0,14"/><Button x:Name="ChooseImages" Content="or choose images" Background="#DCE5D5" HorizontalAlignment="Center"/></StackPanel>
  </Border>
  <StackPanel Grid.Row="3" Margin="0,0,0,18">
   <Grid><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="16"/><ColumnDefinition Width="*"/><ColumnDefinition Width="16"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
    <StackPanel><TextBlock Text="Solid area" FontSize="12" Margin="0,0,0,6"/><ComboBox x:Name="Mask" SelectedIndex="0"><ComboBoxItem Content="Dark pixels" Tag="dark"/><ComboBoxItem Content="Light pixels" Tag="light"/><ComboBoxItem Content="PNG transparency" Tag="alpha"/></ComboBox></StackPanel>
    <StackPanel Grid.Column="2"><TextBlock Text="Depth · units" FontSize="12" Margin="0,0,0,6"/><TextBox x:Name="Depth" Text="32" AutomationProperties.Name="Extrusion depth in units"/></StackPanel>
    <StackPanel Grid.Column="4"><TextBlock Text="Orientation" FontSize="12" Margin="0,0,0,6"/><ComboBox x:Name="Orientation" SelectedIndex="0"><ComboBoxItem Content="Floor" Tag="floor"/><ComboBoxItem Content="Wall" Tag="wall"/></ComboBox></StackPanel>
   </Grid>
   <Expander Header="Size and detail" Margin="0,14,0,0" Foreground="#63755F"><Grid Margin="0,10,0,0"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="16"/><ColumnDefinition Width="*"/><ColumnDefinition Width="16"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
    <StackPanel><TextBlock Text="Longest edge · cells" FontSize="12" Margin="0,0,0,6"/><TextBox x:Name="Resolution" Text="96"/></StackPanel><StackPanel Grid.Column="2"><TextBlock Text="Units per cell" FontSize="12" Margin="0,0,0,6"/><TextBox x:Name="Cell" Text="4"/></StackPanel><StackPanel Grid.Column="4"><TextBlock Text="Threshold · 0–255" FontSize="12" Margin="0,0,0,6"/><TextBox x:Name="Threshold" Text="128"/></StackPanel>
   </Grid></Expander>
  </StackPanel>
  <Border Grid.Row="4" BorderBrush="#DDE3D8" BorderThickness="0,1,0,0" Padding="0,14,0,0"><StackPanel><TextBlock x:Name="Status" Text="Choose a folder to get started." FontSize="13" TextWrapping="Wrap"/>
   <ListBox x:Name="Results" Background="Transparent" BorderThickness="0" MaxHeight="90" Margin="0,8,0,0" ScrollViewer.HorizontalScrollBarVisibility="Disabled"><ListBox.ItemTemplate><DataTemplate><TextBlock Text="{Binding}" TextWrapping="Wrap" FontSize="12" Margin="0,3"/></DataTemplate></ListBox.ItemTemplate></ListBox>
  </StackPanel></Border>
  <Grid Grid.Row="5" Margin="0,14,0,0"><TextBlock Text="Grid-based brushes · caulk material" FontSize="11" Foreground="#7C877D" VerticalAlignment="Center"/><Button x:Name="OpenFolder" Content="Open prefab folder ↗" HorizontalAlignment="Right" Padding="10,7" Background="Transparent"/></Grid>
 </Grid>
</Window>
'@
$window = [Windows.Markup.XamlReader]::Load((New-Object System.Xml.XmlNodeReader $markup))
$ui = @{}
foreach ($name in @('Folder','Browse','DropZone','DropTitle','ChooseImages','Mask','Depth','Orientation','Resolution','Cell','Threshold','Status','Results','OpenFolder')) { $ui[$name] = $window.FindName($name) }
$state = @{ Queue = New-Object System.Collections.Queue; Process = $null; Job = $null; Temp = $null; Done = 0; Failed = 0 }
function Save-Preferences {
    if ($SmokeTest) { return }
    try { @{ folder=$ui.Folder.Text; depth=$ui.Depth.Text; resolution=$ui.Resolution.Text; cell=$ui.Cell.Text; threshold=$ui.Threshold.Text; mask=$ui.Mask.SelectedIndex; orientation=$ui.Orientation.SelectedIndex } | ConvertTo-Json | Set-Content -LiteralPath $settingsFile -Encoding UTF8 }
    catch { $ui.Status.Text = 'Could not remember settings. Conversion is still available.' }
}
if ((Test-Path -LiteralPath $settingsFile) -and -not $SmokeTest) {
    try {
        $saved = Get-Content -LiteralPath $settingsFile -Raw | ConvertFrom-Json
        $ui.Folder.Text = [string]$saved.folder
        foreach ($pair in @(@('Depth','depth'),@('Resolution','resolution'),@('Cell','cell'),@('Threshold','threshold'))) { if ($null -ne $saved.($pair[1])) { $ui[$pair[0]].Text = [string]$saved.($pair[1]) } }
        if ($saved.mask -in 0,1,2) { $ui.Mask.SelectedIndex = $saved.mask }; if ($saved.orientation -in 0,1) { $ui.Orientation.SelectedIndex = $saved.orientation }
        $ui.Status.Text = 'Ready. Drop images to convert and save.'
    } catch { }
}
function Add-Images([string[]]$paths) {
    try {
        $folder = $ui.Folder.Text.Trim().Trim('"')
        if (-not (Test-Path -LiteralPath $folder -PathType Container)) { throw 'Choose an existing prefab folder first.' }
        $folder = (Get-Item -LiteralPath $folder).FullName
        $culture = [Globalization.CultureInfo]::InvariantCulture
        $depth = [double]::Parse($ui.Depth.Text, $culture); $cell = [double]::Parse($ui.Cell.Text, $culture)
        $resolution = [int]::Parse($ui.Resolution.Text, $culture); $threshold = [int]::Parse($ui.Threshold.Text, $culture)
        if ([double]::IsNaN($depth) -or [double]::IsInfinity($depth) -or $depth -lt 0.125 -or $depth -gt 8192) { throw 'Depth must be between 0.125 and 8192 units.' }
        if ([double]::IsNaN($cell) -or [double]::IsInfinity($cell) -or $cell -lt 0.125 -or $cell -gt 8192) { throw 'Units per cell must be between 0.125 and 8192.' }
        if ($resolution -lt 4 -or $resolution -gt 512) { throw 'Resolution must be between 4 and 512 cells.' }
        if ($threshold -lt 0 -or $threshold -gt 255) { throw 'Threshold must be between 0 and 255.' }
        $accepted = 0
        foreach ($path in $paths) {
            if ((Test-Path -LiteralPath $path -PathType Leaf) -and [IO.Path]::GetExtension($path).ToLowerInvariant() -in '.png','.jpg','.jpeg','.webp','.bmp','.tif','.tiff') {
                $state.Queue.Enqueue(@{ Source=$path; Folder=$folder; Depth=$depth.ToString($culture); Cell=$cell.ToString($culture); Resolution=$resolution; Threshold=$threshold; Mode=[string]$ui.Mask.SelectedItem.Tag; Orientation=[string]$ui.Orientation.SelectedItem.Tag }); $accepted++
            } else { [void]$ui.Results.Items.Insert(0, "Skipped: $([IO.Path]::GetFileName($path)) - unsupported file.") }
        }
        if ($accepted -eq 0) { $ui.Status.Text = 'Drop PNG, JPG, WEBP, BMP or TIFF images.' } else { $ui.Status.Text = "$accepted image(s) queued."; Save-Preferences }
    } catch { $ui.Status.Text = $_.Exception.Message }
}
$ui.Browse.Add_Click({
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description = 'Choose the map source folder where prefabs will be saved'; $dialog.SelectedPath = $ui.Folder.Text
    try { if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $ui.Folder.Text = $dialog.SelectedPath; Save-Preferences; $ui.Status.Text = 'Ready. Drop images to convert and save.' } } finally { $dialog.Dispose() }
})
$ui.ChooseImages.Add_Click({ $dialog = New-Object Microsoft.Win32.OpenFileDialog; $dialog.Multiselect = $true; $dialog.Filter = 'Images|*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tif;*.tiff'; if ($dialog.ShowDialog($window)) { Add-Images $dialog.FileNames } })
$ui.DropZone.Add_PreviewDragOver({ param($sender,$eventArgs); $eventArgs.Effects = if ($eventArgs.Data.GetDataPresent([Windows.DataFormats]::FileDrop)) { [Windows.DragDropEffects]::Copy } else { [Windows.DragDropEffects]::None }; $eventArgs.Handled = $true; $ui.DropZone.Background = [Windows.Media.BrushConverter]::new().ConvertFromString('#DCE7D4') })
$ui.DropZone.Add_DragLeave({ $ui.DropZone.Background = [Windows.Media.BrushConverter]::new().ConvertFromString('#EAEFE5') })
$ui.DropZone.Add_Drop({ param($sender,$eventArgs); $ui.DropZone.Background = [Windows.Media.BrushConverter]::new().ConvertFromString('#EAEFE5'); if ($eventArgs.Data.GetDataPresent([Windows.DataFormats]::FileDrop)) { Add-Images $eventArgs.Data.GetData([Windows.DataFormats]::FileDrop) }; $eventArgs.Handled = $true })
$ui.OpenFolder.Add_Click({ if (Test-Path -LiteralPath $ui.Folder.Text -PathType Container) { Start-Process explorer.exe -ArgumentList ('"' + $ui.Folder.Text + '"') } else { $ui.Status.Text = 'Choose an existing prefab folder first.' } })

# Poll serial child processes rather than blocking the window during conversions.
function Tick-Queue {
    if ($null -ne $state.Process -and $state.Process.HasExited) {
        try {
            $stdout = $state.Process.StandardOutput.ReadToEnd(); $stderr = $state.Process.StandardError.ReadToEnd()
            if ($state.Process.ExitCode -ne 0) { throw $stderr.Trim() }
            $report = $stdout | ConvertFrom-Json
            $stem = [regex]::Replace([IO.Path]::GetFileNameWithoutExtension($state.Job.Source), '[^A-Za-z0-9_-]', '_').Trim('_')
            if (-not $stem) { $stem = 'image' }; if ($stem.Length -gt 80) { $stem = $stem.Substring(0,80) }; $stem = 'prefab_' + $stem
            $suffix = 0
            while ($true) {
                $name = if ($suffix -eq 0) { "$stem.map" } else { "${stem}_$suffix.map" }
                $destination = Join-Path $state.Job.Folder $name
                try { [IO.File]::Copy($state.Temp, $destination, $false); break }
                catch [IO.IOException] { if ([IO.File]::Exists($destination)) { $suffix++; continue }; throw }
            }
            $state.Done++; [void]$ui.Results.Items.Insert(0, "Saved $name - $($report.brushes) brushes")
        } catch { $state.Failed++; [void]$ui.Results.Items.Insert(0, "Failed: $([IO.Path]::GetFileName($state.Job.Source)) - $($_.Exception.Message)") }
        finally {
            if ($state.Temp -and [IO.File]::Exists($state.Temp)) { [IO.File]::Delete($state.Temp) }
            $state.Process.Dispose(); $state.Process = $null
            $ui.Status.Text = "$($state.Done) saved | $($state.Failed) failed | $($state.Queue.Count) queued"; $ui.DropTitle.Text = 'Drop images here'
        }
    }
    if ($null -eq $state.Process -and $state.Queue.Count -gt 0) {
        $state.Job = $state.Queue.Dequeue(); $state.Temp = Join-Path ([IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString() + '.map'); $job = $state.Job
        $arguments = @((Join-Path $appRoot 'app.py'), $job.Source, '-o', $state.Temp, '--mode', $job.Mode, '--depth', $job.Depth, '--cell', $job.Cell, '--resolution', $job.Resolution, '--threshold', $job.Threshold, '--orientation', $job.Orientation)
        $start = New-Object Diagnostics.ProcessStartInfo; $start.FileName = $workerPython
        $start.Arguments = ($arguments | ForEach-Object { '"' + [string]$_ + '"' }) -join ' '
        $start.UseShellExecute = $false; $start.CreateNoWindow = $true; $start.RedirectStandardOutput = $true; $start.RedirectStandardError = $true
        $start.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'; $start.StandardOutputEncoding = [Text.Encoding]::UTF8; $start.StandardErrorEncoding = [Text.Encoding]::UTF8
        try { $state.Process = [Diagnostics.Process]::Start($start); $ui.Status.Text = "Converting $([IO.Path]::GetFileName($job.Source))..."; $ui.DropTitle.Text = 'Converting...' }
        catch { $state.Process = $null; $state.Failed++; $ui.Status.Text = "Could not start converter: $($_.Exception.Message)" }
    }
}
$timer = New-Object Windows.Threading.DispatcherTimer; $timer.Interval = [TimeSpan]::FromMilliseconds(150); $timer.Add_Tick({ Tick-Queue })
$window.Add_Closing({ param($sender,$eventArgs); if ($null -ne $state.Process -or $state.Queue.Count -gt 0) { $eventArgs.Cancel = $true; $ui.Status.Text = 'Finishing queued conversions. Close the window when they finish.' } else { Save-Preferences; $timer.Stop() } })
if ($SmokeTest) {
    $window.Measure([Windows.Size]::new(760,780)); $window.Arrange([Windows.Rect]::new(0,0,760,780)); $window.UpdateLayout()
    if ($RenderPath) {
        $surface = $window.Content
        $surface.Measure([Windows.Size]::new(696,690)); $surface.Arrange([Windows.Rect]::new(0,0,696,690)); $surface.UpdateLayout()
        $bitmap = New-Object Windows.Media.Imaging.RenderTargetBitmap 760,780,96,96,([Windows.Media.PixelFormats]::Pbgra32)
        $visual = New-Object Windows.Media.DrawingVisual
        $drawing = $visual.RenderOpen()
        $drawing.DrawRectangle([Windows.Media.BrushConverter]::new().ConvertFromString('#F5F5F0'), $null, [Windows.Rect]::new(0,0,760,780))
        $drawing.Close(); $bitmap.Render($visual); $bitmap.Render($surface)
        $encoder = New-Object Windows.Media.Imaging.PngBitmapEncoder
        $encoder.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($bitmap))
        $stream = [IO.File]::Create($RenderPath)
        try { $encoder.Save($stream) } finally { $stream.Dispose() }
    }
    if ($TestFolder) {
        $ui.Folder.Text = Join-Path $TestFolder 'missing-folder'
        Add-Images @((Join-Path $appRoot 'examples\honeycomb.png'))
        if ($state.Queue.Count -ne 0) { throw 'Invalid destination was accepted.' }
        $ui.Folder.Text = $TestFolder
        $ui.Depth.Text = 'NaN'
        Add-Images @((Join-Path $appRoot 'examples\honeycomb.png'))
        if ($state.Queue.Count -ne 0) { throw 'Invalid depth was accepted.' }
        $ui.Depth.Text = '32'
        $data = New-Object Windows.DataObject
        $data.SetData([Windows.DataFormats]::FileDrop, [string[]]@((Join-Path $appRoot 'examples\honeycomb.png'),(Join-Path $appRoot 'examples\honeycomb.png')))
        $constructor = [Windows.DragEventArgs].GetConstructors([Reflection.BindingFlags]'Instance,NonPublic,Public')[0]
        $drop = $constructor.Invoke([object[]]@($data.PSObject.BaseObject, [Windows.DragDropKeyStates]::None, [Windows.DragDropEffects]::Copy, $ui.DropZone.PSObject.BaseObject, [Windows.Point]::new(10,10)))
        $drop.RoutedEvent = [Windows.DragDrop]::DropEvent
        $ui.DropZone.RaiseEvent($drop)
        $deadline = [DateTime]::Now.AddSeconds(30)
        while (($state.Queue.Count -gt 0 -or $null -ne $state.Process) -and [DateTime]::Now -lt $deadline) { Tick-Queue; Start-Sleep -Milliseconds 100 }
        if ($state.Done -ne 2 -or $state.Failed -ne 0) { throw "Queue test failed: $($ui.Results.Items -join ', ')" }
        Write-Output 'PASS: drop event, invalid folder/depth checks, and background queue with duplicate filenames.'
    }
    Write-Output "PASS: WPF layout loaded; $($ui.Count) controls found."
    $window.Close()
} else { $timer.Start(); [void]$window.ShowDialog() }
