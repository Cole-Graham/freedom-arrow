using System.Diagnostics;
using BAModManager.Core;
using static BAModManager.Core.Loc;

namespace BAModManager.Ui;

/// <summary>
/// The Mod Launcher window (BAModLauncher.exe): one PLAY button that installs/updates MelonLoader and the modpack
/// this copy is set up for, and starts the game; a button to turn mods off and play normally with Anti-Cheat;
/// and a few settings. Players can't change the modpack - the modder sets it up once (launcher.json).
/// </summary>
internal sealed class LauncherForm : Form
{
    private readonly ManagerConfig _cfg;
    private readonly LauncherService _launcher;
    private readonly string[] _startupFiles;
    private readonly Image? _logo;
    private readonly Icon? _icon;

    private readonly PictureBox _packPicture;
    private readonly Label _packName;
    private readonly Label _packVersion;
    private readonly Label _modsState;
    private readonly LaunchProgressPanel _panel;
    private readonly Button? _lang;
    private Action? _placeHeaderButtons;
    private readonly NewsPanel? _news;
    private readonly Label? _linuxState;
    private readonly Control? _header;
    private readonly Button _play;
    private readonly Button _vanilla;
    private readonly Button _settings;
    private readonly Button _setUp;
    private readonly FlowLayoutPanel _channels;

    private string? _gameDir;
    private bool _busy;
    private readonly List<string> _log = new();
    private readonly System.Windows.Forms.Timer _gameWatch = new() { Interval = 1000 };
    private bool _gameRunning;
    private readonly System.Windows.Forms.Timer _updateCheck = new() { Interval = 20 * 60 * 1000 };

