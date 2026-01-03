# AI 文件自動命名整理 (AI PDF Renamer)

這是一個基於 Google Gemini AI 的自動化工具，專門設計用於整理和重命名 PDF 研究報告或文檔。

它能夠智能識別 PDF 封面內容，提取關鍵信息（行業、市場範圍、機構來源、日期），並自動生成精簡有力的**中文標題**，最後按統一格式重命名並歸檔。

## ✨ 主要功能

*   **AI 智能識別**：利用 Gemini 2.0 Flash 模型精準識別封面信息。
*   **中文語義理解**：不只是翻譯，AI 會理解報告內容並生成易讀的繁體中文標題。
*   **標準化命名**：格式統一為 `行業-地域-中文標題-機構-日期` (例如: `AI-WW-生成式AI未來展望-MS-250916.pdf`)。
*   **批量處理**：一鍵掃描並處理目錄下的所有 PDF 文件。
*   **安全預覽**：提供 Dry Run 模式，先預覽重命名結果，滿意後再執行。

## 🚀 快速開始

### 1. 安裝依賴
確保已安裝 Python，然後運行：
```bash
pip install -r requirements.txt
```

### 2. 初始化目錄
創建 `未整理` 和 `已整理` 文件夾：
```bash
python setup_folders.py
```

### 3. 配置環境變量
在項目根目錄創建 `.env` 文件，並填入你的 Gemini API Key：
```env
GEMINI_API_KEY=your_api_key_here
```

### 4. 使用方法

**步驟 1**：將 PDF 文件放入 `未整理` 文件夾。

**步驟 2**：運行程序進行預覽（不會修改文件）：
```bash
python pdf_renamer.py
```

**步驟 3**：確認無誤後，執行重命名並移動到 `已整理` 文件夾：
```bash
python pdf_renamer.py --execute
```

## 🛠️ 技術棧

*   [Python](https://www.python.org/)
*   [Google Gemini API](https://ai.google.dev/) (Generative AI)
*   [PyMuPDF](https://pymupdf.readthedocs.io/) (PDF Processing)

## 📄 命名規則詳解

生成的文件名遵循以下格式：
`[行業應用]-[市場範圍]-[智能摘要標題]-[機構來源]-[日期]`

*   **行業應用**: 如 AI, ADAS, Semi, Auto (AI 自動提取)
*   **市場範圍**: WW (全球) 或 CN (中國)
*   **智能摘要**: AI 生成的精簡繁體中文標題
*   **機構來源**: 縮寫，如 MS (Morgan Stanley), GS (Goldman Sachs)
*   **日期**: YYMMDD 格式 (如 231025)

---
*Created by Antigravity*
