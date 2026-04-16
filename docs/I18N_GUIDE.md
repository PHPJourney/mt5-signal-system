# TradeMind MT5 多语言支持

## 概述

TradeMind MT5 系统提供完整的多语言支持，包括：
- Windows 安装包（NSIS）
- Python GUI 管理面板

## 语言文件结构

### 1. NSIS 安装包语言文件

位置：`lang/Chinese.nsh` 和 `lang/English.nsh`

这些文件用于 Windows 安装程序的界面文本。

**文件格式：**
```nsis
LangString KEY_NAME ${LANG_SIMPCHINESE} "中文文本"
LangString KEY_NAME ${LANG_ENGLISH} "English text"

