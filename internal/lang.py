from typing import Optional
from locale import getdefaultlocale

lang = {
    "Cannot connect game components. Close programs using {0} and check folder permissions, then try again.": {
        "ru_RU": "Не удалось подключить игровые компоненты. Закройте программы, использующие {0}, проверьте права на папку и повторите попытку.",
    },
    "Choose game folder": {
        "ru_RU": "Выбрать папку игры",
    },
    "Choose Tiny Bunny folder": {
        "ru_RU": "Выберите папку Tiny Bunny",
    },
    "Local game components linked ({0}).": {
        "ru_RU": "Локальные игровые компоненты подключены ({0}).",
    },
    "Local game components available ({0}). Install them to connect the game.": {
        "ru_RU": "Доступны локальные компоненты ({0}). Установите их для подключения игры.",
    },
    "Connecting game components...": {
        "ru_RU": "Подключаем игровые компоненты...",
    },
    "Previous game components saved to {0}": {
        "ru_RU": "Предыдущие игровые компоненты сохранены в {0}",
    },
    "Game components connected.": {
        "ru_RU": "Игровые компоненты подключены.",
    },
    "Cannot check game components: {0}": {
        "ru_RU": "Не удалось проверить игровые компоненты: {0}",
    },
    "Game launch failed: {0}": {
        "ru_RU": "Не удалось запустить игру: {0}",
    },
    "Tiny Bunny Mod Manager": {
        "ru_RU": "Менеджер модов для игры Tiny Bunny",
    },
    "Developer mode": {
        "ru_RU": "Режим разработчика",
    },
    "Game will have developer mode enabled (config.developer).": {
        "ru_RU": "В игре будет включён режим разработчика (config.developer).",
    },
    "In-game console": {
        "ru_RU": "Внутриигровая консоль",
    },
    "Game will have in-game console enabled (config.console).": {
        "ru_RU": "В игре будет включена внутриигровая консоль (config.console).",
    },
    "External console": {
        "ru_RU": "Внешняя консоль",
    },
    "Game will launch with external console enabled, allowing easier debugging of mods.": {
        "ru_RU": "Игра будет запущена с внешней консолью, что упростит отладку модов.",
    },
    "Launch the game!": {
        "ru_RU": "Запустить игру!",
    },
    "Will start the game with selected features.": {
        "ru_RU": "Запустит игру с выбранными функциями.",
    },
    "Install game components": {
        "ru_RU": "Установить игровые компоненты",
    },
    "Will install game components of the manager.": {
        "ru_RU": "Установит игровые компоненты менеджера.",
    },
    "Error!": {
        "ru_RU": "Ошибка!",
    },
    "The program could not find Tiny Bunny game folder!": {
        "ru_RU": "Программа не смогла найти папку игры Tiny Bunny!",
    },
    "Cannot get local files! Are game component files installed?": {
        "ru_RU": "Невозможно найти локальные файлы! Установлены ли файлы компонентов игры?",
    },
    "Cannot get remote files! Please, check your internet connection.": {
        "ru_RU": "Невозможно получить удаленные файлы! Пожалуйста, проверьте подключение к Интернету.",
    },
    "The current version of the game component files ({0}) is outdated.\nPlease update them to the latest version ({1}).": {
        "ru_RU": "Текущая версия файлов компонентов игры ({0}) устарела.\nПожалуйста, обновите их до последней версии ({1}).",
    },
    "The current version of the game component files is up to date! ({0})": {
        "ru_RU": "Текущая версия файлов компонентов игры актуальна! ({0})",
    },
    "Installation failed: {0}": {
        "ru_RU": "Не удалось установить компоненты: {0}",
    },
    "Starting the download...": {
        "ru_RU": "Начинаем загрузку...",
    },
    "{0} bytes downloaded...": {
        "ru_RU": "{0} байтов скачано...",
    },
    "Unpacking \"{0}\", {1} out of {2} files...": {
        "ru_RU": "Распаковываем \"{0}\", {1} из {2} файлов...",
    }
}

def gt(s: str, locale: Optional[str] = None) -> str:
    """
    Translates string `s` to `locale` language or falls back to the original `s` if no translation found.
    Args:
        s: Original string.
        locale: Target locale string. Defaults to computer's locale.
    Returns:
        Translated or untranslated string `s`.
    """
    if locale is None:
        locale = getdefaultlocale()[0]
    if not s in lang:
        print(f"Could not find string \"{s}\" in lang.")
        return s
    localized = lang[s]
    return localized.get(locale, s)
