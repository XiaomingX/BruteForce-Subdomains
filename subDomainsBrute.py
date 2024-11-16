import os
import socket
import threading
import time
import ssl
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
    检查子域名是否存在
    """
    try:
        socket.gethostbyname(subdomain)
        return True
    except socket.gaierror:
        return False

def check_https_certificate(subdomain):
    """
    检查HTTPS证书信息
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((subdomain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=subdomain) as secure_sock:
                cert = secure_sock.getpeercert()
                return {
                    'subject': dict(x[0] for x in cert['subject']),
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'notBefore': cert['notBefore'],
                    'notAfter': cert['notAfter']
                }
    except Exception as e:
        return None

def analyze_timing(start_time, end_time, domain_count, found_count):
    """
    分析总用时和每个域名的平均用时
    """
    total_time = end_time - start_time
    avg_time = total_time / domain_count if domain_count > 0 else 0
    print(f"\n总检查子域名数: {domain_count}")
    print(f"发现的子域名数: {found_count}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"平均每个域名耗时: {avg_time:.2f} 秒")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='子域名扫描器')
    parser.add_argument('domain', type=str, nargs='?', default='qq.com', 
                       help='要扫描的域名 (默认: qq.com)')
    args = parser.parse_args()
    domain = args.domain

    prefixes = load_next_subs(filename="next_sub.txt")
    output = []
    cert_results = {}
    output_lock = threading.Lock()

    def process_subdomain(prefix):
        subdomain = f"{prefix}.{domain}"
        if check_subdomain_exists(subdomain):
            cert_info = check_https_certificate(subdomain)
            with output_lock:
                output.append(subdomain)
                if cert_info:
                    cert_results[subdomain] = cert_info

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        executor.map(process_subdomain, prefixes)

    end_time = time.time()

    # 保存结果
    os.makedirs('out', exist_ok=True)
    output_file = os.path.join('out', f'{domain}.txt')
    cert_file = os.path.join('out', f'{domain}_certs.txt')

    # 保存子域名
    with open(output_file, 'w') as file:
        for subdomain in output:
            print(subdomain)
            file.write(subdomain + '\n')

    # 保存证书信息
    with open(cert_file, 'w') as file:
        for subdomain, cert_info in cert_results.items():
            file.write(f"{subdomain}\n")
            # file.write(f"证书主题: {cert_info['subject']}\n")
            # file.write(f"证书颁发者: {cert_info['issuer']}\n")
            # file.write(f"有效期始: {cert_info['notBefore']}\n")
            # file.write(f"有效期止: {cert_info['notAfter']}\n")
            # file.write("-" * 50 + "\n")

    print("\n=========================扫描统计=========================")
    analyze_timing(start_time, end_time, len(prefixes), len(output))
    print(f"\n发现的子域名已保存到: {output_file}")
    print(f"证书信息已保存到: {cert_file}")

if __name__ == '__main__':
    main()