    public LauncherForm(ManagerConfig cfg, string[]? startupFiles = null)
    {
        _cfg = cfg;
        _launcher = new LauncherService(cfg);
        _startupFiles = startupFiles ?? Array.Empty<string>();
        _logo = MainForm.LoadEmbeddedImage("Assets.logo.png");
        _icon = MainForm.LoadEmbeddedIcon("Assets.icon.ico");

        AutoScaleDimensions = new SizeF(96F, 96F);   // laid out at 100 %, scaled for the screen
        AutoScaleMode = AutoScaleMode.Dpi;
        Text = AppInfo.FullName;
        if (_icon != null) Icon = _icon;
        Font = Theme.Ui(10f);
        BackColor = Theme.Background;
        ForeColor = Theme.Text;
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
#if FA_DEV45
        // 1.1.14 (Osama 21 Nov 2026): freedomarrow.app look - menu-art header with the title logo, red/black colours,
        // condensed headings, and a progress panel that shows steps, MB, speed, time left and when data last arrived.
        // 1.1.15 (Osama 22 Nov 2026): a News column on the right with the Battlefield report and the patch notes.
        // Osama 22 Nov 2026: "make the launcher bigger so more of it is art", "or just more space, its very cramped":
        // a full-width 1440x320 header and a wide News column. On a smaller screen the window shrinks to fit: the header gives up
        // height first (FitScreen).
        // Osama 22 Nov 2026: "news and patch notes should be able to get more room", "no one is playing on steam deck"
        _news = new NewsPanel { Dock = DockStyle.Right, Width = DesignNewsWidth };   // features and patch notes side by side
        ClientSize = new Size(DesignWidth, DesignHeight);
        Padding = new Padding(0);
        var header = new FaBanner(MainForm.LoadEmbeddedImage("Assets.fa_banner.jpg")) { Dock = DockStyle.Top, Height = DesignHeaderHeight };
        // 中文 / English switch, like the button on freedomarrow.app (Osama 21 Nov 2026: "Make sure there's a Chinese switch").
        _lang = Theme.MakeButton(Loc.IsChinese ? "English" : "中文", ButtonKind.Secondary);
        _lang.AutoSize = false;
        _lang.Size = new Size(72, 25);
        _lang.MinimumSize = new Size(0, 0);
        _lang.Padding = new Padding(0);
        _lang.Margin = new Padding(0);
        _lang.Location = new Point(DesignWidth - 72 - 14, 9);
        _lang.Font = Loc.IsChinese ? Theme.Head(10.5f, semi: true) : AppFonts.Chinese(9f, FontStyle.Bold);
        _lang.BackColor = Theme.Background;
        _lang.Click += (_, _) => ToggleChinese();
        header.RightInset = 72 + 8;
        header.Controls.Add(_lang);
        // Osama 22 Nov 2026: "make sure there's a big button to visit our website" / "our website button should be on the top"
        var site = Theme.MakeButton(T("VISIT FREEDOMARROW.APP"), ButtonKind.Primary);
        site.AutoSize = false;
        site.Size = new Size(270, 46);
        site.MinimumSize = new Size(0, 0);
        site.Margin = new Padding(0);
        site.Font = Theme.Head(16f);
        site.Location = new Point(DesignWidth - 270 - 14, 44);
        // keep both buttons at the top right when the window is narrowed for a small screen (FitScreen)
        _placeHeaderButtons = () =>
        {
            _lang.Left = header.Width - _lang.Width - header.LogicalToDeviceUnits(14);
            site.Left = header.Width - site.Width - header.LogicalToDeviceUnits(14);
        };
        header.Resize += (_, _) => _placeHeaderButtons();
        site.Click += (_, _) => LauncherNews.Open(LauncherNews.Site);
        header.Controls.Add(site);
        var body = new Panel { Dock = DockStyle.Fill, BackColor = Theme.Background, Padding = new Padding(28, 14, 28, 12) };
#else
        ClientSize = new Size(460, 640);
        Padding = new Padding(28, 22, 28, 18);
        var body = this;

        // ── brand ──
        var header = new Panel { Dock = DockStyle.Top, Height = 70, BackColor = Theme.Background };
        var logoBox = new PictureBox
        {
            Image = _logo,
            SizeMode = PictureBoxSizeMode.Zoom,
            Size = new Size(52, 52),
            Location = new Point(0, 4),
            BackColor = Color.Transparent,
        };
        var brandSmall = new Label { Text = "BROKEN ARROW", AutoSize = true, Font = Theme.BrandSmall(8.5f), ForeColor = Theme.Accent, Location = new Point(62, 8) };
        var brandBig = new Label { Text = AppInfo.ShortName, AutoSize = true, Font = Theme.BrandLarge(16f), ForeColor = Theme.Text, Location = new Point(60, 24) };
        header.Controls.AddRange(new Control[] { logoBox, brandSmall, brandBig });
#endif

        // ── mod pack card ──
        var card = new Panel { Dock = DockStyle.Top, Height = 116, BackColor = Theme.Panel, Padding = new Padding(16) };
        card.Paint += (_, e) =>
        {
            // freedomarrow.app card: thin outline and the red left edge of its section headings
            using var edge = new Pen(Theme.Border);
            e.Graphics.DrawRectangle(edge, 0, 0, card.Width - 1, card.Height - 1);
            using var strip = new SolidBrush(Theme.Accent);
            e.Graphics.FillRectangle(strip, 0, 0, Math.Max(3, card.LogicalToDeviceUnits(4)), card.Height);
        };
        var cardLabel = new Label { Text = T("MODPACK"), AutoSize = true, Location = new Point(119, 12), Font = Theme.Head(9.5f, semi: true), ForeColor = Theme.Accent, BackColor = Theme.Panel };
        _packPicture = new PictureBox { SizeMode = PictureBoxSizeMode.Zoom, Size = new Size(86, 86), Location = new Point(18, 15), BackColor = Theme.Panel };
        _packName = new Label { AutoSize = false, Location = new Point(118, 30), Size = new Size(370, 30), Font = Theme.Head(19f), ForeColor = Theme.Text, AutoEllipsis = true, BackColor = Theme.Panel };
        _packVersion = new Label { AutoSize = false, Location = new Point(119, 61), Size = new Size(370, 20), ForeColor = Theme.TextMuted, AutoEllipsis = true, BackColor = Theme.Panel, UseMnemonic = false };   // "Models & music": no & shortcut
        _modsState = new Label { AutoSize = false, Location = new Point(119, 81), Size = new Size(370, 20), ForeColor = Theme.TextMuted, BackColor = Theme.Panel };
        // Only shown before a modder has set the modpack up
        _setUp = Theme.MakeButton(T("Set up modpack (for modders)…"));
        _setUp.Location = new Point(119, 76);
        // Stable / Testing - only when the modder offers a testing channel
        _channels = new FlowLayoutPanel { Location = new Point(119, 78), Size = new Size(300, 32), WrapContents = false, BackColor = Theme.Panel, Visible = false };
        card.Controls.AddRange(new Control[] { cardLabel, _packPicture, _packName, _packVersion, _modsState, _setUp, _channels });

        // ── progress ──
        _panel = new LaunchProgressPanel { Dock = DockStyle.Top, Height = 146 };

        // ── buttons ──
        _play = Theme.MakeButton(T("PLAY"), ButtonKind.Primary);
        _play.AutoSize = false;
        _play.Dock = DockStyle.Top;
        _play.Height = 58;
        _play.Font = Theme.Head(22f);
        _play.Margin = new Padding(0);

        _vanilla = Theme.MakeButton(T("Play vanilla with no mods"));
        _vanilla.AutoSize = false;
        _vanilla.Dock = DockStyle.Top;
        _vanilla.Height = 40;

        // ── footer ──
        var footer = new Panel { Dock = DockStyle.Bottom, Height = 36, BackColor = Theme.Background };
        _settings = Theme.MakeButton("⚙   " + T("Settings"), ButtonKind.Ghost);
        _settings.Dock = DockStyle.Left;
        _settings.AutoSize = true;
        footer.Controls.Add(_settings);
        var help = Theme.MakeButton("🩺   " + T("Help me install"), ButtonKind.Ghost);
        help.Dock = DockStyle.Right;
        help.AutoSize = true;
        help.Click += (_, _) => CheckInstall();
        footer.Controls.Add(help);
        var decks = Theme.MakeButton("🗂   " + T("Deck backups"), ButtonKind.Ghost);
        decks.Dock = DockStyle.Left;
        decks.AutoSize = true;
        decks.Click += (_, _) => RestoreDecks();
        footer.Controls.Add(decks);
        if (LauncherService.HelperUrl is string helperUrl)
        {
            var ask = Theme.MakeButton("💬   " + T("Ask the AI helper"), ButtonKind.Ghost);
            ask.Dock = DockStyle.Right;
            ask.AutoSize = true;
            ask.Click += (_, _) =>
            {
                using var dlg = new HelperChatForm(helperUrl, InstallDoctor.Run(_gameDir).Report);
                dlg.ShowDialog(this);
            };
            footer.Controls.Add(ask);
        }

        // Docked top controls are added bottom-up
        body.Controls.Add(_vanilla);
        body.Controls.Add(Spacer(10));
        body.Controls.Add(_play);
        body.Controls.Add(Spacer(10));
        body.Controls.Add(_panel);
#if FA_DEV45
        // Linux / Steam Deck (Osama 22 Nov 2026: "on the launcher remind linux players to do the launch options")
        if (LinuxSteam.IsWine)
        {
            body.Controls.Add(Spacer(12));
            body.Controls.Add(LinuxStrip(out _linuxState));
            body.Controls.Add(Spacer(10));
        }
        else body.Controls.Add(Spacer(16));
#else
        body.Controls.Add(Spacer(16));
#endif
        body.Controls.Add(card);
        body.Controls.Add(Spacer(12));
        body.Controls.Add(footer);
#if FA_DEV45
        Controls.Add(body);
        Controls.Add(_news);
#endif
        Controls.Add(header);   // added last so it docks first: the art spans the full width
#if FA_DEV45
        _header = header;
#endif

        _play.Click += async (_, _) => await PlayModded();
        _vanilla.Click += (_, _) => PlayVanilla();
        _settings.Click += (_, _) => OpenSettings();
        _setUp.Click += async (_, _) => await SetUpModpack();

        // The modpack's .bamod dropped on the launcher (e.g. downloaded by hand) is installed; anything else is refused
        AllowDrop = true;
        DragEnter += (_, e) => e.Effect = !_busy && e.Data?.GetDataPresent(DataFormats.FileDrop) == true ? DragDropEffects.Copy : DragDropEffects.None;
        DragDrop += async (_, e) =>
        {
            if (e.Data?.GetData(DataFormats.FileDrop) is string[] files && files.Length > 0) await InstallPackFile(files[0]);
        };
        Shown += async (_, _) => await OnFirstShown();
#if FA_DEV45
        // ... and every 20 minutes while the launcher sits open and idle
        _updateCheck.Tick += async (_, _) => { if (!_busy && !_gameRunning && await UpdateLauncher(quiet: true)) _updateCheck.Stop(); };
        Shown += (_, _) => _updateCheck.Start();
        FormClosed += (_, _) => _updateCheck.Dispose();
#endif
        // Only look for the game while the launcher is the active window: a program that keeps checking
        // other processes in the background is one more thing antivirus behaviour monitors hold against it.
        _gameWatch.Tick += (_, _) => UpdateGameRunning();
        Activated += (_, _) => { UpdateGameRunning(); _gameWatch.Start(); };
        Deactivate += (_, _) => _gameWatch.Stop();
        FormClosed += (_, _) => _gameWatch.Dispose();
        FormClosing += (_, e) =>
        {
            if (_busy && e.CloseReason == CloseReason.UserClosing) e.Cancel = true;
        };
    }

