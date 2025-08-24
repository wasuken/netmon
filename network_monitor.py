import subprocess
import time
import sys
import os
import argparse
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from collections import defaultdict, deque


# カラーコード定義
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


# ping履歴保存用（各ホストごとに最大N回分）
ping_history = defaultdict(lambda: deque(maxlen=10))


def resolve_hostname(hostname):
    """ホスト名をIPアドレスに解決"""
    try:
        ip = socket.gethostbyname(hostname)
        return ip
    except socket.gaierror:
        return None


def resolve_all_hosts(hosts):
    """全ホスト名を事前にIPアドレスに解決"""
    print(f"{Colors.YELLOW}DNS解決中...{Colors.RESET}")
    host_ip_map = {}
    failed_hosts = []

    for host in hosts:
        print(f"  {host} -> ", end="", flush=True)
        ip = resolve_hostname(host)
        if ip:
            host_ip_map[host] = ip
            if ip == host:
                print(f"{Colors.CYAN}{ip}{Colors.RESET} (既にIPアドレス)")
            else:
                print(f"{Colors.CYAN}{ip}{Colors.RESET}")
        else:
            print(f"{Colors.RED}解決失敗{Colors.RESET}")
            failed_hosts.append(host)

    if failed_hosts:
        print(
            f"\n{Colors.RED}エラー: 以下のホストの名前解決に失敗しました: {', '.join(failed_hosts)}{Colors.RESET}"
        )
        sys.exit(1)

    print(f"{Colors.GREEN}DNS解決完了{Colors.RESET}\n")
    return host_ip_map


def ping_host(ip, timeout):
    """指定したIPにpingを送信して結果を返す"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["ping", "-n", "1", "-w", str(timeout * 1000), ip],
                capture_output=True,
                text=True,
                timeout=timeout + 1,
            )
        else:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", str(timeout), ip],
                capture_output=True,
                text=True,
                timeout=timeout + 1,
            )
        return result.returncode == 0
    except:
        return False


def check_all_hosts(hosts, host_ip_map, timeout):
    """並列でpingを送信し、履歴を記録"""
    with ThreadPoolExecutor(max_workers=len(hosts)) as executor:
        futures = {
            executor.submit(ping_host, host_ip_map[host], timeout): host
            for host in hosts
        }
        results = {}
        for future in futures:
            host = futures[future]
            try:
                result = future.result()
                results[host] = result
                # 履歴に追加
                ping_history[host].append(result)
            except:
                results[host] = False
                ping_history[host].append(False)
    return results


def get_success_rate(host):
    """指定ホストの成功率を計算"""
    history = ping_history[host]
    if not history:
        return 0, 0
    success_count = sum(1 for result in history if result)
    total_count = len(history)
    return success_count, total_count


def format_history_display(host):
    """履歴をチェックマーク形式で表示"""
    history = list(ping_history[host])
    if not history:
        return ""

    # 最新から順に表示（左が最新）
    symbols = []
    for result in reversed(history):
        if result:
            symbols.append(f"{Colors.GREEN}✓{Colors.RESET}")
        else:
            symbols.append(f"{Colors.RED}✗{Colors.RESET}")

    return " ".join(symbols)


def format_status(host, status, host_ip_map, checking=False):
    """ステータスをフォーマット"""
    if checking:
        color_status = f"{Colors.YELLOW}Ping送信中{Colors.RESET}"
    elif status is None:
        color_status = f"{Colors.YELLOW}初期化中{Colors.RESET}"
    elif status:
        color_status = f"{Colors.GREEN}疎通{Colors.RESET}"
    else:
        color_status = f"{Colors.RED}非接続{Colors.RESET}"

    # 成功率を計算
    success, total = get_success_rate(host)
    rate_display = (
        f"{Colors.CYAN}{success}/{total}{Colors.RESET}"
        if total > 0
        else f"{Colors.CYAN}0/0{Colors.RESET}"
    )

    # 履歴表示
    history_display = format_history_display(host)
    history_part = f" [{history_display}]" if history_display else ""

    # IPアドレス表示
    ip = host_ip_map.get(host, host)
    if ip != host:
        ip_part = f" ({Colors.CYAN}{ip}{Colors.RESET})"
    else:
        ip_part = ""

    return f"{Colors.CYAN}{host:<20}{Colors.RESET}{ip_part}: {color_status} ({rate_display}){history_part}"


def display_screen(hosts, results, host_ip_map, checking=False):
    """画面全体を表示"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_text = " [チェック中...]" if checking else ""

    print(
        f"{Colors.BOLD}[{current_time}]{Colors.RESET}{Colors.YELLOW}{status_text}{Colors.RESET}"
    )

    for host in hosts:
        status = results.get(host, None)
        print(format_status(host, status, host_ip_map, checking and status is not None))


