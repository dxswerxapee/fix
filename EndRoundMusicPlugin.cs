using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Core.Attributes.Registration;
using CounterStrikeSharp.API.Modules.Commands;
using CounterStrikeSharp.API.Modules.Cvars;
using CounterStrikeSharp.API.Modules.Entities;
using CounterStrikeSharp.API.Modules.Utils;
using System.Text.Json.Serialization;

namespace EndRoundMusicPlugin;

public class EndRoundMusicConfig : BasePluginConfig
{
    [JsonPropertyName("MusicVolume")]
    public float MusicVolume { get; set; } = 0.5f;

    [JsonPropertyName("PlayMusicOnTerroristWin")]
    public bool PlayMusicOnTerroristWin { get; set; } = true;

    [JsonPropertyName("PlayMusicOnCounterTerroristWin")]
    public bool PlayMusicOnCounterTerroristWin { get; set; } = true;

    [JsonPropertyName("PlayMusicOnDraw")]
    public bool PlayMusicOnDraw { get; set; } = true;

    [JsonPropertyName("MusicDelay")]
    public float MusicDelay { get; set; } = 2.0f;

    [JsonPropertyName("TerroristWinSounds")]
    public List<string> TerroristWinSounds { get; set; } = new()
    {
        "music/terrorist_win_1.mp3",
        "music/terrorist_win_2.mp3"
    };

    [JsonPropertyName("CounterTerroristWinSounds")]
    public List<string> CounterTerroristWinSounds { get; set; } = new()
    {
        "music/ct_win_1.mp3",
        "music/ct_win_2.mp3"
    };

    [JsonPropertyName("DrawSounds")]
    public List<string> DrawSounds { get; set; } = new()
    {
        "music/draw_1.mp3",
        "music/draw_2.mp3"
    };
}

[MinimumApiVersion(210)]
public class EndRoundMusicPlugin : BasePlugin, IPluginConfig<EndRoundMusicConfig>
{
    public override string ModuleName => "End Round Music";
    public override string ModuleVersion => "1.0.0";
    public override string ModuleAuthor => "YourName";
    public override string ModuleDescription => "Плагин для воспроизведения музыки в конце раунда";

    public EndRoundMusicConfig Config { get; set; } = new();
    private readonly Random _random = new();
    private readonly HashSet<string> _preloadedSounds = new();

    public void OnConfigParsed(EndRoundMusicConfig config)
    {
        Config = config;
        PreloadSounds();
    }

    public override void Load(bool hotReload)
    {
        RegisterListener<Listeners.OnRoundEnd>(OnRoundEnd);
        RegisterListener<Listeners.OnMapStart>(OnMapStart);
        
        Console.WriteLine($"[{ModuleName}] Плагин загружен!");
    }

    public override void Unload(bool hotReload)
    {
        Console.WriteLine($"[{ModuleName}] Плагин выгружен!");
    }

    private void OnMapStart(string mapName)
    {
        AddTimer(5.0f, () => PreloadSounds());
    }

    private void PreloadSounds()
    {
        var allSounds = new List<string>();
        allSounds.AddRange(Config.TerroristWinSounds);
        allSounds.AddRange(Config.CounterTerroristWinSounds);
        allSounds.AddRange(Config.DrawSounds);

        foreach (var sound in allSounds.Distinct())
        {
            if (!_preloadedSounds.Contains(sound))
            {
                Server.PrecacheSound(sound);
                _preloadedSounds.Add(sound);
                Console.WriteLine($"[{ModuleName}] Предзагружен звук: {sound}");
            }
        }
    }

    private void OnRoundEnd(int winner, int reason, string message, float delay)
    {
        var teamWinner = (CsTeam)winner;
        List<string>? soundList = null;
        bool shouldPlay = false;

        switch (teamWinner)
        {
            case CsTeam.Terrorist:
                soundList = Config.TerroristWinSounds;
                shouldPlay = Config.PlayMusicOnTerroristWin;
                break;
            case CsTeam.CounterTerrorist:
                soundList = Config.CounterTerroristWinSounds;
                shouldPlay = Config.PlayMusicOnCounterTerroristWin;
                break;
            case CsTeam.None:
                soundList = Config.DrawSounds;
                shouldPlay = Config.PlayMusicOnDraw;
                break;
        }

        if (!shouldPlay || soundList == null || soundList.Count == 0)
            return;

        var selectedSound = soundList[_random.Next(soundList.Count)];
        
        AddTimer(Config.MusicDelay, () => PlaySoundToAll(selectedSound));
    }

    private void PlaySoundToAll(string soundPath)
    {
        var players = Utilities.GetPlayers().Where(p => p != null && p.IsValid && !p.IsBot);
        
        foreach (var player in players)
        {
            if (player.PawnIsAlive)
            {
                player.ExecuteClientCommand($"play {soundPath}");
            }
        }

        Console.WriteLine($"[{ModuleName}] Воспроизведен звук: {soundPath}");
    }

    [ConsoleCommand("css_music_reload", "Перезагрузить настройки музыки")]
    [RequiresPermissions("@css/config")]
    public void OnMusicReloadCommand(CCSPlayerController? player, CommandInfo command)
    {
        OnConfigParsed(Config);
        
        var message = "[EndRoundMusic] Настройки перезагружены!";
        if (player == null)
        {
            Console.WriteLine(message);
        }
        else
        {
            player.PrintToChat(message);
        }
    }

    [ConsoleCommand("css_music_test", "Тестировать воспроизведение музыки")]
    [RequiresPermissions("@css/generic")]
    public void OnMusicTestCommand(CCSPlayerController? player, CommandInfo command)
    {
        if (player == null) return;

        var args = command.GetCommandString.Split(' ');
        if (args.Length < 2)
        {
            player.PrintToChat("[EndRoundMusic] Использование: css_music_test <t/ct/draw>");
            return;
        }

        List<string>? soundList = args[1].ToLower() switch
        {
            "t" or "terrorist" => Config.TerroristWinSounds,
            "ct" or "counter" => Config.CounterTerroristWinSounds,
            "draw" => Config.DrawSounds,
            _ => null
        };

        if (soundList == null || soundList.Count == 0)
        {
            player.PrintToChat("[EndRoundMusic] Неверный тип или нет звуков для данного типа!");
            return;
        }

        var selectedSound = soundList[_random.Next(soundList.Count)];
        player.ExecuteClientCommand($"play {selectedSound}");
        player.PrintToChat($"[EndRoundMusic] Тестирование звука: {selectedSound}");
    }

    [ConsoleCommand("css_music_volume", "Установить громкость музыки")]
    [RequiresPermissions("@css/config")]
    public void OnMusicVolumeCommand(CCSPlayerController? player, CommandInfo command)
    {
        var args = command.GetCommandString.Split(' ');
        if (args.Length < 2 || !float.TryParse(args[1], out var volume))
        {
            var message = $"[EndRoundMusic] Текущая громкость: {Config.MusicVolume}. Использование: css_music_volume <0.0-1.0>";
            if (player == null)
                Console.WriteLine(message);
            else
                player.PrintToChat(message);
            return;
        }

        volume = Math.Clamp(volume, 0.0f, 1.0f);
        Config.MusicVolume = volume;

        var responseMessage = $"[EndRoundMusic] Громкость установлена на: {volume}";
        if (player == null)
            Console.WriteLine(responseMessage);
        else
            player.PrintToChat(responseMessage);
    }
}