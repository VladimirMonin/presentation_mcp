"""
Размещение медиа-контента (аудио/видео) на слайдах.

Модуль отвечает за вставку аудио и видео файлов в презентацию,
включая настройку автоматического воспроизведения через OXML.
"""

import logging
from pathlib import Path
from pptx.util import Cm
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls

from io_handlers import ResourceLoader

logger = logging.getLogger(__name__)


class MediaPlacer:
    """
    Класс для размещения медиа-контента (аудио/видео) на слайдах.

    Этот класс инкапсулирует всю логику работы с медиа-файлами:
    - Резолвинг путей через ResourceLoader
    - Workaround для аудио через add_movie (python-pptx limitation)
    - XML-инъекция для автоматического воспроизведения

    Attributes:
        loader: ResourceLoader для разрешения путей к медиа-файлам.
        errors: Список ошибок, возникших при размещении медиа.

    Example:
        >>> from io_handlers import ResourceLoader, PathResolver
        >>> resolver = PathResolver(Path("config.json"))
        >>> loader = ResourceLoader(resolver)
        >>> placer = MediaPlacer(loader)
        >>>
        >>> placer.place_audio(slide, "audio/intro.mp3")
    """

    def __init__(self, resource_loader: ResourceLoader):
        """
        Инициализация MediaPlacer.

        Args:
            resource_loader: Объект для разрешения путей к ресурсам.
        """
        self.loader = resource_loader
        self.errors = []
        logger.debug("⚙️ MediaPlacer инициализирован")

    def place_audio(self, slide, audio_path_str: str, autoplay: bool = True) -> bool:
        """
        Вставляет аудиофайл на слайд и настраивает автозапуск.

        Args:
            slide: Объект слайда python-pptx.
            audio_path_str: Путь к аудиофайлу (строка).
            autoplay: Включить ли автоматическое воспроизведение (default: True).

        Returns:
            True если аудио успешно добавлено, False в случае ошибки.

        Note:
            python-pptx не имеет нативного метода add_audio, поэтому используется
            add_movie с mime_type='video/mp4'. PowerPoint корректно распознает аудио
            при открытии. Объект скрывается за пределами видимой области слайда.

            Автозапуск реализуется через XML-инъекцию структуры <p:timing>.
        """
        logger.info(f"🎵 Добавление медиа: {audio_path_str}")

        try:
            # 1. Разрешаем путь к аудиофайлу через ResourceLoader
            audio_path = self.loader.resolve_audio(audio_path_str)
            logger.debug(f"🔗 Файл разрешен: {audio_path}")

            # 2. Вставка медиа-объекта (Workaround через Movie)
            logger.debug(f"🔧 Вставка медиа-блоба: {audio_path.name}, MIME: video/mp4")
            logger.debug("🔧 Применен audio workaround: Координаты left=0cm, top=-10cm")

            movie = slide.shapes.add_movie(
                str(audio_path),
                left=Cm(0),  # Скрыт слева
                top=Cm(-10),  # Скрыт выше верхней границы слайда
                width=Cm(1),  # Минимальный размер
                height=Cm(1),
                mime_type="video/mp4",  # Критично для прохождения валидации библиотеки
            )
            logger.debug("✅ Медиа-объект добавлен на слайд")

            # 3. Включение автозапуска (если требуется)
            if autoplay:
                self._enable_autoplay(slide, movie)
                logger.info(f"🔧 Автозапуск включен для: {audio_path.name}")
            else:
                logger.debug("🔍 Автозапуск отключен (autoplay=False)")

            return True

        except FileNotFoundError:
            error_msg = f"Аудиофайл не найден: {audio_path_str}"
            self.errors.append(error_msg)
            logger.warning(f"⚠️ Медиа-файл не найден: {audio_path_str}, продолжаем без него")
            return False

        except Exception as e:
            # Не блокируем генерацию слайда, если аудио не вставилось
            error_msg = f"Ошибка добавления аудио {audio_path_str}: {e}"
            self.errors.append(error_msg)
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False

    def _enable_autoplay(self, slide, shape) -> None:
        """
        Включает автоматическое воспроизведение для медиа-объекта через OXML.

        Этот метод создает сложную XML-структуру <p:timing> для настройки
        автоматического запуска медиа при открытии слайда ('onBegin').

        Args:
            slide: Объект слайда python-pptx.
            shape: Объект медиа-фигуры (результат add_movie).

        Note:
            Это хак для обхода ограничения python-pptx, который не предоставляет
            API для настройки анимации. Мы напрямую модифицируем XML-дерево слайда.

            Структура создает параллельную анимацию <p:par>, которая запускается
            при старте слайда (delay="0") и вызывает команду playFrom(0.0) для
            указанного shape_id.

        XML Structure:
            <p:par> (параллельная анимация)
              └─ <p:cTn> (timing node с delay=0)
                   └─ <p:childTnLst>
                        └─ <p:cmd type="call" cmd="playFrom(0.0)">
                             └─ <p:tgtEl>
                                  └─ <p:spTgt spid="{shape_id}" />
        """
        logger.debug(f"🔧 Настройка автозапуска для медиа-объекта")

        try:
            # 1. Получаем или создаем дерево тайминга слайда
            timing = slide.element.get_or_add_timing()
            tnLst = timing.tnLst
            if tnLst is None:
                tnLst = timing.add_tnLst()
                logger.debug("🔍 Создан новый timing list для слайда")
            else:
                logger.debug("🔍 Использован существующий timing list")

            # 2. Получаем shape_id для привязки анимации к объекту
            shape_id = shape.shape_id
            logger.debug(f"🔍 Shape ID медиа-объекта: {shape_id}")

            # 3. Генерируем XML для автозапуска
            # Это стандартная структура PowerPoint для "Start Automatically"
            xml = f"""
            <p:par {nsdecls('p')}>
              <p:cTn id="1" fill="hold" display="0" >
                <p:stCondLst>
                  <p:cond delay="0" />
                </p:stCondLst>
                <p:childTnLst>
                  <p:par>
                    <p:cTn id="2" fill="hold" display="0">
                      <p:stCondLst>
                        <p:cond delay="0" />
                      </p:stCondLst>
                      <p:childTnLst>
                        <p:par>
                          <p:cTn id="3" fill="hold" display="0">
                            <p:stCondLst>
                              <p:cond delay="0" />
                            </p:stCondLst>
                            <p:childTnLst>
                              <p:cmd type="call" cmd="playFrom(0.0)">
                                <p:cBhvr>
                                  <p:cTn id="4" dur="indefinite" fill="hold" display="0" />
                                  <p:tgtEl>
                                    <p:spTgt spid="{shape_id}" />
                                  </p:tgtEl>
                                </p:cBhvr>
                              </p:cmd>
                            </p:childTnLst>
                          </p:cTn>
                        </p:par>
                      </p:childTnLst>
                    </p:cTn>
                  </p:par>
                </p:childTnLst>
              </p:cTn>
            </p:par>
            """

            logger.debug("🔧 XML структура для автозапуска сгенерирована")

            # 4. Парсим XML и добавляем в дерево тайминга
            par = parse_xml(xml)
            tnLst.append(par)
            logger.debug(f"✅ Autoplay включен для shape_id={shape_id}")

        except Exception as e:
            error_msg = f"Ошибка включения автозапуска: {e}"
            self.errors.append(error_msg)
            logger.error(f"❌ {error_msg}", exc_info=True)
            # Не падаем, просто логируем - медиа уже вставлено, просто без автозапуска

    def get_errors(self) -> list:
        """
        Возвращает список ошибок, накопленных в процессе работы.

        Returns:
            Копия списка строк с описаниями ошибок.
        """
        return self.errors.copy()

    def clear_errors(self) -> None:
        """Очищает список накопленных ошибок."""
        self.errors = []
        logger.debug("🧹 Список ошибок MediaPlacer очищен")
