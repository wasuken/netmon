# Network Monitor CLI

シンプルなネットワーク監視ツール。複数のホストに対してpingを送信し、リアルタイムで疎通状況を表示します。

## 特徴

- リアルタイムでの疎通監視
- 成功率の表示（X/N形式）
- ping履歴の視覚表示（✓/✗）
- 事前DNS解決による高速化
- シームレスな画面更新

## 必要環境

- Python 3.6以上
- ping コマンド（通常はOSに標準搭載）

## 使用方法

### 基本的な使い方

```bash
# ホストを直接指定
python network_monitor.py 8.8.8.8 1.1.1.1 google.com

# ファイルから読み込み
python network_monitor.py -f hosts.txt

# ファイル + 追加ホスト
python network_monitor.py -f hosts.txt 192.168.1.1
```

### オプション

```bash
python network_monitor.py [オプション] [ホスト...]

  -f, --file       ホストリストファイルのパス
  -i, --interval   更新間隔（秒、デフォルト: 2）
  -t, --timeout    Pingタイムアウト（秒、デフォルト: 2）
  -n, --history    ping履歴保存数（1-10、デフォルト: 10）
  -h, --help       ヘルプを表示
```

### ホストファイルの形式

```
# hosts.txt の例
8.8.8.8
1.1.1.1
google.com
server.example.com
# この行はコメントなので無視される
192.168.1.100
```

## 表示例

```
=== Network Monitor CLI ===
監視対象: server1, server2, google.com
間隔: 2秒 | タイムアウト: 2秒 | 履歴: 10回
Ctrl+C で終了

[2024-08-24 12:30:45]
server1             (192.168.1.10): 疎通 (8/10) [✓ ✓ ✗ ✓ ✓ ✓ ✗ ✓ ✓ ✓]
server2             (192.168.1.20): 疎通 (10/10) [✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓]
google.com          (172.217.175.78): 非接続 (2/10) [✗ ✗ ✗ ✓ ✗ ✗ ✗ ✓ ✗ ✗]
```

## 表示の見方

- **疎通/非接続**: 現在の接続状態
- **(X/N)**: 成功回数/総試行回数
- **[✓ ✗ ✓...]**: ping履歴（左が最新、✓=成功、✗=失敗）
- **[チェック中...]**: ping実行中の表示

## 実行例

```bash
# 基本監視
python network_monitor.py 8.8.8.8 1.1.1.1

# 5秒間隔、10秒タイムアウトで監視
python network_monitor.py -i 5 -t 10 server1.local server2.local

# 履歴5回分で監視
python network_monitor.py -n 5 -f servers.txt

# ファイルと直接指定を組み合わせ
python network_monitor.py -f production.txt 192.168.1.100 test.server.com
```

## 終了方法

Ctrl+C で終了します。

## トラブルシューティング

### DNS解決が遅い場合

タイムアウト値を長めに設定してください：

```bash
python network_monitor.py -t 10 hostname.local
```

### ping権限エラー

一部の環境では管理者権限が必要な場合があります：

```bash
sudo python network_monitor.py 8.8.8.8
```

## ライセンス

MIT License