def clear_lines(count):
    """指定した行数分カーソルを上に移動してクリア"""
    for _ in range(count):
        print("\033[A\033[K", end="")


def load_hosts_from_file(file_path):
    """ファイルからホストリストを読み込み"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            hosts = []
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    hosts.append(line)
            return hosts
    except FileNotFoundError:
        print(
            f"{Colors.RED}エラー: ファイル '{file_path}' が見つかりません{Colors.RESET}"
        )
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}エラー: ファイル読み込みに失敗しました: {e}{Colors.RESET}")
        sys.exit(1)


def parse_arguments():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description="Network Monitor CLI - シームレスなネットワーク監視ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python network_monitor.py 8.8.8.8 1.1.1.1
  python network_monitor.py -f hosts.txt
  python network_monitor.py -f hosts.txt 192.168.1.1
  python network_monitor.py -i 3 -t 2 8.8.8.8

ファイル形式例 (hosts.txt):
  8.8.8.8
  1.1.1.1
  google.com
  # コメント行は無視
        """,
    )

    parser.add_argument("hosts", nargs="*", help="監視するホスト/IPアドレス")
    parser.add_argument("-f", "--file", help="ホストリストファイル")
    parser.add_argument("-i", "--interval", type=int, default=2, help="更新間隔（秒）")
    parser.add_argument(
        "-t", "--timeout", type=int, default=2, help="Pingタイムアウト（秒）"
    )
    parser.add_argument(
        "-n",
        "--history",
        type=int,
        default=10,
        help="ping履歴保存数（1-10、デフォルト: 10）",
    )

    return parser.parse_args()


def get_hosts_list(args):
    """ホストリストを取得"""
    hosts = []

    if args.file:
        hosts.extend(load_hosts_from_file(args.file))

    if args.hosts:
        hosts.extend(args.hosts)

    if not hosts:
        print(f"{Colors.RED}エラー: 監視対象が指定されていません{Colors.RESET}")
        print("使用例: python network_monitor.py 8.8.8.8 1.1.1.1")
        sys.exit(1)

    return list(dict.fromkeys(hosts))  # 重複削除


def main():
    args = parse_arguments()
    hosts = get_hosts_list(args)

    # 履歴保存数の制限（1-10）
    history_size = max(1, min(10, args.history))

    # 各ホストの履歴サイズを設定
    for host in hosts:
        ping_history[host] = deque(maxlen=history_size)

    # 事前DNS解決
    host_ip_map = resolve_all_hosts(hosts)

    print(f"{Colors.BOLD}{Colors.MAGENTA}=== Network Monitor CLI ==={Colors.RESET}")
    print(f"{Colors.YELLOW}監視対象: {', '.join(hosts)}{Colors.RESET}")
    print(
        f"{Colors.YELLOW}間隔: {args.interval}秒 | タイムアウト: {args.timeout}秒 | 履歴: {history_size}回{Colors.RESET}"
    )
    print(f"{Colors.YELLOW}Ctrl+C で終了{Colors.RESET}\n")

    results = {}  # 結果保存用
    line_count = len(hosts) + 1  # 表示する行数

    try:
        while True:
            # チェック中表示
            display_screen(hosts, results, host_ip_map, checking=True)

            # ping実行
            new_results = check_all_hosts(hosts, host_ip_map, args.timeout)
            results.update(new_results)

            # 結果表示に更新
            clear_lines(line_count)
            display_screen(hosts, results, host_ip_map, checking=False)

            # 待機
            time.sleep(args.interval)

            # 次回更新の準備
            clear_lines(line_count)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}監視を終了します{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
