# End Round Music Plugin для CS2

Плагин для CounterStrikeSharp, который воспроизводит музыку в конце раунда в зависимости от победившей команды.

## Особенности

- ✅ Воспроизведение разной музыки для побед T/CT/ничьи
- ✅ Настраиваемая громкость и задержка
- ✅ Случайный выбор из списка треков
- ✅ Команды для тестирования и управления
- ✅ Предзагрузка звуков для плавного воспроизведения
- ✅ Полная настройка через JSON конфиг

## Требования

- Counter-Strike 2 сервер с CounterStrikeSharp
- .NET 8.0 SDK для компиляции
- Windows или Linux

## Компиляция плагина на Windows

### Шаг 1: Установка .NET 8.0 SDK

1. Скачайте и установите .NET 8.0 SDK с официального сайта Microsoft:
   ```
   https://dotnet.microsoft.com/download/dotnet/8.0
   ```

2. Проверьте установку, открыв командную строку и выполнив:
   ```cmd
   dotnet --version
   ```

### Шаг 2: Компиляция плагина

1. Откройте командную строку в папке с плагином
2. Выполните команду:
   ```cmd
   dotnet build -c Release
   ```

3. После успешной компиляции найдите файл `EndRoundMusicPlugin.dll` в папке:
   ```
   bin/Release/net8.0/EndRoundMusicPlugin.dll
   ```

## Установка плагина на сервер

### Шаг 1: Установка CounterStrikeSharp

1. Скачайте последнюю версию CounterStrikeSharp:
   ```
   https://github.com/roflmuffin/CounterStrikeSharp/releases
   ```

2. Распакуйте в папку сервера CS2

### Шаг 2: Установка плагина

1. Скопируйте `EndRoundMusicPlugin.dll` в папку:
   ```
   csgo/addons/counterstrikesharp/plugins/EndRoundMusicPlugin/
   ```

2. Скопируйте `config.json` в папку:
   ```
   csgo/addons/counterstrikesharp/configs/plugins/EndRoundMusicPlugin/
   ```

## Настройка музыки

### Создание папки для музыки

Создайте папку для музыки в:
```
csgo/sound/music/
```

### Добавление музыкальных файлов

1. Поместите ваши MP3 файлы в папку `csgo/sound/music/`
2. Переименуйте их согласно конфигурации:
   - `terrorist_win_1.mp3`, `terrorist_win_2.mp3`, `terrorist_win_3.mp3`
   - `ct_win_1.mp3`, `ct_win_2.mp3`, `ct_win_3.mp3`
   - `draw_1.mp3`, `draw_2.mp3`

### Автоматическая загрузка музыки для клиентов

Для автоматической загрузки музыки клиентам создайте файл `music.res` в папке `csgo/`:

```
sound/music/terrorist_win_1.mp3
sound/music/terrorist_win_2.mp3
sound/music/terrorist_win_3.mp3
sound/music/ct_win_1.mp3
sound/music/ct_win_2.mp3
sound/music/ct_win_3.mp3
sound/music/draw_1.mp3
sound/music/draw_2.mp3
```

И добавьте в `csgo/cfg/server.cfg`:
```
sv_downloadurl "http://yourserver.com/fastdownload/"
sv_allowdownload 1
sv_allowupload 1
```

## Настройка конфигурации

Отредактируйте файл `config.json`:

```json
{
  "MusicVolume": 0.5,              // Громкость (0.0 - 1.0)
  "PlayMusicOnTerroristWin": true, // Играть при победе T
  "PlayMusicOnCounterTerroristWin": true, // Играть при победе CT
  "PlayMusicOnDraw": true,         // Играть при ничьей
  "MusicDelay": 2.0,               // Задержка перед воспроизведением
  "TerroristWinSounds": [          // Список треков для побед T
    "music/terrorist_win_1.mp3"
  ],
  "CounterTerroristWinSounds": [   // Список треков для побед CT
    "music/ct_win_1.mp3"
  ],
  "DrawSounds": [                  // Список треков для ничьей
    "music/draw_1.mp3"
  ]
}
```

## Команды плагина

- `css_music_reload` - Перезагрузить настройки плагина (требует права @css/config)
- `css_music_test <t/ct/draw>` - Тестировать воспроизведение музыки (требует права @css/generic)
- `css_music_volume <0.0-1.0>` - Установить громкость музыки (требует права @css/config)

### Примеры использования команд:

```
css_music_test t          // Тестировать музыку победы террористов
css_music_test ct         // Тестировать музыку победы спецназа
css_music_test draw       // Тестировать музыку ничьей
css_music_volume 0.8      // Установить громкость 80%
css_music_reload          // Перезагрузить настройки
```

## Структура файлов

```
EndRoundMusicPlugin/
├── EndRoundMusicPlugin.cs     // Основной код плагина
├── EndRoundMusicPlugin.csproj // Файл проекта
├── config.json               // Конфигурация по умолчанию
└── README.md                // Этот файл

Установка на сервере:
csgo/
├── addons/counterstrikesharp/plugins/EndRoundMusicPlugin/
│   └── EndRoundMusicPlugin.dll
├── addons/counterstrikesharp/configs/plugins/EndRoundMusicPlugin/
│   └── config.json
├── sound/music/
│   ├── terrorist_win_1.mp3
│   ├── ct_win_1.mp3
│   └── ...
└── music.res
```

## Рекомендуемые форматы аудио

- **MP3**: Наиболее совместимый формат
- **WAV**: Высокое качество, но большие файлы
- Битрейт: 128-320 kbps
- Длительность: 10-30 секунд (для лучшего игрового опыта)

## Устранение неполадок

### Музыка не воспроизводится:

1. Проверьте, что файлы находятся в правильной папке `csgo/sound/music/`
2. Убедитесь, что пути в конфиге соответствуют названиям файлов
3. Проверьте права доступа к файлам
4. Убедитесь, что плагин загружен (`css plugins list`)

### Музыка не загружается клиентам:

1. Настройте FastDL сервер
2. Проверьте файл `music.res`
3. Убедитесь, что `sv_allowdownload 1` в server.cfg

### Плагин не компилируется:

1. Убедитесь, что установлен .NET 8.0 SDK
2. Проверьте доступность пакета CounterStrikeSharp.API
3. Выполните `dotnet restore` перед компиляцией

## Лицензия

Этот плагин предоставляется "как есть" для использования в образовательных и развлекательных целях.

## Поддержка

Если у вас возникли проблемы или вопросы, создайте issue или обратитесь к документации CounterStrikeSharp.