using System.Net.Http.Json;
using System.Text.Json;
using BAModManager.Core;
using static BAModManager.Core.Loc;

namespace BAModManager.Ui;

/// <summary>
/// Optional AI install helper. Shows the player exactly what is sent, and sends nothing until they tick the box.
/// The launcher only talks to the Freedom Arrow relay; the relay holds the AI key.
/// </summary>
internal sealed class HelperChatForm : Form
{
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(60) };
    private readonly string _url, _report;
    private readonly List<object> _messages = new();
    private readonly TextBox _chat, _input;
    private readonly Button _send;
    private readonly CheckBox _agree;

    public HelperChatForm(string url, string report)
    {
        _url = url;
        _report = report;
        Text = T("Ask the AI helper");
        Font = Theme.Ui(10f);
        BackColor = Theme.Background;
        ForeColor = Theme.Text;
        StartPosition = FormStartPosition.CenterParent;
        Size = new Size(760, 720);
        MinimumSize = new Size(480, 520);
        ShowInTaskbar = false;
        MinimizeBox = false;
        Padding = new Padding(18, 16, 18, 14);

        var warning = new Label
        {
            Dock = DockStyle.Top,
            AutoSize = false,
            Height = 92,
            ForeColor = Color.FromArgb(255, 196, 0),
            Text = T("⚠ What the AI sees: only the install report below and the messages you type here. "
                + "They are sent to the Freedom Arrow helper server and to DeepSeek, an AI company, to write the answer. "
                + "Nothing else on your PC is read or sent. Don't type passwords, your Steam login or personal details. "
                + "The AI can make mistakes and can't change anything on your PC."),
        };
        var reportBox = Box(report, 150);
        var reportLabel = new Label { Dock = DockStyle.Top, Height = 26, Text = T("The install report the AI sees:"), ForeColor = Theme.TextMuted };
        _agree = new CheckBox { Dock = DockStyle.Top, Height = 30, Text = T("I understand what is sent"), ForeColor = Theme.Text };

        _chat = Box("", 0);
        _chat.Dock = DockStyle.Fill;
        var chatHost = new Panel { Dock = DockStyle.Fill, BackColor = Theme.Panel, Padding = new Padding(10, 8, 4, 8) };
        chatHost.Controls.Add(_chat);

        var bottom = new Panel { Dock = DockStyle.Bottom, Height = 46, Padding = new Padding(0, 10, 0, 0), BackColor = Theme.Background };
        _input = new TextBox { Dock = DockStyle.Fill, BackColor = Theme.Panel, ForeColor = Theme.Text, BorderStyle = BorderStyle.FixedSingle, PlaceholderText = T("Type your question, for example: the game starts without the mod") };
        _send = Theme.MakeButton(T("Send"), ButtonKind.Primary);
        _send.Dock = DockStyle.Right;
        _send.Enabled = false;
        bottom.Controls.Add(_input);
        bottom.Controls.Add(_send);

        _agree.CheckedChanged += (_, _) => _send.Enabled = _agree.Checked;
        _send.Click += async (_, _) => await Send();
        AcceptButton = _send;

        Controls.Add(chatHost);
        Controls.Add(bottom);
        Controls.Add(_agree);
        Controls.Add(reportBox);
        Controls.Add(reportLabel);
        Controls.Add(warning);
    }

    private static TextBox Box(string text, int height) => new()
    {
        Dock = DockStyle.Top,
        Height = height,
        Multiline = true,
        ReadOnly = true,
        ScrollBars = ScrollBars.Vertical,
        BorderStyle = BorderStyle.None,
        BackColor = Theme.Panel,
        ForeColor = Theme.Text,
        Text = text.Replace("\r\n", "\n").Replace("\n", Environment.NewLine),
    };

    private async Task Send()
    {
        var question = _input.Text.Trim();
        if (question.Length == 0 || !_agree.Checked) return;
        _input.Clear();
        _send.Enabled = false;
        Append(T("You") + ": " + question);
        _messages.Add(new { role = "user", content = question });
        string answer;
        try
        {
            using var r = await Http.PostAsJsonAsync(_url, new { report = _report, messages = _messages });
            using var doc = JsonDocument.Parse(await r.Content.ReadAsStringAsync());
            answer = doc.RootElement.TryGetProperty("answer", out var a) ? a.GetString() ?? ""
                : doc.RootElement.TryGetProperty("error", out var e) ? e.GetString() ?? "" : "";
            if (r.IsSuccessStatusCode) _messages.Add(new { role = "assistant", content = answer });
            else _messages.RemoveAt(_messages.Count - 1);
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException or JsonException)
        {
            _messages.RemoveAt(_messages.Count - 1);
            answer = T("The helper can't be reached. Check your internet connection, or ask in the Freedom Arrow Discord.");
        }
        Append(T("Helper") + ": " + answer);
        _send.Enabled = _agree.Checked;
    }

    private void Append(string text)
    {
        _chat.AppendText(text.Replace("\r\n", "\n").Replace("\n", Environment.NewLine) + Environment.NewLine + Environment.NewLine);
    }

    protected override void OnHandleCreated(EventArgs e)
    {
        base.OnHandleCreated(e);
        Theme.UseDarkTitleBar(Handle);
    }
}