    /// <summary>Linux reminder: the Steam launch options Freedom Arrow needs, with a button that copies them.</summary>
    private Control LinuxStrip(out Label state)
    {
        var strip = new Panel { Dock = DockStyle.Top, Height = 68, BackColor = Theme.Surface };
        strip.Paint += (_, e) =>
        {
            using var edge = new Pen(Theme.Border);
            e.Graphics.DrawRectangle(edge, 0, 0, strip.Width - 1, strip.Height - 1);
            using var bar = new SolidBrush(Theme.Warn);
            e.Graphics.FillRectangle(bar, 0, 0, Math.Max(3, strip.LogicalToDeviceUnits(4)), strip.Height);
        };
        var title = new Label { Text = T("LINUX / STEAM DECK"), AutoSize = true, Location = new Point(16, 7), Font = Theme.Head(10.5f, semi: true), ForeColor = Theme.Warn, BackColor = Theme.Surface };
        state = new Label { Text = T("Set Broken Arrow's Steam launch options before you play."), AutoSize = false, AutoEllipsis = true, Location = new Point(16, 24), Size = new Size(214, 40), ForeColor = Theme.Text, BackColor = Theme.Surface };
        var copy = Theme.MakeButton(T("Copy launch options"));
        copy.AutoSize = false;
        copy.Width = 180;
        copy.Dock = DockStyle.Right;
        strip.Padding = new Padding(0, 13, 10, 13);
        copy.Click += (_, _) => CopyLinuxLaunchOptions();
        strip.Controls.AddRange(new Control[] { title, state, copy });
        return strip;
    }

    /// <summary>The line PLAY would ask for: with the crash-fix helper when this PC needs it (see LinuxGcFixReady).</summary>
    private void CopyLinuxLaunchOptions()
    {
        var line = LinuxSteam.LaunchOption;
        var scope = LinuxGcFix.PtraceScope();
        if (scope is 1 or 2)
        {
            var appId = (_gameDir != null ? GameLocator.FindSteamAppId(_gameDir) : null) ?? ManagerConfig.SteamAppId;
            try { line = LinuxGcFix.LaunchLine(LinuxGcFix.Install(LinuxGcFix.Folder(LinuxSteam.SteamRoots().ToList(), appId) ?? throw new IOException("no Linux home folder"))); }
            catch (Exception ex) { Log(T("Linux crash fix not installed: {0}", ex.Message)); }
        }
        try { Clipboard.SetText(line); } catch { /* no clipboard */ }
        MessageBox.Show(this, T("Copied to the clipboard:\n\n{0}\n\nIn Steam: right-click Broken Arrow > Properties > General > Launch Options, replace the line with it, then press PLAY here.", line),
            T("Steam launch options"), MessageBoxButtons.OK, MessageBoxIcon.Information);
        UpdateLinuxState();
    }

    private void UpdateLinuxState()
    {
        if (_linuxState == null) return;
        var appId = (_gameDir != null ? GameLocator.FindSteamAppId(_gameDir) : null) ?? ManagerConfig.SteamAppId;
        var roots = LinuxSteam.SteamRoots().ToList();
        bool? set = LinuxSteam.HasLaunchOption(roots, appId);
        if (set == true && LinuxGcFix.PtraceScope() is 1 or 2) set = LinuxGcFix.Active(roots, appId);
        _linuxState.Text = set == true ? T("✓ Steam launch options are set.") : T("Set Broken Arrow's Steam launch options before you play.");
        _linuxState.ForeColor = set == true ? Theme.Good : Theme.Text;
    }

    private static Control Spacer(int height) => new Panel { Dock = DockStyle.Top, Height = height, BackColor = Theme.Background };

    protected override void OnLoad(EventArgs e)
    {
        base.OnLoad(e);
        ScaleForDpi();
        FitScreen();
    }

    /// <summary>
    /// 1.1.16 (Osama 22 Nov 2026, 4K under Proton): with Wine's DPI raised to the desktop scale (WineDpi), the fonts grew but the window and
    /// its panels stayed at 100 % sizes, so the text was cut off. When the layout was not scaled by WinForms, scale it here by DeviceDpi / 96
    /// (fonts are left alone: they already follow the DPI) and centre the window again.
    /// </summary>
    private static IEnumerable<Control> AllControls(Control root)
    {
        foreach (Control c in root.Controls) { yield return c; foreach (var d in AllControls(c)) yield return d; }
    }

