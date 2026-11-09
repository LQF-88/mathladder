PYTHON ?= .venv/bin/python
BUILDOZER ?= buildozer

.PHONY: help install run test lint fmt apk aab clean screenshots

help:
	@echo "install     安装桌面依赖（需要先创建 .venv）"
	@echo "run         在手机比例的窗口中运行应用"
	@echo "test        运行 pytest"
	@echo "lint        运行 ruff 检查"
	@echo "fmt         自动修复可修复的 lint 问题"
	@echo "apk         构建 Android debug APK（需 Linux/WSL + buildozer）"
	@echo "aab         构建 Android release AAB（需配置签名）"
	@echo "screenshots 生成文档截图（桌面）"
	@echo "clean       清理测试与构建缓存"

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

run:
	$(PYTHON) main.py

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check app main.py tests tools

fmt:
	$(PYTHON) -m ruff check app main.py tests tools --fix

apk:
	$(BUILDOZER) -v android debug

aab:
	$(BUILDOZER) -v android release

screenshots:
	$(PYTHON) tools/make_screenshots.py

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ app/__pycache__ app/*/__pycache__ \
		app/ui/screens/__pycache__ app/ui/widgets/__pycache__ tests/__pycache__
	rm -rf bin .buildozer build dist
