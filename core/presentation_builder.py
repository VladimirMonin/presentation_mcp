"""
Построитель презентаций PowerPoint.

Этот модуль содержит главный оркестратор, который собирает все компоненты
вместе для генерации итоговой презентации.
"""

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

        # Шаг 1: Загрузка шаблона
        if self.verbose:
            print(f"📄 Загрузка шаблона: {template_path}")

        try:
            prs = Presentation(str(template_path))
        except FileNotFoundError:
            raise FileNotFoundError(f"Шаблон не найден: {template_path}")
        except Exception as e:
            raise ValueError(f"Ошибка загрузки шаблона: {e}")

        # Шаг 2: Применение workaround для PowerPoint 2013
        # (Инициализация notes_slide для всех существующих слайдов)
        for slide in prs.slides:
            _ = slide.notes_slide

        # Шаг 3: Создание слайдов
        if self.verbose:
            print(f"\n🔨 Создание {len(config.slides)} слайдов...")

        for i, slide_cfg in enumerate(config.slides, 1):
            try:
                # Определяем макет для этого слайда
                # Если в слайде указан layout_name - используем его, иначе глобальный
                current_layout_name = slide_cfg.layout_name or config.layout_name
                slide_layout = self._find_layout(prs, current_layout_name)

                if not slide_layout:
                    raise ValueError(
                        f"Макет '{current_layout_name}' не найден в шаблоне. "
                        f"Доступные макеты: {[layout.name for layout in prs.slide_layouts]}"
                    )

                self._add_slide(prs, slide_layout, slide_cfg, i)
                if self.verbose:
                    layout_info = (
                        f" [{current_layout_name}]" if slide_cfg.layout_name else ""
                    )
                    print(f"  ✓ Слайд {i}: '{slide_cfg.title}'{layout_info}")
            except Exception as e:
                error_msg = f"Ошибка при создании слайда {i} ('{slide_cfg.title}'): {e}"
                self._errors.append(error_msg)
                if self.verbose:
                    print(f"  ✗ {error_msg}")

        # Шаг 4: Вывод итогов
        if self._errors:
            print(f"\n⚠ Завершено с {len(self._errors)} ошибками:")
            for err in self._errors:
                print(f"  - {err}")
        elif self.verbose:
            print("\n✅ Презентация успешно собрана!")

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
            prs.save(str(output_path))
            if self.verbose:
                print(f"\n💾 Сохранено: {output_path}")
        except Exception as e:
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
        # Создание слайда
        slide = prs.slides.add_slide(layout)

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
        except KeyError:
            raise KeyError(f"Заполнитель заголовка с индексом {idx_title} не найден")

        # 2. Дополнительные поля для YouTubeTitleSlideConfig
        if is_title_layout:
            self._set_youtube_title_fields(slide, cfg)

        # 3. Номер слайда
        try:
            num_ph = slide.shapes.placeholders[idx_slide_num]
            num_ph.text_frame.text = str(number)
        except KeyError:
            # Номер не критичен, можно продолжить
            if self.verbose:
                print(f"    ⚠ Заполнитель номера ({idx_slide_num}) не найден")

        # 4. Заметки докладчика
        notes_text = self.loader.load_notes(cfg.notes_source)
        clean_notes = clean_markdown_for_notes(notes_text)
        slide.notes_slide.notes_text_frame.text = clean_notes

        # 5. Изображения
        self._place_images(slide, cfg)

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
        # Subtitle (placeholder idx=13 в TitleLayout)
        try:
            subtitle_ph = slide.shapes.placeholders[
                PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX
            ]
            subtitle_ph.text_frame.text = cfg.subtitle
        except KeyError as e:
            if self.verbose:
                print(
                    f"    ❌ Заполнитель subtitle (idx={PLACEHOLDER_TITLE_LAYOUT_SUBTITLE_IDX}) не найден: {e}"
                )
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Ошибка при заполнении subtitle: {e}")

        # Series number - пока нет заполнителя в шаблоне
        if cfg.series_number and self.verbose:
            print(
                f"    ℹ Series number '{cfg.series_number}' не добавлен (нет заполнителя)"
            )

    def _place_images(self, slide, cfg: BaseSlideConfig) -> None:
        """
        Размещает изображения на слайде согласно макету.

        Args:
            slide: Объект слайда.
            cfg: Конфигурация слайда.
        """
        if not cfg.images:
            return  # Нет изображений - пропускаем

        # Получаем чертёж макета
        # Для YouTubeTitleSlideConfig используем фиксированный макет title_youtube
        if isinstance(cfg, YouTubeTitleSlideConfig):
            layout_type = "title_youtube"
        else:
            layout_type = cfg.layout_type

        try:
            blueprint = self.layouts.get(layout_type)
        except KeyError:
            raise KeyError(
                f"Макет '{layout_type}' не зарегистрирован. "
                f"Доступные: {self.layouts.list_all()}"
            )

        # Проверка количества изображений
        if len(cfg.images) < blueprint.required_images:
            if self.verbose:
                print(
                    f"    ⚠ Ожидалось {blueprint.required_images} изображений, "
                    f"предоставлено {len(cfg.images)}"
                )

        # Размещение каждого изображения
        for i, img_path_str in enumerate(cfg.images):
            if i >= len(blueprint.placements):
                # Больше изображений, чем размещений - игнорируем лишние
                if self.verbose:
                    print(f"    ⚠ Изображение #{i + 1} игнорируется (нет размещения)")
                break

            # Инициализация переменной для временного файла вне try-блока
            temp_png_path = None

            try:
                # Разрешение пути к изображению
                img_path = self.loader.resolve_image(img_path_str)

                # Автоматическая конвертация WebP → PNG
                original_path = img_path
                if img_path.suffix.lower() == ".webp":
                    try:
                        temp_png_path = convert_webp_to_png(img_path)
                        img_path = temp_png_path
                        if self.verbose:
                            print(
                                f"    🔄 WebP сконвертирован в PNG: {original_path.name}"
                            )
                    except Exception as e:
                        error_msg = f"Ошибка конвертации WebP {img_path_str}: {e}"
                        self._errors.append(error_msg)
                        if self.verbose:
                            print(f"    ✗ {error_msg}")
                        continue

                # Получение параметров размещения
                placement = blueprint.placements[i]
                placement_dict = placement.to_dict()

                # Умное масштабирование
                width, height = calculate_smart_dimensions(
                    img_path, placement_dict["max_width"], placement_dict["max_height"]
                )

                # Конвертация в единицы python-pptx
                left_cm = Cm(placement_dict["left"])
                top_cm = Cm(placement_dict["top"])
                width_cm = Cm(width) if width is not None else None
                height_cm = Cm(height) if height is not None else None

                # Добавление изображения на слайд
                slide.shapes.add_picture(
                    str(img_path), left_cm, top_cm, width=width_cm, height=height_cm
                )

                # Удаление временного PNG файла после вставки
                if temp_png_path and temp_png_path.exists():
                    try:
                        temp_png_path.unlink()
                        if self.verbose:
                            print(f"    🗑 Временный файл удалён: {temp_png_path.name}")
                    except Exception as e:
                        if self.verbose:
                            print(
                                f"    ⚠ Не удалось удалить временный файл {temp_png_path.name}: {e}"
                            )

            except FileNotFoundError:
                # Изображение не найдено - добавляем в ошибки, но продолжаем
                error_msg = f"Изображение не найдено: {img_path_str}"
                self._errors.append(error_msg)
                if self.verbose:
                    print(f"    ✗ {error_msg}")
                # Удаляем временный файл, если был создан
                if temp_png_path and temp_png_path.exists():
                    temp_png_path.unlink()

            except Exception as e:
                # Другая ошибка при добавлении изображения
                error_msg = f"Ошибка добавления изображения {img_path_str}: {e}"
                self._errors.append(error_msg)
                if self.verbose:
                    print(f"    ✗ {error_msg}")
                # Удаляем временный файл, если был создан
                if temp_png_path and temp_png_path.exists():
                    temp_png_path.unlink()

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
        for layout in prs.slide_layouts:
            if layout.name == layout_name:
                return layout
        return None
