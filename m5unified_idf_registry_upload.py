#!/usr/bin/env python3
"""
M5Unified idf component registry 发版脚本
"""

import os
import subprocess
import sys
import json

TARGET_REPO = "git@github.com:Forairaaaaa/M5Unified.git"
WORKFLOW_PATH = ".github/workflows/main.yml"
UPLOAD_BRANCH_NAME = "idf-component-registry-upload"

# 全局变量存储workflow内容
workflow_content = None

# 全局变量存储版本号
m5unified_version = None
m5gfx_version = None


def run_command(cmd, cwd=None):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True, cwd=cwd
        )
        print(f"✓ 执行成功: {cmd}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"✗ 执行失败: {cmd}")
        print(f"错误信息: {e.stderr}")
        return None


def clone_repository():
    """第一步：拉取仓库"""
    repo_url = TARGET_REPO
    repo_name = "M5Unified"

    print("=== 步骤1：拉取仓库 ===")

    print(f"正在克隆仓库: {repo_url}")
    result = run_command(f"git clone {repo_url}")
    if result is not None:
        os.chdir(repo_name)
        print(f"已进入仓库目录: {os.getcwd()}")

    if result is not None:
        print("✓ 仓库拉取成功！")
        return True
    else:
        print("✗ 仓库拉取失败！")
        return False


def read_workflow_file():
    """第二步：读取.github/workflows/main.yml内容"""
    print("=== 步骤2：读取workflow文件 ===")

    workflow_path = WORKFLOW_PATH

    if not os.path.exists(workflow_path):
        print(f"✗ 文件不存在: {workflow_path}")
        return None

    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"✓ 成功读取workflow文件，内容长度: {len(content)} 字符")
        return content
    except Exception as e:
        print(f"✗ 读取workflow文件失败: {e}")
        return None


def create_upload_branch():
    """第三步：从master分支创建并切换到upload分支"""
    print("=== 步骤3：从master分支创建upload分支 ===")

    # 首先切换到master分支
    print("切换到master分支...")
    result = run_command("git checkout master")
    if result is None:
        # 如果master分支不存在，尝试main分支
        print("master分支不存在，尝试main分支...")
        result = run_command("git checkout main")
        if result is None:
            print("✗ 无法找到master或main分支！")
            return False

    # 删除已存在的upload分支（如果存在）
    existing_branches = run_command("git branch")
    if existing_branches and UPLOAD_BRANCH_NAME in existing_branches:
        print("删除已存在的upload分支...")
        run_command(f"git branch -D {UPLOAD_BRANCH_NAME}")

    # 创建新的upload分支
    print("从当前分支创建upload分支...")
    result = run_command(f"git checkout -b {UPLOAD_BRANCH_NAME}")

    if result is not None:
        print("✓ 成功从master分支创建upload分支！")
        return True
    else:
        print("✗ 创建upload分支失败！")
        return False


def read_version_info():
    """第四步：从library.json中读取版本号信息"""
    print("=== 步骤4：读取版本号信息 ===")

    library_path = "library.json"

    if not os.path.exists(library_path):
        print(f"✗ 文件不存在: {library_path}")
        return None, None

    try:
        with open(library_path, "r", encoding="utf-8") as f:
            library_data = json.load(f)

        # 读取自己的版本号
        m5unified_ver = library_data.get("version")
        if not m5unified_ver:
            print("✗ 未找到M5Unified版本号")
            return None, None

        print(f"✓ M5Unified版本号: {m5unified_ver}")

        # 读取M5GFX依赖版本号
        dependencies = library_data.get("dependencies", [])
        m5gfx_ver = None

        for dep in dependencies:
            if dep.get("name") == "M5GFX":
                m5gfx_ver = dep.get("version")
                break

        if not m5gfx_ver:
            print("✗ 未找到M5GFX依赖版本号")
            return None, None

        print(f"✓ M5GFX依赖版本号: {m5gfx_ver}")

        return m5unified_ver, m5gfx_ver

    except json.JSONDecodeError as e:
        print(f"✗ JSON解析错误: {e}")
        return None, None
    except Exception as e:
        print(f"✗ 读取library.json失败: {e}")
        return None, None


def write_workflow_file():
    """第五步：把workflow内容写回到相同路径"""
    print("=== 步骤5：写入workflow文件 ===")

    global workflow_content

    if workflow_content is None:
        print("✗ 没有可用的workflow内容")
        return False

    workflow_path = WORKFLOW_PATH
    workflow_dir = os.path.dirname(workflow_path)

    try:
        # 创建目录（如果不存在）
        if not os.path.exists(workflow_dir):
            print(f"创建目录: {workflow_dir}")
            os.makedirs(workflow_dir, exist_ok=True)

        # 写入workflow内容
        with open(workflow_path, "w", encoding="utf-8") as f:
            f.write(workflow_content)

        print(f"✓ 成功写入workflow文件: {workflow_path}")
        print(f"✓ 文件大小: {len(workflow_content)} 字符")
        return True

    except Exception as e:
        print(f"✗ 写入workflow文件失败: {e}")
        return False


def convert_pio_version_to_idf(pio_version):
    """将PIO版本格式转换为IDF Component Register格式"""
    if not pio_version:
        return None

    # 移除空格
    version = pio_version.strip()

    # 如果已经有^前缀，直接使用
    if version.startswith("^"):
        return version

    # 如果有~前缀，转换为^前缀
    if version.startswith("~"):
        return "^" + version[1:]

    # 如果有>=前缀，转换为^前缀
    if version.startswith(">="):
        return "^" + version[2:]

    # 如果有>前缀，转换为^前缀
    if version.startswith(">"):
        return "^" + version[1:]

    # 如果有=前缀，去掉=
    if version.startswith("="):
        version = version[1:]

    # 如果是纯数字版本号，添加^前缀
    if version.replace(".", "").replace("-", "").replace("_", "").isalnum():
        return "^" + version

    # 其他情况保持原样
    return version


