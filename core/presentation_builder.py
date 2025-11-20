"""
Построитель презентаций PowerPoint.

Этот модуль содержит главный оркестратор, который собирает все компоненты
вместе для генерации итоговой презентации.
"""

import logging
from pathlib import Path
from typing import Optional
from pptx import Presentation
from pptx.util import Cm

from models import PresentationConfig, LayoutRegistry
from models.slide_types import BaseSlideConfig, YouTubeTitleSlideConfig
from io_handlers import ResourceLoader
from core import (
    clean_markdown_for_notes,
    calculate_smart_dimensions,
    convert_webp_to_png,
)
from config import (
    PLACEHOLDER_TITLE_IDX,
    PLACEHOLDER_SLIDE_NUM_IDX,
    PLACEHOLDER_TITLE_LAYOUT_TITLE_IDX,
    PLACEHOLDER_TITLE_LAYOUT_SLIDE_NUM_IDX,
    PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX,
)

logger = logging.getLogger(__name__)


class PresentationBuilder:
    """
    Оркестратор сборки презентации из конфигурации.

    Основной компонент, который:
    1. Загружает шаблон PPTX
    2. Создаёт слайды согласно конфигурации
    3. Размещает контент (текст, изображения, заметки)
    4. Сохраняет итоговый файл

    Attributes:
        layout_registry: Реестр макетов для размещения изображений.
        resource_loader: Загрузчик ресурсов (MD файлов, изображений).
        idx_title: Индекс заполнителя для заголовка.
        idx_slide_num: Индекс заполнителя для номера слайда.

    Example:
        >>> from models import LayoutRegistry
        >>> from io_handlers import ResourceLoader, PathResolver
        >>> from config import register_default_layouts
        >>>
        >>> resolver = PathResolver(Path("config.json"))
        >>> loader = ResourceLoader(resolver)
        >>> registry = LayoutRegistry()
        >>> register_default_layouts(registry)
        >>>
        >>> builder = PresentationBuilder(registry, loader)
        >>> prs = builder.build(config, Path("template.pptx"))
        >>> builder.save(prs, Path("output.pptx"))
    """

    def __init__(
        self,
        layout_registry: LayoutRegistry,
        resource_loader: ResourceLoader,
        idx_title: int = PLACEHOLDER_TITLE_IDX,
        idx_slide_num: int = PLACEHOLDER_SLIDE_NUM_IDX,
        verbose: bool = True,
    ):
        """
        Инициализация построителя.

        Args:
            layout_registry: Реестр макетов слайдов.
            resource_loader: Загрузчик ресурсов.
            idx_title: Индекс заполнителя заголовка (по умолчанию из config).
            idx_slide_num: Индекс заполнителя номера слайда.
            verbose: Выводить ли подробные сообщения о процессе.
        """
        self.layouts = layout_registry
        self.loader = resource_loader
        self.idx_title = idx_title
        self.idx_slide_num = idx_slide_num
        self.verbose = verbose

        self._errors = []  # Список ошибок, накопленных в процессе

        logger.debug(
            f"⚙️ Инициализация PresentationBuilder: idx_title={idx_title}, idx_slide_num={idx_slide_num}"
        )

    def build(
        self, config: PresentationConfig, template_path: Path
    ) -> Optional[Presentation]:
        """
        Главный метод сборки презентации.

        Args:
            config: Конфигурация презентации.
            template_path: Путь к файлу шаблона .pptx.

        Returns:
            Объект Presentation или None при критической ошибке.

        Raises:
            FileNotFoundError: Если шаблон не найден.
            ValueError: Если макет не найден в шаблоне.
        """
        self._errors = []  # Сброс ошибок

        logger.info(f"🚀 Начало сборки презентации из шаблона: {template_path}")
        logger.debug(f"📂 Полный путь к шаблону: {template_path.resolve()}")

        # Шаг 1: Загрузка шаблона
        logger.debug(f"� Загрузка шаблона: {template_path}")

        try:
            prs = Presentation(str(template_path))
            logger.debug(f"✅ Шаблон загружен, слайдов в мастере: {len(prs.slide_layouts)}")
        except FileNotFoundError:
            logger.error(f"❌ Шаблон не найден: {template_path}")
            raise FileNotFoundError(f"Шаблон не найден: {template_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки шаблона: {e}", exc_info=True)
            raise ValueError(f"Ошибка загрузки шаблона: {e}")

        # Шаг 2: Применение workaround для PowerPoint 2013
        # (Инициализация notes_slide для всех существующих слайдов)
        for slide in prs.slides:
            _ = slide.notes_slide

        # Шаг 3: Создание слайдов
        logger.info(f"� Создание {len(config.slides)} слайдов...")
        logger.debug(f"🔍 Глобальный макет: {config.layout_name}")

        for i, slide_cfg in enumerate(config.slides, 1):
            try:
                # Определяем макет для этого слайда
                # Если в слайде указан layout_name - используем его, иначе глобальный
                current_layout_name = slide_cfg.layout_name or config.layout_name
                
                if slide_cfg.layout_name:
                    logger.debug(f"🎭 Слайд #{i}: локальный макет '{current_layout_name}' (override)")
                else:
                    logger.debug(f"🎭 Слайд #{i}: глобальный макет '{current_layout_name}'")
                
                slide_layout = self._find_layout(prs, current_layout_name)

                if not slide_layout:
                    available = [layout.name for layout in prs.slide_layouts]
                    logger.error(f"❌ Макет '{current_layout_name}' не найден. Доступные: {available}")
                    raise ValueError(
                        f"Макет '{current_layout_name}' не найден в шаблоне. "
                        f"Доступные макеты: {available}"
                    )

                self._add_slide(prs, slide_layout, slide_cfg, i)
                logger.debug(f"✅ Слайд {i} '{slide_cfg.title}' создан успешно")
            except Exception as e:
                error_msg = f"Ошибка при создании слайда {i} ('{slide_cfg.title}'): {e}"
                self._errors.append(error_msg)
                logger.error(f"❌ {error_msg}", exc_info=True)

        # Шаг 4: Вывод итогов
        total_slides = len(config.slides)
        successful_slides = total_slides - len(self._errors)
        
        if self._errors:
            logger.warning(f"⚠️ Завершено с {len(self._errors)} ошибками из {total_slides} слайдов")
            for err in self._errors:
                logger.error(f"  - {err}")
        else:
            logger.info(f"✅ Презентация успешно собрана")

        logger.info(f"📊 Создано слайдов: {successful_slides}/{total_slides}")
        return prs

    def save(self, prs: Presentation, output_path: Path) -> None:
        """
        Сохраняет презентацию в файл.

        Args:
            prs: Объект презентации для сохранения.
            output_path: Путь для сохранения файла.

        Raises:
            IOError: Если не удалось сохранить файл.
        """
        try:
            logger.debug(f"🔧 Сохранение презентации: {output_path}")
            prs.save(str(output_path))
            logger.info(f"✅ Презентация сохранена: {output_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения презентации: {e}", exc_info=True)
            raise IOError(f"Ошибка сохранения презентации: {e}")

    def get_errors(self) -> list:
        """
        Возвращает список ошибок, накопленных в процессе сборки.

        Returns:
            Список строк с описаниями ошибок.
        """
        return self._errors.copy()

    def _add_slide(
        self, prs: Presentation, layout, cfg: BaseSlideConfig, number: int
    ) -> None:
        """
        Добавляет один слайд в презентацию.

        Args:
            prs: Объект презентации.
            layout: Макет слайда из шаблона.
            cfg: Конфигурация слайда (BaseSlideConfig или его подклассы).
            number: Номер слайда (для отображения).
        """
        logger.info(f"📄 Обработка слайда #{number}: '{cfg.title}' (Layout: {layout.name})")
        logger.debug(f"🔍 Тип конфига: {type(cfg).__name__}, изображений: {len(cfg.images) if cfg.images else 0}, аудио: {bool(cfg.audio)}")
        
        # Создание слайда
        slide = prs.slides.add_slide(layout)
        logger.debug(f"🔧 Слайд создан, ID: {slide.slide_id}")

        # Workaround для PowerPoint 2013
        _ = slide.notes_slide

        # Определяем, используется ли TitleLayout
        is_title_layout = isinstance(cfg, YouTubeTitleSlideConfig)

        # Выбираем правильные индексы в зависимости от типа макета
        if is_title_layout:
            idx_title = PLACEHOLDER_TITLE_LAYOUT_TITLE_IDX
            idx_slide_num = PLACEHOLDER_TITLE_LAYOUT_SLIDE_NUM_IDX
        else:
            idx_title = self.idx_title
            idx_slide_num = self.idx_slide_num

        # 1. Заголовок
        try:
            title_ph = slide.shapes.placeholders[idx_title]
            title_ph.text_frame.text = cfg.title
            logger.debug(f"🔧 Title установлен в placeholder idx={idx_title}")
        except KeyError:
            logger.error(f"❌ Заполнитель заголовка idx={idx_title} не найден")
            raise KeyError(f"Заполнитель заголовка с индексом {idx_title} не найден")

        # 2. Дополнительные поля для YouTubeTitleSlideConfig
        if is_title_layout:
            logger.debug("🔧 Обработка YouTube-титульника")
            self._set_youtube_title_fields(slide, cfg)

        # 3. Номер слайда
        try:
            num_ph = slide.shapes.placeholders[idx_slide_num]
            num_ph.text_frame.text = str(number)
            logger.debug(f"🔧 Номер слайда {number} установлен в placeholder idx={idx_slide_num}")
        except KeyError:
            logger.debug(f"🔍 Заполнитель номера idx={idx_slide_num} не найден (не критично)")

        # 4. Заметки докладчика
        logger.debug(f"📝 Загрузка заметок: {cfg.notes_source}")
        notes_text = self.loader.load_notes(cfg.notes_source)
        clean_notes = clean_markdown_for_notes(notes_text)
        slide.notes_slide.notes_text_frame.text = clean_notes
        logger.debug(f"🔧 Заметки добавлены: {len(clean_notes)} символов")

        # 5. Изображения
        logger.debug(f"� Размещение изображений: {len(cfg.images) if cfg.images else 0}")
        self._place_images(slide, cfg)

        # 6. Аудио (если указано)
        if cfg.audio:
            logger.debug(f"🔍 Добавление аудио: {cfg.audio}")
            self._place_audio(slide, cfg.audio)

    def _set_youtube_title_fields(self, slide, cfg: YouTubeTitleSlideConfig) -> None:
        """
        Устанавливает специфичные поля для YouTubeTitleSlideConfig.

        Args:
            slide: Объект слайда.
            cfg: Конфигурация титульного слайда YouTube.

        Note:
            Индексы заполнителей для TitleLayout в youtube_base.pptx:
            - idx=10: title (основной заголовок)
            - idx=12: slide_number (номер слайда)
            - idx=13: subtitle (подзаголовок/описание серии)
        """
        logger.debug(f"🔧 YouTube поля: subtitle='{cfg.subtitle}', series_number={cfg.series_number}")
        
        # Subtitle (placeholder idx=13 в TitleLayout)
        try:
            subtitle_ph = slide.shapes.placeholders[
                PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX
            ]
            subtitle_ph.text_frame.text = cfg.subtitle
            logger.debug(f"🔧 Subtitle установлен в placeholder idx={PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX}")
        except KeyError as e:
            logger.warning(f"⚠️ Заполнитель subtitle idx={PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX} не найден: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка при заполнении subtitle: {e}", exc_info=True)

        # Series number - пока нет заполнителя в шаблоне
        if cfg.series_number:
            logger.debug(f"🔍 Series number '{cfg.series_number}' не добавлен (нет заполнителя)")

    def _place_images(self, slide, cfg: BaseSlideConfig) -> None:
        """
        Размещает изображения на слайде согласно макету.

        Args:
            slide: Объект слайда.
            cfg: Конфигурация слайда.
        """
        if not cfg.images:
            logger.debug("🔍 Нет изображений для размещения")
            return  # Нет изображений - пропускаем

        logger.info(f"🖼️ Размещение изображений для слайда: '{cfg.title}'")
        
        # Получаем чертёж макета
        # Для YouTubeTitleSlideConfig используем фиксированный макет title_youtube
        if isinstance(cfg, YouTubeTitleSlideConfig):
            layout_type = "title_youtube"
            logger.debug("🔍 YouTube титульник -> макет 'title_youtube'")
        else:
            layout_type = cfg.layout_type
            logger.debug(f"🔍 Используем макет из конфига: '{layout_type}'")

        try:
            blueprint = self.layouts.get(layout_type)
            logger.debug(f"🔍 Чертеж макета '{layout_type}': требуется {blueprint.required_images} изображений")
        except KeyError:
            logger.error(f"❌ Макет '{layout_type}' не зарегистрирован. Доступные: {self.layouts.list_all()}")
            raise KeyError(
                f"Макет '{layout_type}' не зарегистрирован. "
                f"Доступные: {self.layouts.list_all()}"
            )

        # Проверка количества изображений
        if len(cfg.images) < blueprint.required_images:
            logger.warning(
                f"⚠️ Ожидалось {blueprint.required_images} изображений, предоставлено {len(cfg.images)}"
            )

        # Размещение каждого изображения
        for i, img_path_str in enumerate(cfg.images):
            if i >= len(blueprint.placements):
                # Больше изображений, чем размещений - игнорируем лишние
                logger.warning(f"⚠️ Изображение #{i + 1} '{img_path_str}' игнорируется (нет размещения в макете)")
                break

            try:
                logger.debug(f"📍 Размещение изображения: {img_path_str}")
                
                # Разрешение пути к изображению
                img_path = self.loader.resolve_image(img_path_str)

                # Автоматическая конвертация WebP → PNG (in-memory)
                original_path = img_path
                image_source = img_path  # По умолчанию используем путь к файлу

                if img_path.suffix.lower() == ".webp":
                    try:
                        # convert_webp_to_png теперь возвращает BytesIO
                        image_source = convert_webp_to_png(img_path)
                        logger.debug(f"🔄 WebP сконвертирован в памяти: {original_path.name}")
                    except Exception as e:
                        error_msg = f"Ошибка конвертации WebP {img_path_str}: {e}"
                        self._errors.append(error_msg)
                        logger.error(f"❌ {error_msg}", exc_info=True)
                        continue

                # Получение параметров размещения
                placement = blueprint.placements[i]
                placement_dict = placement.to_dict()
                
                logger.debug(
                    f"📏 Чертеж: left={placement_dict['left']}, top={placement_dict['top']}, "
                    f"max_width={placement_dict['max_width']}, max_height={placement_dict['max_height']}"
                )

                # Умное масштабирование (для BytesIO используем исходный путь)
                dimensions_source = (
                    original_path if img_path.suffix.lower() == ".webp" else img_path
                )
                width, height = calculate_smart_dimensions(
                    dimensions_source,
                    placement_dict["max_width"],
                    placement_dict["max_height"],
                )

                # Конвертация в единицы python-pptx
                left_cm = Cm(placement_dict["left"])
                top_cm = Cm(placement_dict["top"])
                width_cm = Cm(width) if width is not None else None
                height_cm = Cm(height) if height is not None else None
                
                width_str = f"{width:.2f}" if width is not None else "auto"
                height_str = f"{height:.2f}" if height is not None else "auto"
                logger.debug(
                    f"📐 Вычислено (см): left={placement_dict['left']:.2f}, top={placement_dict['top']:.2f}, "
                    f"w={width_str}, h={height_str}"
                )
                
                # EMU для детального логирования
                emu_left = int(left_cm)
                emu_top = int(top_cm)
                emu_width = int(width_cm) if width_cm else None
                emu_height = int(height_cm) if height_cm else None
                
                logger.debug(
                    f"🎯 Финальные EMU: left={emu_left}, top={emu_top}, "
                    f"width={emu_width or 'auto'}, height={emu_height or 'auto'}"
                )

                # Добавление изображения на слайд
                # python-pptx поддерживает как пути (str/Path), так и потоки (BytesIO)
                if isinstance(image_source, Path):
                    slide.shapes.add_picture(
                        str(image_source),
                        left_cm,
                        top_cm,
                        width=width_cm,
                        height=height_cm,
                    )
                else:
                    # BytesIO передаём напрямую
                    slide.shapes.add_picture(
                        image_source, left_cm, top_cm, width=width_cm, height=height_cm
                    )

            except FileNotFoundError:
                # Изображение не найдено - добавляем в ошибки, но продолжаем
                error_msg = f"Изображение не найдено: {img_path_str}"
                self._errors.append(error_msg)
                logger.warning(f"⚠️ {error_msg}")

            except Exception as e:
                # Другая ошибка при добавлении изображения
                error_msg = f"Ошибка добавления изображения {img_path_str}: {e}"
                self._errors.append(error_msg)
                logger.error(f"❌ {error_msg}", exc_info=True)

    def _place_audio(self, slide, audio_path_str: str) -> None:
        """
        Размещает аудиофайл на слайде используя workaround через add_movie.

        Args:
            slide: Объект слайда.
            audio_path_str: Путь к аудиофайлу (строка).

        Note:
            python-pptx не имеет нативного метода add_audio, поэтому используется
            add_movie с mime_type='video/mp4'. PowerPoint корректно распознает аудио
            при открытии. Объект скрывается за пределами видимой области слайда.
        """
        logger.info(f"🎵 Добавление медиа: {audio_path_str}")
        
        try:
            # Разрешаем путь к аудиофайлу
            audio_path = self.loader.resolve_audio(audio_path_str)
            
            logger.debug(f"🔗 Вставка медиа-блоба: {audio_path.name}, MIME: video/mp4")
            logger.debug("🔧 Применен audio workaround: Координаты left=0cm, top=-10cm")

            # Используем add_movie workaround
            # Геометрия: минимальный размер (1x1 см), вынесен за пределы слайда
            slide.shapes.add_movie(
                str(audio_path),
                left=Cm(0),
                top=Cm(-10),  # Скрыт за верхней границей слайда
                width=Cm(1),
                height=Cm(1),
                mime_type="video/mp4",  # Критично для прохождения валидации библиотеки
            )

            logger.debug("🔧 Аудио добавлено успешно")

        except FileNotFoundError:
            error_msg = f"Аудиофайл не найден: {audio_path_str}"
            self._errors.append(error_msg)
            logger.warning(f"⚠️ Медиа-файл не найден: {audio_path_str}, продолжаем без него")

        except Exception as e:
            # Не блокируем генерацию слайда, если аудио не вставилось
            error_msg = f"Ошибка добавления аудио {audio_path_str}: {e}"
            self._errors.append(error_msg)
            logger.error(f"❌ {error_msg}", exc_info=True)

    @staticmethod
    def _find_layout(prs: Presentation, layout_name: str):
        """
        Ищет макет по имени в шаблоне.

        Args:
            prs: Объект презентации.
            layout_name: Имя макета для поиска.

        Returns:
            Объект макета или None, если не найден.
        """
        logger.debug(f"🔍 Поиск макета '{layout_name}' в мастере...")
        
        for layout in prs.slide_layouts:
            if layout.name == layout_name:
                logger.debug(f"🔧 Макет '{layout_name}' найден")
                return layout
        
        logger.warning(f"⚠️ Макет '{layout_name}' не найден в шаблоне")
        return None
