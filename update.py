# -- coding:utf-8 --
"""
User: ww
Version: 3.8
Date: 2025/2/7 9:36
File: update.py
"""
import os
import requests
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 远程 URL 和本地路径
remote_base_url = "http://192.168.2.225:8000/AutoTest/"

# 需要忽略更新的文件或路径列表
ignore_files = [
    'update.exe',  # 文件名匹配
]

# 获取远程目录的文件列表
def get_remote_file_list(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # 假设所有文件都以 <a> 标签的 href 属性出现
        file_list = [a['href'] for a in soup.find_all('a', href=True)]
        return file_list
    else:
        print(f"无法访问远程目录 {url}")
        return []

# 计算文件的哈希值
def calculate_file_hash(filepath, hash_algorithm='sha256'):
    hash_func = hashlib.new(hash_algorithm)
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hash_func.update(chunk)
    return hash_func.hexdigest()

# 下载文件并保存到本地
def download_file(remote_url, local_filepath):
    response = requests.get(remote_url, stream=True)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(local_filepath), exist_ok=True)  # 确保目录存在
        with open(local_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"已下载并保存文件: {local_filepath}")
    else:
        print(f"下载失败: {remote_url}")

# 规范化路径，防止 `../` 导致错误
def safe_join(base_path, *paths):
    # 先拼接路径，再使用 normpath 规范化
    combined_path = os.path.join(base_path, *paths)
    return os.path.normpath(combined_path)

# 比较本地文件和远程文件的哈希值
def is_file_updated(remote_url, local_filepath, hash_algorithm='sha256'):
    try:
        # 获取远程文件内容并计算哈希
        remote_response = requests.get(remote_url, stream=True)
        if remote_response.status_code != 200:
            return False  # 如果下载失败，则不更新

        remote_hash = hashlib.new(hash_algorithm)
        for chunk in remote_response.iter_content(chunk_size=8192):
            remote_hash.update(chunk)
        remote_hash_value = remote_hash.hexdigest()

        # 如果本地文件存在，计算本地文件的哈希
        if os.path.exists(local_filepath):
            local_hash_value = calculate_file_hash(local_filepath, hash_algorithm)
            return remote_hash_value != local_hash_value  # 如果哈希不同，则需要更新
        else:
            return True  # 如果本地文件不存在，直接下载
    except Exception as e:
        print(f"检查文件差异时出错: {e}")
        return True  # 出现错误时，默认需要更新文件

# 递归下载文件
def download_files_recursively(remote_url, local_dir):
    file_list = get_remote_file_list(remote_url)

    for file_name in file_list:
        # 检查文件是否需要忽略
        if any(ignored in file_name for ignored in ignore_files):
            print(f"忽略文件: {file_name}")
            continue

        # 过滤掉包含 '../' 的文件名
        if '../' in file_name:
            print(f"忽略无效文件名: {file_name}")
            continue

        # 使用 urljoin 来正确拼接 URL
        remote_file_url = urljoin(remote_url, file_name)
        local_file_path = safe_join(local_dir, file_name)

        # 调试输出文件路径
        # print(f"检查文件路径:\nRemote URL: {remote_file_url}\nLocal Path: {local_file_path}")

        # 如果是目录，递归处理
        if remote_file_url.endswith('/'):
            os.makedirs(local_file_path, exist_ok=True)
            download_files_recursively(remote_file_url, local_file_path)
        else:
            # 检查文件是否需要更新
            if is_file_updated(remote_file_url, local_file_path):
                download_file(remote_file_url, local_file_path)

if __name__ == "__main__":

    local_base_dir = os.getcwd() + '/'
    # 确保本地目标目录存在
    os.makedirs(local_base_dir, exist_ok=True)
    # 执行递归文件下载和替换操作
    download_files_recursively(remote_base_url, local_base_dir)