    private void ScaleForDpi()
    {
        float f = DeviceDpi / 96f;
        if (f < 1.05f || _news == null || _news.Width >= LogicalToDeviceUnits(DesignNewsWidth) * 0.9f) return;
        // Windows (SteelPlate, Windows 11, 2560x1440, 22 Nov 2026) scales the window itself but not the panels in it: the News column stayed
        // 960 px in a 2160 px window and the 100 % rows cut their 150 % text. Then only the panels are scaled; under Wine, the whole form.
        bool windowScaled = ClientSize.Width >= LogicalToDeviceUnits(DesignWidth) * 0.9f;
        if (windowScaled) foreach (Control c in Controls) c.Scale(new SizeF(f, f));
        else Scale(new SizeF(f, f));
        // AutoSize buttons (the footer) kept a doubled or stale width: size them to their text at this DPI.
        foreach (var b in AllControls(this).OfType<Button>().Where(b => b.AutoSize).ToList())
        {
            b.AutoSize = false;
            b.Width = TextRenderer.MeasureText(b.Text, b.Font).Width + b.Padding.Horizontal + LogicalToDeviceUnits(8);
        }
        _placeHeaderButtons?.Invoke();
        PerformLayout();
        var area = Screen.FromControl(this).WorkingArea;
        StartPosition = FormStartPosition.Manual;
        Location = new Point(area.Left + Math.Max(0, (area.Width - Width) / 2), area.Top + Math.Max(0, (area.Height - Height) / 2));
        NetDiagnostics.Append($"{(windowScaled ? "Panels" : "Window")} scaled x{f:0.##} for {DeviceDpi} DPI: {ClientSize.Width}x{ClientSize.Height}");
    }

    /// <summary>The window taller than the screen (Steam Deck 1280x800): shrink the header art, never the controls.</summary>
    private const int DesignWidth = 1440, DesignHeight = 960, DesignHeaderHeight = 320, DesignNewsWidth = 960;

    private void FitScreen()
    {
        if (_header == null || _news == null) return;
        // Sizes as designed: Wine/Proton already clamps the window to the screen, so ClientSize may be smaller here.
        int want = LogicalToDeviceUnits(DesignHeight), header = LogicalToDeviceUnits(DesignHeaderHeight), minHeader = LogicalToDeviceUnits(190),
            minBody = LogicalToDeviceUnits(540), frameH = Height - ClientSize.Height, frameW = Width - ClientSize.Width;
        var area = Screen.FromControl(this).WorkingArea;
        // Wine/Proton: + room for a title bar it doesn't count
        var over = want + frameH + (LinuxSteam.IsWine ? LogicalToDeviceUnits(40) : 0) - area.Height;
        // Too wide (e.g. a 1366x768 laptop): the News column gets narrower, never below 520.
        var overW = LogicalToDeviceUnits(DesignWidth) + frameW - area.Width;
        int width = LogicalToDeviceUnits(DesignWidth);
        if (overW > 0)
        {
            var cutW = Math.Min(overW, LogicalToDeviceUnits(DesignNewsWidth - 520));
            _news.Width = LogicalToDeviceUnits(DesignNewsWidth) - cutW;
            width -= cutW;
        }
        if (over <= 0 && overW <= 0) return;
        if (over > 0)
        {
            // The News column gives up its extra height first, then the header art shrinks; the PLAY column never does.
            var headerCut = Math.Clamp(over - (want - header - minBody), 0, header - minHeader);
            _header.Height = header - headerCut;
            want = Math.Max(want - over, _header.Height + minBody);
        }
        ClientSize = new Size(width, want);
        StartPosition = FormStartPosition.Manual;
        Location = new Point(area.Left + Math.Max(0, (area.Width - Width) / 2), area.Top + Math.Max(0, (area.Height - Height) / 2));
    }

    protected override void OnHandleCreated(EventArgs e)
    {
        base.OnHandleCreated(e);
        Theme.UseDarkTitleBar(Handle);
    }

    // ───────────────────────── start-up ─────────────────────────

    private async Task OnFirstShown()
    {
        if (Environment.GetCommandLineArgs().Contains(PreviewArg)) { await ProgressPreview(); return; }
        if (_news != null) _ = _news.LoadAsync();   // in the background; PLAY never waits for it
        if (PinnedFreedomArrow.Enabled && await UpdateLauncher()) return;
        SetStatus(T("Looking for Broken Arrow…"));
        var saved = AppSettings.LoadGamePath();
        var steamFolder = _cfg.SteamFolderName;
        _gameDir = await Task.Run(() => saved != null && GameLocator.IsGameFolder(saved) ? saved : GameLocator.AutoDetect(steamFolder));
        if (_gameDir != null)
        {
            _gameDir = PathUtil.RealCase(_gameDir);
            AppSettings.SaveGamePath(_gameDir);
        }
        RefreshCard();
        SetStatus(_gameDir == null ? T("Broken Arrow wasn't found. Choose its folder in Settings.") : "");
        if (_gameDir != null && !GameLocator.IsGameRunning(_gameDir)) DeckNote(DeckGuard.AfterModdedSession(Log));

        // Double-clicked .bamod files (if the player turned that on in Settings)
        SingleInstance.StartServer(OnFilesFromExplorer);
        if (_startupFiles.Length > 0) await InstallPackFile(_startupFiles[0]);
    }

    /// <summary>1.1.9 (Lateralus 19 Nov 2026): replace this exe with the newer launcher named in the signed version list, then restart.
    /// Any failure keeps the current launcher and is shown; it never blocks PLAY.</summary>
    /// <param name="quiet">The 20-minute check: nothing on screen unless a new launcher is actually being installed.</param>
    private async Task<bool> UpdateLauncher(bool quiet = false)
    {
        var exe = Environment.ProcessPath;
        if (exe == null || !exe.EndsWith(".exe", StringComparison.OrdinalIgnoreCase)) return false;
        SelfUpdate.CleanUp(exe);
        try
        {
            if (!quiet) SetStatus(T("Checking for a launcher update…"));
            Directory.CreateDirectory(HostedDistribution.CacheRoot);
            using var cts = new CancellationTokenSource(TimeSpan.FromMinutes(5));
            var progress = new Progress<LaunchProgress>(ShowProgress);
            var (manifest, _) = await HostedDistribution.ReadManifestAsync(HostedDistribution.Client, SignedManifest.Url, HostedDistribution.ManifestFile, null, cts.Token);
            if (!await SelfUpdate.ApplyAsync(manifest.Launcher, exe, HostedDistribution.Client, progress, cts.Token)) { if (!quiet) { _panel.Finish(true, ""); SetStatus(""); } return false; }
            Log("Launcher updated to " + manifest.Launcher!.Version + ".");
            Process.Start(new ProcessStartInfo(exe, Loc.RestartArg) { UseShellExecute = false })?.Dispose();
            Close();
            return true;
        }
        catch (Exception ex)
        {
            Log("Launcher update skipped: " + ex.Message);
            if (quiet) return false;
            _panel.Finish(false, T("Launcher update skipped: {0}", ex.Message));
            SetStatus(T("Launcher update skipped: {0}", ex.Message));
            return false;
        }
    }

