using System.Runtime.InteropServices;
using BAModManager.Core;
using static BAModManager.Core.Loc;

namespace BAModManager.Ui;

/// <summary>
/// 1.1.15 (Osama 22 Nov 2026, "can we add a news section on the launcher? like the battle stats and patch notes?"):
/// the right-hand column of the Freedom Arrow launcher. Battlefield report numbers from freedomarrow.app and the short
/// release announcements (中文 when the launcher is in Chinese), with a link to the full notes on the site. See LauncherNews.
/// </summary>
internal sealed class NewsPanel : Panel
{
    private readonly StatTiles _tiles = new() { Dock = DockStyle.Top, Height = 78 };
    private readonly RichTextBox _notes;
    private readonly Button _more;
    private string _link = LauncherNews.Site;
    // NEW FEATURES / PATCH NOTES tabs (Osama 22 Nov 2026: "add the gif with changing the paint scheme in the launcher under a
    // new feature category")
    private readonly Tab _featuresTab, _notesTab;
    private readonly Panel _feature;
    private readonly Label _featureTitle, _featureText;
    private readonly PictureBox _featureImage;
    private MemoryStream? _imageData;   // an animated GIF needs its stream for as long as it plays

    public NewsPanel()
    {
        BackColor = Theme.Panel;
        Padding = new Padding(24, 18, 24, 16);
        _notes = new RichTextBox
        {
            Dock = DockStyle.Fill,
            ReadOnly = true,
            BorderStyle = BorderStyle.None,
            BackColor = Theme.Panel,
            ForeColor = Theme.Text,
            DetectUrls = false,
            ScrollBars = RichTextBoxScrollBars.Vertical,
            Font = Body(),
            TabStop = false,
            Cursor = Cursors.Default,
            ShortcutsEnabled = false,
        };
        // Windows 10/11 dark scroll bar, like the rest of the launcher (ignored where the theme doesn't exist)
        _notes.HandleCreated += (_, _) => { try { SetWindowTheme(_notes.Handle, "DarkMode_Explorer", null); } catch (Exception) { } };
        _more = Theme.MakeButton(T("Full patch notes and statistics →"), ButtonKind.Ghost);
        _more.Dock = DockStyle.Bottom;
        _more.AutoSize = false;
        _more.Height = 34;
        _more.Click += (_, _) => LauncherNews.Open(_link);
        // Osama 22 Nov 2026: "make sure there's a big button to visit our website"
        var site = Theme.MakeButton(T("VISIT FREEDOMARROW.APP"), ButtonKind.Secondary);
        site.Dock = DockStyle.Bottom;
        site.AutoSize = false;
        site.Height = 52;
        site.Font = Theme.Head(18f);
        site.Click += (_, _) => LauncherNews.Open(LauncherNews.Site);

        _featureTitle = new Label { Dock = DockStyle.Top, Height = 28, Font = Theme.Head(15f), ForeColor = Theme.Text, BackColor = Theme.Panel, UseMnemonic = false };
        _featureText = new Label { Dock = DockStyle.Top, Height = 44, ForeColor = Theme.TextMuted, BackColor = Theme.Panel, UseMnemonic = false };
        _featureImage = new PictureBox { Dock = DockStyle.Fill, SizeMode = PictureBoxSizeMode.Zoom, BackColor = Theme.Panel, Cursor = Cursors.Hand };
        _featureImage.Click += (_, _) => LauncherNews.Open(LauncherNews.Site);
        _feature = new Panel { Dock = DockStyle.Fill, BackColor = Theme.Panel, Visible = false };
        _feature.Controls.Add(_featureImage);
        _feature.Controls.Add(Gap(4));
        _feature.Controls.Add(_featureText);
        _feature.Controls.Add(_featureTitle);
        var content = new Panel { Dock = DockStyle.Fill, BackColor = Theme.Panel };
        content.Controls.Add(_notes);
        content.Controls.Add(_feature);
        _featuresTab = new Tab(T("NEW FEATURES")) { Visible = false };
        _notesTab = new Tab(T("PATCH NOTES")) { Selected = true };
        _featuresTab.Click += (_, _) => ShowTab(features: true);
        _notesTab.Click += (_, _) => ShowTab(features: false);
        var tabs = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 34, BackColor = Theme.Panel, WrapContents = false, Margin = Padding.Empty };
        tabs.Controls.Add(_featuresTab);
        tabs.Controls.Add(_notesTab);

