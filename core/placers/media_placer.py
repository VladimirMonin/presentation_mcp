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

        Этот метод ищет медиа-объект в timing структуре слайда по shape_id
        и устанавливает delay="0" вместо delay="indefinite" для автозапуска.

        Args:
            slide: Объект слайда python-pptx.
            shape: Объект медиа-фигуры (результат add_movie).

        Note:
            Используется подход из python-pptx issue #427 (@monstarnn):
            https://github.com/scanny/python-pptx/issues/427

            Структура PowerPoint для медиа:
            <p:video>
              <p:cMediaNode>
                <p:cTn id="X">
                  <p:stCondLst>
                    <p:cond delay="indefinite"/> ← меняем на delay="0"
                  </p:stCondLst>
                </p:cTn>
                <p:tgtEl>
                  <p:spTgt spid="{shape_id}"/> ← по этому ID находим нужное медиа
                </p:tgtEl>
              </p:cMediaNode>
            </p:video>
        """
        logger.debug(f"� Настройка автозапуска для медиа-объекта")

        try:
            # Получаем shape_id медиа-объекта
            shape_id = shape.shape_id
            logger.debug(f"🔍 Shape ID медиа-объекта: {shape_id}")

            # Получаем root element слайда
            sld = slide.element

            # Импортируем функцию для преобразования namespace-префиксов
            from pptx.oxml.ns import qn

            # Ищем все элементы <p:video> в timing структуре
            timing_element = sld.find(qn('p:timing'))
            if timing_element is None:
                logger.warning(f"⚠️ Не найден <p:timing> на слайде, автозапуск не установлен")
                error_msg = f"Не найден timing элемент на слайде"
                self.errors.append(error_msg)
                return

            # Ищем все <p:video> элементы
            for video_elem in timing_element.iter(qn('p:video')):
                # Ищем <p:spTgt> с нужным spid
                for sp_tgt in video_elem.iter(qn('p:spTgt')):
                    if sp_tgt.get('spid') == str(shape_id):
                        logger.debug(f"✅ Найден <p:spTgt spid='{shape_id}'>")
                        
                        # Поднимаемся к родительскому <p:cTn>
                        # Структура: p:spTgt -> p:tgtEl -> p:cMediaNode -> p:cTn
                        c_media_node = sp_tgt.getparent().getparent()
                        c_tn = c_media_node.find(qn('p:cTn'))
                        
                        if c_tn is None:
                            logger.warning(f"⚠️ Не найден <p:cTn> для shape_id={shape_id}")
                            continue
                        
                        # Ищем <p:cond> внутри <p:stCondLst>
                        st_cond_lst = c_tn.find(qn('p:stCondLst'))
                        if st_cond_lst is None:
                            logger.warning(f"⚠️ Не найден <p:stCondLst> для shape_id={shape_id}")
                            continue
                        
                        cond = st_cond_lst.find(qn('p:cond'))
                        if cond is None:
                            logger.warning(f"⚠️ Не найден <p:cond> для shape_id={shape_id}")
                            continue
                        
                        # Устанавливаем delay="0" для автозапуска
                        old_delay = cond.get('delay', 'не указан')
                        cond.set('delay', '0')
                        
                        logger.debug(f"🔧 Изменён delay: '{old_delay}' -> '0'")
                        logger.debug(f"✅ Autoplay включен для shape_id={shape_id}")
                        return  # Нашли и настроили, выходим

            # Если дошли сюда, значит не нашли нужный spTgt
            logger.warning(f"⚠️ Не найден <p:spTgt> для shape_id={shape_id}, автозапуск не установлен")
            error_msg = f"Не найден timing элемент для медиа shape_id={shape_id}"
            self.errors.append(error_msg)

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