    private void OnFilesFromExplorer(string[] files)
    {
        if (IsDisposed || files.Length == 0) return;
        try
        {
            BeginInvoke(new Action(async () =>
            {
                if (WindowState == FormWindowState.Minimized) WindowState = FormWindowState.Normal;
                Activate();
                await InstallPackFile(files[0]);
            }));
        }
        catch (InvalidOperationException) { /* closing */ }
    }

    /// <summary>
    /// Linux: Steam starts the game, and only loads MelonLoader's version.dll with this launch option.
    /// We read Steam's settings but never write them (Steam overwrites them while it runs).
    /// </summary>
    private bool LinuxLaunchOptionSet(string dir)
    {
        var ok = LinuxSteam.HasLaunchOption(LinuxSteam.SteamRoots(), GameLocator.FindSteamAppId(dir) ?? ManagerConfig.SteamAppId);
        if (ok != false)
        {
            if (ok == null) Log(T("Couldn't read Steam's launch options; make sure Broken Arrow has: ") + LinuxSteam.LaunchOption);
            return true;
        }
        try { Clipboard.SetText(LinuxSteam.LaunchOption); } catch { /* no clipboard */ }
        var msg = T("Linux: Broken Arrow needs this Steam launch option to load mods (copied to the clipboard):\n\n{0}\n\nIn Steam: right-click Broken Arrow > Properties > General > Launch Options, paste it, then press PLAY again.", LinuxSteam.LaunchOption);
        SetStatus(T("Set Broken Arrow's Steam launch option first."));
        MessageBox.Show(this, msg, T("Steam launch option"), MessageBoxButtons.OK, MessageBoxIcon.Information);
        return false;
    }

    private bool _gcFixAsked;
    /// <summary>
    /// Linux crash fix (Core/LinuxGcFix): needed only when kernel.yama.ptrace_scope is 1 or 2. Puts fa_ptracer.so in place, then
    /// asks once per session for the launch line (copied to the clipboard). Never blocks PLAY when something can't be read.
    /// </summary>
    private bool LinuxGcFixReady(string dir)
    {
        var scope = LinuxGcFix.PtraceScope();
        if (scope is null or 0) return true;
        if (scope == 3) { Log(T("Linux: kernel.yama.ptrace_scope is 3, so the \"Fatal error in GC\" crash fix cannot work on this PC.")); return true; }
        var appId = GameLocator.FindSteamAppId(dir) ?? ManagerConfig.SteamAppId;
        var roots = LinuxSteam.SteamRoots().ToList();
        string unix;
        try { unix = LinuxGcFix.Install(LinuxGcFix.Folder(roots, appId) ?? throw new IOException("no Linux home folder")); }
        catch (Exception ex) { Log(T("Linux crash fix not installed: {0}", ex.Message)); return true; }
        if (LinuxGcFix.Active(roots, appId) != false) { Log(T("Linux crash fix: active.")); return true; }
        if (_gcFixAsked) return true;
        _gcFixAsked = true;
        var line = LinuxGcFix.LaunchLine(unix);
        try { Clipboard.SetText(line); } catch { /* no clipboard */ }
        var msg = T("Linux: Proton can crash Broken Arrow with \"Fatal error in GC\". The launcher installed a small fix; it needs this Steam launch option (copied to the clipboard):\n\n{0}\n\nIn Steam: right-click Broken Arrow > Properties > General > Launch Options, replace the line with it, then press PLAY again.\n\nIt only lets Proton inspect Broken Arrow while the game runs; no system setting changes. Press Cancel to play without it this time.", line);
        if (MessageBox.Show(this, msg, T("Linux crash fix"), MessageBoxButtons.OKCancel, MessageBoxIcon.Information) != DialogResult.OK) return true;
        SetStatus(T("Set Broken Arrow's Steam launch option first."));
        return false;
    }

    private void RefreshCard()
    {
        DeckGuard.GameDir = _gameDir;
        try { UpdateLinuxState(); } catch { /* Steam's files unreadable: keep the reminder */ }
        Manifest? manifest = null;
        InstalledPackage? pack = null;
        string? preview = null;
        bool on = false;
        if (_gameDir != null)
        {
            try
            {
                manifest = Manifest.Load(_gameDir);
                pack = _launcher.FindPack(manifest);
                if (pack != null) preview = _launcher.FindPackPreview(_gameDir, manifest, pack);
            }
            catch { /* shown as not installed */ }
            on = _launcher.ModsOn(_gameDir);
        }

        var old = _packPicture.Image;
        _packPicture.Image = LoadPicture(preview);
        if (old != null && old != _logo) old.Dispose();

        if (pack != null)
        {
            _packName.Text = pack.Info?.Name ?? pack.Name;
            var version = pack.Info?.Version;
            _packVersion.Text = version != null ? "v" + version.TrimStart('v', 'V') : "";
        }
        else if (LauncherService.ActiveRepo() is { } repo)
        {
            _packName.Text = repo.Split('/')[1];
            _packVersion.Text = T("Downloaded when you press PLAY");
        }
        if (PinnedFreedomArrow.Enabled)
        {
            _packName.Text = "Freedom Arrow";
            // Lateralus 14 Nov 2026: show the installed mod and launcher versions.
            var assets = manifest?.Packages.FirstOrDefault(p => p.Info?.Id == PinnedFreedomArrow.AssetsId)?.Info?.Version;
            _packVersion.Text = pack?.Info?.Version is string installed
                ? T("Mod {0}", installed) + (assets != null ? "  ·  " + T("Models & music {0}", assets) : "")
                : T("Downloads all mod content on PLAY");
        }
        if (!PinnedFreedomArrow.Enabled && pack != null && LauncherService.InstalledFromOtherRepo())
            _packVersion.Text = T("{0}: installed on next PLAY", T(LauncherService.ActiveChannel));
        else if (pack != null && LauncherService.Channels.Count > 1)
            _packVersion.Text += "  ·  " + T(LauncherService.ActiveChannel);
        else if (!PinnedFreedomArrow.Enabled && pack == null && LauncherService.ActiveRepo() == null)
        {
            _packName.Text = T("No modpack set up");
            _packVersion.Text = T("Only MelonLoader is installed");
        }
        _setUp.Visible = LauncherService.ConfiguredRepo == null;
        _modsState.Visible = !_setUp.Visible;   // same spot in the card
        RefreshChannels();

        _modsState.ForeColor = on ? Theme.Good : Theme.TextMuted;
        _modsState.Text = PinnedFreedomArrow.Enabled ? T("Launcher {0}", typeof(LauncherForm).Assembly.GetName().Version?.ToString(3) ?? "?") : on
            ? "●  " + T("Mods are on")
            : "○  " + T("Mods are off - the game starts normally with Anti-Cheat");
    }