        // Docked top controls are added bottom-up
        Controls.Add(content);
        Controls.Add(Gap(6));
        Controls.Add(tabs);
        Controls.Add(Gap(14));
        Controls.Add(_tiles);
        Controls.Add(Title(T("BATTLEFIELD REPORT")));
        Controls.Add(_more);
        Controls.Add(Gap(6, DockStyle.Bottom));
        Controls.Add(site);   // added last: the very bottom of the column
        ShowText(T("Loading news…"));
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        // the site's card edge on the left, against the launcher column
        using var edge = new SolidBrush(Theme.Border);
        e.Graphics.FillRectangle(edge, 0, 0, Math.Max(1, LogicalToDeviceUnits(1)), Height);
    }

    public async Task LoadAsync()
    {
        var news = await LauncherNews.LoadAsync();
        if (IsDisposed) return;
        if (news == null) { ShowText(T("News is unavailable right now. It doesn't affect PLAY.")); return; }
        _tiles.Set(news.Stats);
        if (news.Notes.Count > 0) _link = news.Notes[0].Link;
        Render(news.Notes);
        if (news.Features.Count > 0) await ShowFeature(news.Features[0]);
    }

    /// <summary>The newest feature, shown first: title, a line of text and its animated picture.</summary>
    private async Task ShowFeature(LauncherNews.Feature f)
    {
        _featureTitle.Text = Loc.IsChinese && f.TitleZh.Length > 0 ? f.TitleZh : f.Title;
        _featureText.Text = Loc.IsChinese && f.TextZh.Length > 0 ? f.TextZh : f.Text;
        _featuresTab.Visible = true;
        ShowTab(features: true);
        if (f.Image.Length == 0) return;
        var bytes = await LauncherNews.LoadImageAsync(f.Image);
        if (bytes == null || IsDisposed) return;
        try
        {
            _imageData = new MemoryStream(bytes);
            _featureImage.Image = Image.FromStream(_imageData);   // PictureBox plays an animated GIF by itself
        }
        catch (Exception) { _imageData = null; }
    }

    private void ShowTab(bool features)
    {
        _feature.Visible = features;
        _notes.Visible = !features;
        _featuresTab.Selected = features;
        _notesTab.Selected = !features;
        _more.Visible = !features;   // the patch-notes link; the feature picture gets its room
    }

    private void ShowText(string text)
    {
        _notes.Clear();
        Append(text, Body(), Theme.TextMuted);
    }

    private void Render(IReadOnlyList<LauncherNews.Note> notes)
    {
        _notes.SuspendLayout();
        _notes.Clear();
        bool first = true;
        foreach (var n in notes)
        {
            var text = Loc.IsChinese && n.Chinese.Length > 0 ? n.Chinese : n.English;
            if (!first) Append("\n\n", Body(), Theme.Text);
            first = false;
            Append("Freedom Arrow " + n.Version, VersionFont, Theme.Text);
            if (n.Date.Length > 0) Append("   " + Date(n.Date), DateFont, Theme.TextMuted);
            Append("\n", Body(), Theme.Text);
            foreach (var raw in text.Replace("\r", "").Split('\n'))
            {
                var line = raw.TrimEnd();
                if (line.Length == 0 || line.Trim() == "---") continue;
                if (line.StartsWith("#"))
                {
                    Append("\n" + Heading(line) + "\n", SectionFont, Theme.Accent);
                    continue;
                }
                int indent = line.Length - line.TrimStart().Length;
                var body = line.TrimStart();
                string lead = "";
                if (body.StartsWith("- ") || body.StartsWith("* "))
                {
                    body = body[2..];
                    lead = indent >= 2 ? "      ◦  " : "•  ";
                }
                Append(lead, Body(), indent >= 2 ? Theme.TextMuted : Theme.Accent);
                Inline(body, indent >= 2 ? Theme.TextMuted : Theme.Text);
                Append("\n", Body(), Theme.Text);
            }
        }
        _notes.SelectionStart = 0;
        _notes.ScrollToCaret();
        _notes.ResumeLayout();
    }

    /// <summary>**bold** runs; every other character is shown as it is.</summary>
    private void Inline(string text, Color color)
    {
        var parts = text.Split("**");
        for (int i = 0; i < parts.Length; i++)
            if (parts[i].Length > 0) Append(parts[i], i % 2 == 1 ? BoldFont : Body(), i % 2 == 1 ? Theme.Text : color);
    }

    /// <summary>"## ⚔️ Combat" -> "Combat": the emoji in front of a heading don't render in every Windows font.</summary>
    private static string Heading(string line)
    {
        var t = line.TrimStart('#', ' ');
        int i = 0;
        while (i < t.Length && !char.IsLetterOrDigit(t[i])) i++;
        return i < t.Length ? t[i..] : t;
    }

    /// <summary>"21 November 2026" -> "2026 年 11 月 21 日" in Chinese.</summary>
    private static string Date(string date) =>
        Loc.IsChinese && DateTime.TryParseExact(date, "d MMMM yyyy", System.Globalization.CultureInfo.InvariantCulture, System.Globalization.DateTimeStyles.None, out var d)
            ? $"{d.Year} 年 {d.Month} 月 {d.Day} 日" : date;

    [DllImport("uxtheme.dll", CharSet = CharSet.Unicode)]
    private static extern int SetWindowTheme(IntPtr hwnd, string? appName, string? idList);

    private void Append(string text, Font font, Color color)
    {
        _notes.SelectionStart = _notes.TextLength;
        _notes.SelectionLength = 0;
        _notes.SelectionFont = font;
        _notes.SelectionColor = color;
        _notes.AppendText(text);
    }

    // One set of fonts for the whole text (the RichTextBox copies them into its runs)
    private static readonly Font BodyFont = Theme.Ui(9.75f), BoldFont = Theme.Semibold(9.75f), DateFont = Theme.Ui(9f),
        VersionFont = Theme.Head(17f), SectionFont = Theme.Head(12.5f, semi: true);

    private static Font Body() => BodyFont;

    private static Control Gap(int h, DockStyle dock = DockStyle.Top) => new Panel { Dock = dock, Height = h, BackColor = Theme.Panel };

    private static Control Title(string text) => new Label
    {
        Text = text,
        Dock = DockStyle.Top,
        Height = 30,
        Font = Theme.Head(13f),
        ForeColor = Theme.Text,
        BackColor = Theme.Panel,
        TextAlign = ContentAlignment.TopLeft,
        UseMnemonic = false,
    };

    /// <summary>A heading that works as a tab: white with the red line under it when selected, grey otherwise.</summary>
    private sealed class Tab : Control
    {
        private bool _selected;
        public bool Selected { get => _selected; set { _selected = value; Invalidate(); } }

        public Tab(string text)
        {
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
            Text = text;
            Font = Theme.Head(13f);
            BackColor = Theme.Panel;
            Cursor = Cursors.Hand;
            Margin = new Padding(0, 0, 22, 0);
            Height = 32;
            Width = TextRenderer.MeasureText(text, Font).Width + 4;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.Clear(BackColor);
            TextRenderer.DrawText(e.Graphics, Text, Font, new Rectangle(0, 2, Width, Height - 8), _selected ? Theme.Text : Theme.TextMuted,
                TextFormatFlags.Left | TextFormatFlags.Top | TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix);
            if (!_selected) return;
            using var line = new SolidBrush(Theme.Accent);
            e.Graphics.FillRectangle(line, 0, Height - Math.Max(2, LogicalToDeviceUnits(3)), Width - 4, Math.Max(2, LogicalToDeviceUnits(3)));
        }
    }

    /// <summary>4 tiles in a row, like the front page's Battlefield report.</summary>
    private sealed class StatTiles : Control
    {
        private LauncherNews.Stats? _s;

        public StatTiles()
        {
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
            BackColor = Theme.Panel;
        }

        public void Set(LauncherNews.Stats s) { _s = s; Invalidate(); }

        protected override void OnPaint(PaintEventArgs e)
        {
            var g = e.Graphics;
            g.Clear(BackColor);
            var items = new (string Label, int? Value, string Sub)[]
            {
                (T("ONLINE NOW"), _s?.Online, T("in the mod lobby")),
                (T("PEAK, 24 H"), _s?.Peak24, T("players in game")),
                (T("PLAYERS"), _s?.Players, T("all time")),
                (T("MATCHES"), _s?.Matches, T("all time")),
            };
            int gap = LogicalToDeviceUnits(8);
            int w = (Width - 3 * gap) / 4, h = Height;   // one row of 4
            using var label = Theme.Head(9.5f, semi: true);
            using var value = Theme.Head(21f);
            using var sub = Theme.Ui(8.25f);
            for (int i = 0; i < items.Length; i++)
            {
                var r = new Rectangle(i * (w + gap), 0, w, h);
                using (var fill = new SolidBrush(Theme.Surface)) g.FillRectangle(fill, r);
                using (var edge = new Pen(Theme.Border)) g.DrawRectangle(edge, r.X, r.Y, r.Width - 1, r.Height - 1);
                using (var strip = new SolidBrush(i == 0 ? Theme.Accent : Theme.Border))
                    g.FillRectangle(strip, r.X, r.Y, r.Width, Math.Max(2, LogicalToDeviceUnits(2)));
                int pad = LogicalToDeviceUnits(10);
                var f = TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix | TextFormatFlags.EndEllipsis;
                TextRenderer.DrawText(g, items[i].Label, label, new Rectangle(r.X + pad, r.Y + LogicalToDeviceUnits(8), r.Width - 2 * pad, LogicalToDeviceUnits(16)), Theme.TextMuted, f);
                TextRenderer.DrawText(g, items[i].Value?.ToString("N0") ?? "—", value, new Rectangle(r.X + pad, r.Y + LogicalToDeviceUnits(24), r.Width - 2 * pad, LogicalToDeviceUnits(32)), Theme.Text, f);
                TextRenderer.DrawText(g, items[i].Sub, sub, new Rectangle(r.X + pad, r.Bottom - LogicalToDeviceUnits(19), r.Width - 2 * pad, LogicalToDeviceUnits(15)), Theme.TextMuted, f);
            }
        }
    }
}
