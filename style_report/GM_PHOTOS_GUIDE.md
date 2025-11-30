# GM照片集成指南 (GM Photos Integration Guide)

## 概述 (Overview)

棋手报告现在会自动显示与玩家风格最相似的三位大师(GM)的照片。照片会显示在报告顶部的"Player Overview"部分。

## 功能特点 (Features)

### 1. 自动提取GM相似度
系统会从"Overall Synthesis"部分的LLM分析文本中自动提取以下信息：
- GM名字
- 相似度百分比
- 匹配对应的GM照片

### 2. 支持的GM照片
当前已集成以下GM的照片：
- **Tigran Petrosian** (`Petrosian.jpg`)
- **Garry Kasparov** (`Kasparov.jpg`)
- **Mikhail Tal** (`Tal.jpg`)
- **Bobby Fischer** (`Fischer.jpg`)

照片存储位置：`style_report/assets/gm_photos/`

### 3. 文本格式识别
系统支持以下文本格式来提取GM相似度：

```
✅ Tigran Petrosian (85%)
✅ similar to Anatoly Karpov (72%)
✅ Bobby Fischer: 68%
✅ resembles Mikhail Tal 75%
```

### 4. 默认显示
如果LLM文本中没有找到足够的GM相似度信息，系统会显示默认的三位GM：
- Tigran Petrosian (带照片)
- Anatoly Karpov (显示缩写"AK")
- Bobby Fischer (带照片)

## 添加新GM照片 (Adding New GM Photos)

### 步骤1: 准备照片
1. 照片格式：JPG或PNG
2. 建议尺寸：至少200x200像素
3. 照片应为正方形或可裁剪为正方形的肖像照

### 步骤2: 复制照片到assets文件夹
```bash
cp "path/to/gm_photo.jpg" "style_report/assets/gm_photos/GMName.jpg"
```

例如：
```bash
cp "Karpov_photo.jpg" "style_report/assets/gm_photos/Karpov.jpg"
```

### 步骤3: 更新report_builder.py
在 `_extract_gm_similarities()` 函数中添加新的GM照片映射：

```python
gm_photos = {
    # ... 现有的映射 ...
    "new gm name": "NewGM.jpg",
    "newgm": "NewGM.jpg",  # 简短版本
}
```

例如添加Karpov：
```python
gm_photos = {
    # ... existing entries ...
    "anatoly karpov": "Karpov.jpg",
    "karpov": "Karpov.jpg",
}
```

## 技术细节 (Technical Details)

### CSS样式
GM头像使用圆形显示，带有灰色边框：
```css
.gm-avatar {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  overflow: hidden;
  border: 2px solid #d1d5db;
}

.gm-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

### HTML结构
```html
<div class="gm-strip">
  <div class="gm-card">
    <div class="gm-avatar">
      <img src="../../assets/gm_photos/Petrosian.jpg" alt="Tigran Petrosian" />
    </div>
    <div>
      <div class="gm-name">Tigran Petrosian</div>
      <div class="gm-score">Similarity: 85%</div>
    </div>
  </div>
  <!-- 更多GM卡片 -->
</div>
```

### 文件路径说明
- GM照片目录：`style_report/assets/gm_photos/`
- CSS文件：`style_report/assets/report.css`
- HTML模板：`style_report/templates/report_base.html`
- Python逻辑：`style_report/scripts/report_builder.py`

## LLM提示词建议 (LLM Prompt Recommendations)

为了让系统能够准确提取GM相似度，建议在"Overall Synthesis"的LLM提示词中包含类似以下的指示：

```
Please identify the top 3 most similar grandmasters to this player and
include their names with similarity percentages in the format:
"This player's style is most similar to GM Name (XX% similarity), ..."
```

或中文版本：
```
请识别与该玩家风格最相似的前3位大师，并以以下格式包含姓名和相似度百分比：
"该玩家的风格最接近 GM姓名 (XX%相似度)，..."
```

## 故障排除 (Troubleshooting)

### 问题：照片不显示
**可能原因：**
1. 照片文件路径错误
2. 照片文件名在`gm_photos`映射中不存在
3. LLM文本格式不匹配正则表达式

**解决方案：**
1. 检查照片是否存在于 `style_report/assets/gm_photos/` 目录
2. 确认文件名与代码中的映射一致（区分大小写）
3. 查看生成的HTML中的GM卡片部分，检查是否使用了默认值

### 问题：显示的是缩写而不是照片
**原因：** 系统没有找到对应的照片文件

**解决方案：**
1. 为该GM添加照片文件
2. 更新 `gm_photos` 映射

### 问题：相似度百分比不正确
**原因：** LLM文本格式可能不符合预期

**解决方案：**
1. 检查"Overall Synthesis"部分的文本内容
2. 确保使用支持的格式之一（见"文本格式识别"部分）
3. 如需要，更新 `_extract_gm_similarities()` 函数中的正则表达式

## 示例 (Examples)

### 完整的LLM输出示例
```
This player exhibits a sophisticated positional style most similar to
Tigran Petrosian (85% similarity), combining prophylactic thinking with
strategic maneuvering. Secondary influences include Anatoly Karpov (72% similarity)
in endgame technique and Bobby Fischer (68% similarity) in tactical precision.
```

这段文本会被自动解析为：
- GM 1: Tigran Petrosian - 85%
- GM 2: Anatoly Karpov - 72%
- GM 3: Bobby Fischer - 68%

## 未来扩展 (Future Extensions)

可以考虑添加更多GM照片：
- Anatoly Karpov
- Vladimir Kramnik
- Magnus Carlsen
- Levon Aronian
- Veselin Topalov
- Alexander Alekhine
- Jose Raul Capablanca
- Emanuel Lasker

只需按照"添加新GM照片"部分的步骤操作即可。