    private void RefreshChannels()
    {
        var channels = LauncherService.Channels;
        _channels.Visible = channels.Count > 1;
        if (!_channels.Visible) return;
        var active = LauncherService.ActiveChannel;
        foreach (Control c in _channels.Controls) c.Dispose();
        _channels.Controls.Clear();
        foreach (var (name, _) in channels)
        {
            var b = Theme.MakeButton(T(name), name == active ? ButtonKind.Primary : ButtonKind.Secondary);
            b.MinimumSize = new Size(0, 30);
            b.AutoSizeMode = AutoSizeMode.GrowAndShrink;   // MakeButton's default height (34) doesn't fit the card
            b.Padding = new Padding(10, 0, 10, 0);
            b.Margin = new Padding(0, 0, 6, 0);
            b.Font = Theme.Ui(9f);
            b.Enabled = !_busy && !_gameRunning;
            var channel = name;
            b.Click += (_, _) => SwitchChannel(channel);
            _channels.Controls.Add(b);
        }
    }

    private void SwitchChannel(string channel)
    {
        if (_busy || _gameRunning || channel == LauncherService.ActiveChannel) return;
        if (channel == LauncherService.Testing &&
            MessageBox.Show(this,
                T("Testing has the newest changes before they come to Stable. It can have bugs.\n\nSwitch to Testing?"),
                T("Testing"), MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
            return;
        LauncherService.SetChannel(channel);
        Log(T("Switched to {0}.", T(channel)));
        RefreshCard();
        SetStatus(LauncherService.InstalledFromOtherRepo() || _gameDir == null
            ? T("Switched to {0}. Press PLAY to download it.", T(channel))
            : T("Switched to {0}.", T(channel)));
    }

    private Image? LoadPicture(string? path)
    {
        try
        {
            if (path != null && File.Exists(path))
            {
                using var tmp = Image.FromFile(path);
                return new Bitmap(tmp);
            }
        }
        catch { /* fall back to the default picture */ }
        return MainForm.LoadEmbeddedImage("Assets.default_preview.png");
    }

    // ───────────────────────── PLAY ─────────────────────────

    private bool CheckGame()
    {
        if (_gameDir == null || !GameLocator.IsGameFolder(_gameDir))
        {
            SetStatus(T("Broken Arrow wasn't found. Choose its folder in Settings."));
            OpenSettings();
            return false;
        }
        if (GameLocator.IsGameRunning(_gameDir))
        {
            SetStatus(T("{0} is already running.", _cfg.GameName));
            return false;
        }
        return true;
    }

    private async Task PlayModded()
    {
        if (_busy || !CheckGame()) return;
        // Osama 22 Nov 2026: "the launcher should detect a new launcher version". It checked only at start; a launcher left open
        // for hours missed a release. Check again here: a newer signed launcher is installed and this window restarts.
        if (PinnedFreedomArrow.Enabled && await UpdateLauncher()) return;
        var dir = _gameDir!;

        if (!LauncherService.EnsureSteam())
        {
            SetStatus(T("Steam is starting - press PLAY again once it's open."));
            return;
        }

        if (LinuxSteam.IsWine && !LinuxLaunchOptionSet(dir)) return;
        if (LinuxSteam.IsWine && !LinuxGcFixReady(dir)) return;
        DeckNote(DeckGuard.BeforeLaunch(true, Log));
        SetBusy(true);
        _panel.Begin(LaunchStage.Mod, T("Getting ready…"));
        try
        {
            var progress = new Progress<LaunchProgress>(ShowProgress);
            await _launcher.PrepareModsAsync(dir, progress, Log, CancellationToken.None);
            RefreshCard();

            ShowProgress(new LaunchProgress(T("Starting {0}…", _cfg.GameName), Stage: LaunchStage.Start));
            var game = _launcher.StartModded(dir);
            _gameRunning = false;
            _panel.Finish(true, game != null ? T("{0} is starting.", _cfg.GameName) : T("Steam is starting {0}: choose \"Play Anti-Cheat Disabled\".", _cfg.GameName));
            if (game != null) ShowLoadingScreen(game, dir);
        }
        catch (Exception ex)
        {
            // 1.1.16: show the whole reason, not just "see inner exception"; for a secure-connection failure also show what
            // this PC receives from freedomarrow.app (NetDiagnostics), and keep it all in launcher.log.
            var reason = NetDiagnostics.Describe(ex);
            NetDiagnostics.Append($"{AppInfo.FullName}: PLAY failed: {ex}");
            Log(reason);
            _panel.Finish(false, T("Couldn't start the game: ") + reason);
            SetStatus(T("Couldn't start the game: ") + reason);
            var details = reason;
            if (NetDiagnostics.IsSecureConnectionFailure(ex))
            {
                var probe = await NetDiagnostics.ProbeAsync();
                NetDiagnostics.Append("Connection check:" + Environment.NewLine + probe);
                details += Environment.NewLine + Environment.NewLine + probe;
            }
            details += Environment.NewLine + Environment.NewLine + T("Details are saved in {0}", NetDiagnostics.LogPath);
            MessageBox.Show(this, details, T("Couldn't start the game"), MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        finally
        {
            SetBusy(false);
        }
    }

    private void ShowLoadingScreen(Process game, string dir)
    {
        var screen = new GameLoadingScreen(game, dir, _logo, _icon);
        screen.FormClosed += (_, _) =>
        {
            var failure = screen.Failure;
            screen.Dispose();
            game.Dispose();
            if (failure == null)
            {
                SetStatus(T("Have fun!"));
                return;
            }
            WindowState = FormWindowState.Normal;
            Activate();
            SetStatus(failure);
            var log = Path.Combine(dir, "MelonLoader", "Latest.log");
            if (MessageBox.Show(this, failure + "\n\n" + T("Open MelonLoader's log to see what went wrong?"), Text,
                    MessageBoxButtons.YesNo, MessageBoxIcon.Warning) == DialogResult.Yes && File.Exists(log))
            {
                try { Process.Start(new ProcessStartInfo(log) { UseShellExecute = true })?.Dispose(); }
                catch { /* no viewer */ }
            }
        };
        WindowState = FormWindowState.Minimized;
        screen.Show();
    }

    // ───────────────────────── turn off mods ─────────────────────────

    private void PlayVanilla()
    {
        if (_busy || !CheckGame()) return;
        var dir = _gameDir!;
        DeckNote(DeckGuard.BeforeLaunch(false, Log));
        try
        {
            _launcher.TurnOffMods(dir, Log);
            RefreshCard();
            if (!LauncherService.EnsureSteam())
            {
                SetStatus(T("Mods are off. Steam is starting - press the button again once it's open."));
                return;
            }
            _launcher.StartVanilla(dir);
            SetStatus(LinuxSteam.IsWine ? T("Mods are off. Steam is starting {0}: choose \"Play\".", _cfg.GameName)
                                        : T("Mods are off. Starting {0} with Anti-Cheat…", _cfg.GameName));
            _play.Enabled = _vanilla.Enabled = false;   // until the game window closes again (checked every second)
        }
        catch (Exception ex)
        {
            Log(ex.Message);
            SetStatus(ex.Message);
            MessageBox.Show(this, T("Windows didn't allow changing a file:\n\n{0}\n\nMake sure the game is closed. If the game is in Program Files, run the mod manager as administrator.", ex.Message),
                Text, MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    // ───────────────────────── modpack file / setup ─────────────────────────

    /// <summary>The modpack's own .bamod (dropped or double-clicked) is installed; other mods are turned away.</summary>
    private async Task InstallPackFile(string path)
    {
        if (_busy || !CheckGame()) return;
        var dir = _gameDir!;
        SetBusy(true);
        bool accepted = false;
        try
        {
            _panel.Begin(LaunchStage.Mod, T("Installing the mod pack…"));
            accepted = await Task.Run(() => _launcher.InstallPackFile(dir, path, Log));
            _panel.Finish(accepted, accepted ? T("Installed {0}.", Path.GetFileName(path)) : "");
        }
        catch (Exception ex)
        {
            Log(ex.Message);
            _panel.Finish(false, ex.Message);
            SetStatus(ex.Message);
            MessageBox.Show(this, ex.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        finally
        {
            SetBusy(false);
            RefreshCard();
        }

        if (!accepted)
        {
            var pack = LauncherService.ActiveRepo()?.Split('/')[1] ?? T("its modpack");
            MessageBox.Show(this,
                T("This launcher is set up for {0} only. To install other mods, use Broken Arrow Mod Manager.", pack),
                Text, MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
    }

    /// <summary>For modders: link this copy of the launcher to their modpack's GitHub repo.</summary>
    private async Task SetUpModpack()
    {
        if (_busy) return;
        using var dlg = new ModpackSetupForm();
        if (dlg.ShowDialog(this) != DialogResult.OK) return;

        SetBusy(true);
        try
        {
            SetStatus(T("Checking {0}…", dlg.Link));
            var repo = await _launcher.SetUpModpackAsync(dlg.Link, dlg.TestingLink, CancellationToken.None);
            RefreshCard();
            SetStatus(T("Set up for {0}.", repo));
            if (MessageBox.Show(this,
                    T("This launcher is now set up for {0}.\n\nShare these two files with your players:\n•  {1}\n•  launcher.json\n\nPlayers can't change the modpack. To change it yourself, delete launcher.json.\n\nOpen the folder now?",
                        repo, Path.GetFileName(Environment.ProcessPath ?? "BAModLauncher.exe")),
                    Text, MessageBoxButtons.YesNo, MessageBoxIcon.Information) == DialogResult.Yes)
            {
                try { Process.Start(new ProcessStartInfo("explorer.exe", $"/select,\"{LauncherService.ConfigFile}\"") { UseShellExecute = true })?.Dispose(); }
                catch { /* ignore */ }
            }
        }
        catch (Exception ex)
        {
            Log(ex.Message);
            SetStatus(ex.Message);
            MessageBox.Show(this, ex.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        finally
        {
            SetBusy(false);
        }
    }

    // ───────────────────────── help me install ─────────────────────────

    /// <summary>Optional, read-only: checks the game folder and explains what to fix. Nothing is changed or sent.</summary>
    private void CheckInstall()
    {
        var (findings, report) = InstallDoctor.Run(_gameDir);
        var sb = new System.Text.StringBuilder();
        sb.AppendLine(T("This check only reads files in the Broken Arrow folder. It changes nothing and sends nothing."));
        sb.AppendLine();
        foreach (var f in findings)
        {
            sb.AppendLine((f.Ok ? "✔  " : "✖  ") + f.Title);
            if (!f.Ok && f.Fix.Length > 0) sb.AppendLine("      " + T("Fix:") + " " + f.Fix);
            sb.AppendLine();
        }
        bool copied = false;
        try { Clipboard.SetText(report); copied = true; } catch (System.Runtime.InteropServices.ExternalException) { }
        sb.AppendLine(copied
            ? T("Still stuck? The report below is copied. Paste it in the Freedom Arrow Discord and we'll help.")
            : T("Still stuck? Copy the report below and paste it in the Freedom Arrow Discord and we'll help."));
        sb.AppendLine();
        sb.Append(report);
        using var dlg = new ReadmeForm(T("Help me install"), sb.ToString());
        dlg.ShowDialog(this);
    }

    // ───────────────────────── settings ─────────────────────────

    private void OpenSettings()
    {
        if (_busy) return;
        using var dlg = new LauncherSettingsForm(_cfg, _gameDir, _log, _icon);
        dlg.ShowDialog(this);
        if (dlg.ExitApp)
        {
            Close();
            return;
        }
        if (dlg.GameDir != null) _gameDir = dlg.GameDir;
        RefreshCard();
        if (_gameDir != null && _statusText.StartsWith(T("Broken Arrow wasn't found."), StringComparison.Ordinal)) SetStatus("");
        UpdateGameRunning();
    }

    /// <summary>The buttons can't be used while Broken Arrow is open.</summary>
    private void UpdateGameRunning()
    {
        bool running = _gameDir != null && GameLocator.IsGameRunning(_gameDir);
        if (running == _gameRunning) return;
        _gameRunning = running;
        if (!running) DeckNote(DeckGuard.AfterModdedSession(Log));
        _play.Text = running ? T("GAME IS RUNNING") : "▶   " + T("PLAY");
        if (running) SetStatus(T("{0} is running. Close the game to use these buttons again.", _cfg.GameName));
        else if (!_busy) SetStatus("");
        ApplyEnabled();
    }

    private void DeckNote(string? message)
    {
        if (message == null) return;
        SetStatus(message);
        MessageBox.Show(this, message, T("Decks"), MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    /// <summary>Puts a deck backup back: vanilla-*.zip into Decks, mod-*.zip into Decks\FreedomArrow.</summary>
    private void RestoreDecks()
    {
        if (_busy || !CheckGame()) return;
        Directory.CreateDirectory(DeckGuard.BackupDir);
        using var dlg = new OpenFileDialog { InitialDirectory = DeckGuard.BackupDir, Filter = T("Deck backups") + " (*.zip)|*.zip", Title = T("Choose a deck backup to put back") };
        if (dlg.ShowDialog(this) != DialogResult.OK) return;
        if (MessageBox.Show(this, T("Put the decks in {0} back? Decks with the same name are replaced; the current decks are backed up first.", Path.GetFileName(dlg.FileName)), T("Decks"),
                MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        try { SetStatus(T("{0} decks put back.", DeckGuard.Restore(dlg.FileName, Log))); }
        catch (Exception ex) { Log(ex.Message); SetStatus(ex.Message); }
    }

    private void ApplyEnabled()
    {
        _play.Enabled = _vanilla.Enabled = !_busy && !_gameRunning;
        _settings.Enabled = _setUp.Enabled = !_busy;
        if (_lang != null) _lang.Enabled = !_busy;
        foreach (Control c in _channels.Controls) c.Enabled = !_busy && !_gameRunning;
    }

    // ───────────────────────── helpers ─────────────────────────

    private void SetBusy(bool busy)
    {
        _busy = busy;
        ApplyEnabled();
        UseWaitCursor = busy;
        if (!busy) Text = AppInfo.FullName;
    }

    /// <summary>
    /// "FreedomArrow.exe --progress-preview": plays a made-up PLAY run on the progress panel (download, a 25 s stall, a retry,
    /// checks, start) so the look can be checked without a game. Touches no files and no network.
    /// </summary>
    private const string PreviewArg = "--progress-preview";
    private async Task ProgressPreview()
    {
        RefreshCard();
        SetBusy(true);
        const long mb = 1048576;
        async Task Download(string text, LaunchStage stage, long from, long to, long total, double mbPerSecond, string? note = null)
        {
            for (long done = from; ; done = Math.Min(to, done + (long)(mbPerSecond * mb / 4)))
            {
                ShowProgress(new LaunchProgress(text, (double)done / total, stage, done, total, done == from ? note : null));
                if (done >= to) return;
                await Task.Delay(250);
            }
        }
        _panel.Begin(LaunchStage.Mod, T("Getting ready…"));
        ShowProgress(new LaunchProgress(T("Checking the Freedom Arrow version list…"), Stage: LaunchStage.Mod));
        await Task.Delay(1500);
        await Download(T("Downloading {0}", "FreedomArrow-0.9.4.bamod"), LaunchStage.Mod, 0, 104 * mb, 104 * mb, 16);
        ShowProgress(new LaunchProgress(T("Checking MelonLoader…"), Stage: LaunchStage.Loader));
        await Task.Delay(1500);
        for (int f = 0; f <= 10995; f += 700)
        {
            ShowProgress(new LaunchProgress(T("Checking models and music… {0} / {1} files", f, 10995), f / 10995.0, LaunchStage.Assets));
            await Task.Delay(250);
        }
        string files = T("Downloading models and music… {0} / {1} files", 37, 126);
        await Download(files, LaunchStage.Assets, 0, 410 * mb, 1520 * mb, 24);
        await Task.Delay(26000);   // no data: the live line turns amber
        await Download(T("Downloading models and music… {0} / {1} files", 38, 126), LaunchStage.Assets, 410 * mb, 1520 * mb, 1520 * mb, 90,
            T("A file download was interrupted ({0}). Trying again ({1} of {2})…", T("no data for {0} s", 60), 2, 6));
        ShowProgress(new LaunchProgress(T("Checking mod files…"), Stage: LaunchStage.Verify));
        await Task.Delay(3000);
        ShowProgress(new LaunchProgress(T("Starting {0}…", _cfg.GameName), Stage: LaunchStage.Start));
        await Task.Delay(2000);
        _panel.Finish(true, T("Preview finished: nothing was installed or started."));
        SetBusy(false);
    }

    /// <summary>One click between 中文 and English: saves the choice and restarts the launcher (as Settings > Language does).</summary>
    private void ToggleChinese()
    {
        if (_busy) return;
        var data = AppSettings.Load();
        data.Language = Loc.IsChinese ? "en" : "zh";
        if (!AppSettings.Save(data)) return;
        try
        {
            Process.Start(new ProcessStartInfo(Environment.ProcessPath!, Loc.RestartArg) { UseShellExecute = false })?.Dispose();
            Close();
        }
        catch (Exception ex) { SetStatus(T("Couldn't restart: ") + ex.Message); }
    }

    private string _statusText = "";
    private void SetStatus(string text)
    {
        _statusText = text;
        _panel.SetMessage(text);
    }

    /// <summary>One PLAY progress report: the panel, and the percentage in the window title (visible on the taskbar).</summary>
    private void ShowProgress(LaunchProgress p)
    {
        _panel.Report(p);
        Text = _panel.Percent is int pct ? $"{pct}% · {AppInfo.FullName}" : AppInfo.FullName;
    }

    private void Log(string message)
    {
        _log.Add($"[{DateTime.Now:HH:mm:ss}] {message}");
        Debug.WriteLine(message);
        NetDiagnostics.Append(message);
    }
}
