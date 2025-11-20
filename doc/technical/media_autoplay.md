# Автозапуск аудио в PowerPoint

## Проблема

`python-pptx` не предоставляет API для автоматического воспроизведения аудио при открытии слайда. Метод `add_movie()` добавляет медиа с `delay="indefinite"`, что требует ручного клика.

## Решение

Модифицируем XML-структуру PowerPoint OOXML напрямую, изменяя атрибут `delay` в timing элементе.

### Алгоритм (MediaPlacer._enable_autoplay)

1. **Добавляем аудио через `add_movie()`** — workaround для аудио
2. **Находим timing элемент** по `shape_id`:

   ```
   <p:timing>
     <p:video>
       <p:cMediaNode>
         <p:cTn>
           <p:stCondLst>
             <p:cond delay="indefinite"/> ← МЕНЯЕМ НА delay="0"
           </p:stCondLst>
         </p:cTn>
         <p:tgtEl>
           <p:spTgt spid="{shape_id}"/> ← ИЩЕМ ПО ЭТОМУ ID
         </p:tgtEl>
       </p:cMediaNode>
     </p:video>
   </p:timing>
   ```

3. **Навигация через python-pptx API**:

   ```python
   from pptx.oxml.ns import qn
   
   # Ищем <p:spTgt spid="{shape_id}">
   for video_elem in timing_element.iter(qn('p:video')):
       for sp_tgt in video_elem.iter(qn('p:spTgt')):
           if sp_tgt.get('spid') == str(shape_id):
               # Поднимаемся к <p:cond>
               c_media_node = sp_tgt.getparent().getparent()
               c_tn = c_media_node.find(qn('p:cTn'))
               st_cond_lst = c_tn.find(qn('p:stCondLst'))
               cond = st_cond_lst.find(qn('p:cond'))
               
               # ИЗМЕНЯЕМ delay
               cond.set('delay', '0')
   ```

## Почему НЕ работает xpath напрямую

`lxml.etree.Element.xpath()` требует namespace map, но `python-pptx` использует `BaseOxmlElement` с собственным API. Используем:

- `qn()` — для namespace-qualified names
- `.find()` / `.iter()` — для поиска элементов
- `.getparent()` — для навигации вверх по дереву

## Источник решения

GitHub issue [#427](https://github.com/scanny/python-pptx/issues/427) (@monstarnn, 2021)

## Файл реализации

`core/placers/media_placer.py` — метод `_enable_autoplay()`
