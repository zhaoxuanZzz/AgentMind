# UV 使用指南

本项目已支持使用 [uv](https://github.com/astral-sh/uv) 作为 Python 包管理器。uv 是一个极快的 Python 包安装器和解析器，用 Rust 编写。

## 安装 uv

### Linux/macOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 使用 pip 安装
```bash
pip install uv
```

## 快速开始

### 1. 初始化虚拟环境（如果使用 uv）

```bash
cd backend
uv venv
```

### 2. 安装依赖

使用 `pyproject.toml`（推荐）：
```bash
uv sync
```

或使用 `requirements.txt`：
```bash
uv pip install -r requirements.txt
```

### 3. 运行项目

使用 uv 运行：
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或使用项目提供的脚本（自动检测 uv）：
```bash
./run-backend.sh
```

## 常用命令

### 安装依赖
```bash
# 同步所有依赖（从 pyproject.toml）
uv sync

# 安装单个包
uv add package-name

# 安装开发依赖
uv add --dev pytest
```

### 运行命令
```bash
# 在虚拟环境中运行命令
uv run python script.py
uv run uvicorn app.main:app
```

### 更新依赖
```bash
# 更新所有依赖
uv sync --upgrade

# 更新特定包
uv add package-name@latest
```

### 查看依赖
```bash
# 查看依赖树
uv tree
```

## 项目结构

- `pyproject.toml` - 项目配置和依赖定义（uv 推荐使用）
- `requirements.txt` - 传统依赖文件（保持兼容性）
- `.python-version` - Python 版本指定（3.11）

## 优势

1. **极快的安装速度** - 比 pip 快 10-100 倍
2. **自动管理虚拟环境** - 无需手动创建和激活
3. **更好的依赖解析** - 更快的依赖解析和冲突检测
4. **兼容 pip** - 可以使用 `uv pip` 命令替代 pip

## 与现有工作流的兼容性

- ✅ 支持 `requirements.txt`（通过 `uv pip install -r requirements.txt`）
- ✅ 支持 `pyproject.toml`（通过 `uv sync`）
- ✅ `run-backend.sh` 脚本会自动检测并使用 uv（如果已安装）
- ✅ 保持与 pip、venv 的兼容性

## 迁移说明

项目已同时支持 `pyproject.toml` 和 `requirements.txt`：
- 新用户推荐使用 `uv sync`（基于 `pyproject.toml`）
- 现有用户可继续使用 `pip install -r requirements.txt`

## 更多信息

- [uv 官方文档](https://github.com/astral-sh/uv)
- [uv 快速开始](https://docs.astral.sh/uv/)

