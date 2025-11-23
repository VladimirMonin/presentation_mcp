# YouTube Shorts Template — Important Notes

## 📱 Template Status

The `youtube_base_shorts.pptx` template file exists with the correct dimensions (19.05 cm x 33.87 cm, vertical 9:16 format), but currently **lacks placeholders** for title and slide number.

## ⚠️ Current Limitation

To use the Shorts layouts fully, the template needs to be updated in PowerPoint to add placeholders. This is because the presentation builder expects to find placeholders at specific indices to insert:
- Title text (recommended idx: 10)
- Slide number (recommended idx: 11)

## 🔧 How to Fix (Manual Update Required)

1. Open `templates/youtube_base_shorts.pptx` in PowerPoint
2. Go to **View → Slide Master**
3. Select the **ShortsLayout** layout
4. Add two text placeholders:
   - Title placeholder (will auto-assign idx: 10)
   - Slide number placeholder (will auto-assign idx: 11)
5. Position them appropriately:
   - Title: top of slide (~0-2.5 cm from top)
   - Slide number: corner or bottom of slide
6. Save the template

## 📋 Layout Blueprints

The following layout blueprints have been registered and are ready to use once the template has placeholders:

### `single_tall_shorts`
- **Images:** 1
- **Position:** left=1.5 cm, top=3.0 cm
- **Max size:** 16.05 x 29.87 cm
- **Use case:** Full-screen vertical images

### `two_stack_shorts`
- **Images:** 2
- **Positions:** 
  - Top: left=1.5 cm, top=3.0 cm (16.05 x 14.43 cm)
  - Bottom: left=1.5 cm, top=18.43 cm (16.05 x 14.43 cm)
- **Gap:** 1.0 cm
- **Use case:** Before/after comparisons, two-step tutorials

### `three_stack_shorts`
- **Images:** 3
- **Positions:**
  - Top: left=1.5 cm, top=3.0 cm (16.05 x 9.42 cm)
  - Middle: left=1.5 cm, top=13.22 cm (16.05 x 9.42 cm)
  - Bottom: left=1.5 cm, top=23.45 cm (16.05 x 9.42 cm)
- **Gap:** 0.8 cm
- **Use case:** Three-step tutorials, sequential content

## 🎯 Workaround

Until the template is updated with placeholders, you can:
1. Use the layouts for image placement (which will work)
2. Manually add titles and slide numbers in PowerPoint after generation
3. Or use a different template that has placeholders and adjust the slide size

## 📚 Documentation

- Layout documentation: `doc/layouts/single_tall_shorts.md`, `two_stack_shorts.md`, `three_stack_shorts.md`
- Example configuration: `doc/samples/youtube_shorts_example.json`
- Constants defined in: `config/settings.py`

---

**Next Steps:** Update the PowerPoint template to add placeholders following the guide in `doc/TEMPLATE_GUIDE.md`
