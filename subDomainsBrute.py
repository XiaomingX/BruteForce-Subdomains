import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# 最大线程数
MAX_THREADS = 1000

def load_next_subs(filename="next_sub.txt"):
    """
    从 dict/next_sub.txt 中读取子域名的前缀
    """
    next_subs_path = os.path.join('dict', filename)
    if os.path.exists(next_subs_path):
        with open(next_subs_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    return []

def check_subdomain_exists(subdomain):
    """
    求试子域名是否存在
    """
    try:
        socket.gethostbyname(subdomain)
        return True
    except socket.gaierror:
        return False

def analyze_timing(start_time, end_time, domain_count, found_count):
    """
    分析总用时和每个域名的平均用时
    """
    total_time = end_time - start_time
    avg_time = total_time / domain_count if domain_count > 0 else 0
    print(f"\nTotal subdomains checked: {domain_count}")
    print(f"Total subdomains found: {found_count}")
    print(f"Total time taken: {total_time:.2f} seconds")
    print(f"Average time per domain: {avg_time:.2f} seconds")

import argparse

def main():
    # 解析用户输入的域名
    parser = argparse.ArgumentParser(description='Subdomain Scanner')

    ## 在这里扫描子域名
    parser.add_argument('domain', type=str, nargs='?', default='taobao.com', help='The domain to scan subdomains for (default: taobao.com)')

    args = parser.parse_args()
    domain = args.domain if args.domain else 'qq.com'
    # 读取子域前缀
    prefixes = load_next_subs(filename="next_sub_full.txt")
    output = []
    output_lock = threading.Lock()

    def process_prefix(prefix):
        subdomain = f"{prefix}.{domain}"
        if check_subdomain_exists(subdomain):
            with output_lock:
                output.append(subdomain)

    # 开始计时
    start_time = time.time()

    # 使用多线程来验证子域名
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        executor.map(process_prefix, prefixes)

    # 结束计时
    end_time = time.time()

    # 将结果打印到屏幕上并保存到文件
    output_file = os.path.join('out', f'{domain}.txt')
    os.makedirs('out', exist_ok=True)
    with open(output_file, 'w') as file:
        for subdomain in output:
            print(subdomain)
            file.write(subdomain + '\n')

    print()
    print(f"=========================用时统计=========================")
    # 分析用时
    analyze_timing(start_time, end_time, len(prefixes), len(output))

if __name__ == '__main__':
    main()