def create_idf_component():
    """第六步：创建idf_component.yml文件"""
    print("=== 步骤6：创建idf_component.yml文件 ===")

    global m5unified_version, m5gfx_version

    if m5unified_version is None or m5gfx_version is None:
        print("✗ 版本号信息不完整")
        return False

    # 转换M5GFX版本号格式（从PIO格式转换为IDF格式）
    m5gfx_version_formatted = convert_pio_version_to_idf(m5gfx_version)
    if m5gfx_version_formatted is None:
        print("✗ M5GFX版本号转换失败")
        return False

    print(f"版本号转换: {m5gfx_version} -> {m5gfx_version_formatted}")

    # 生成idf_component.yml内容
    idf_content = f"""description: Unified library for M5Stack series
issues: https://github.com/m5stack/M5Unified/issues
repository: https://github.com/m5stack/M5Unified.git
url: https://github.com/m5stack/M5Unified.git
version: {m5unified_version}

dependencies:
  m5stack/m5gfx:
    version: "{m5gfx_version_formatted}"
"""

    idf_path = "idf_component.yml"

    try:
        with open(idf_path, "w", encoding="utf-8") as f:
            f.write(idf_content)

        print("✓ 成功创建idf_component.yml文件")
        print(f"✓ M5Unified版本: {m5unified_version}")
        print(f"✓ M5GFX依赖版本: {m5gfx_version_formatted}")
        return True

    except Exception as e:
        print(f"✗ 创建idf_component.yml文件失败: {e}")
        return False


def update_cmake_file():
    """第七步：把CMakeLists.txt中的M5GFX改成m5gfx"""
    print("=== 步骤7：更新CMakeLists.txt文件 ===")

    cmake_path = "CMakeLists.txt"

    if not os.path.exists(cmake_path):
        print(f"✗ 文件不存在: {cmake_path}")
        return False

    try:
        # 读取原文件内容
        with open(cmake_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 统计替换次数
        count_before = content.count("M5GFX")

        if count_before == 0:
            print("✓ 未发现需要替换的M5GFX")
            return True

        # 替换M5GFX为m5gfx
        new_content = content.replace("M5GFX", "m5gfx")

        # 写回文件
        with open(cmake_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print("✓ 成功更新CMakeLists.txt文件")
        print(f"✓ 共替换了 {count_before} 处 M5GFX -> m5gfx")
        return True

    except Exception as e:
        print(f"✗ 更新CMakeLists.txt文件失败: {e}")
        return False


def commit_and_push():
    """第八步：提交并推送更改"""
    print("=== 步骤8：提交并推送更改 ===")

    global m5unified_version

    if m5unified_version is None:
        print("✗ 版本号信息不完整")
        return False

    try:
        # 添加所有更改到暂存区
        print("添加文件到暂存区...")
        result = run_command("git add .")
        if result is None:
            print("✗ 添加文件到暂存区失败")
            return False

        # 检查是否有文件被暂存
        status_result = run_command("git diff --cached --name-only")
        if not status_result:
            print("✓ 没有需要提交的更改")
            return True

        # 生成commit消息
        commit_message = f"idf component registry upload, version {m5unified_version}"

        # 提交更改
        print(f"提交更改: {commit_message}")
        result = run_command(f'git commit -m "{commit_message}"')
        if result is None:
            print("✗ 提交更改失败")
            return False

        # 推送到远程仓库
        print("推送到远程仓库...")
        result = run_command(f"git push origin {UPLOAD_BRANCH_NAME}")
        if result is None:
            print("✗ 推送到远程仓库失败")
            return False

        print("✓ 成功提交并推送更改")
        print(f"✓ Commit消息: {commit_message}")
        return True

    except Exception as e:
        print(f"✗ 提交并推送更改失败: {e}")
        return False


def main():
    """主函数"""
    global workflow_content, m5unified_version, m5gfx_version
    print("开始执行 M5Unified 发版脚本...")

    try:
        # 第一步：拉取仓库
        if not clone_repository():
            raise Exception("拉取仓库失败")

        # 第二步：读取workflow文件内容
        workflow_content = read_workflow_file()
        if workflow_content is None:
            raise Exception("读取workflow文件失败")

        # 第三步：从master分支创建并切换到upload分支
        if not create_upload_branch():
            raise Exception("创建upload分支失败")

        # 第四步：读取版本号信息
        m5unified_version, m5gfx_version = read_version_info()
        if m5unified_version is None or m5gfx_version is None:
            raise Exception("读取版本号信息失败")

        # 第五步：写入workflow文件
        if not write_workflow_file():
            raise Exception("写入workflow文件失败")

        # 第六步：创建idf_component.yml文件
        if not create_idf_component():
            raise Exception("创建idf_component.yml文件失败")

        # 第七步：更新CMakeLists.txt文件
        if not update_cmake_file():
            raise Exception("更新CMakeLists.txt文件失败")

        # 第八步：提交并推送更改
        if not commit_and_push():
            raise Exception("提交并推送更改失败")

        print("所有步骤完成！发版脚本执行成功！🎉")

    except Exception as e:
        print(f"发版脚本执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
