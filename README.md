# Browser Cookie Dumper & Manager

A Python-based tool for dumping and managing browser cookies across Chrome, Firefox, and Brave browsers on Linux, Windows, and macOS.

## Features

- Extract cookies from multiple browsers:
  - Google Chrome
  - Mozilla Firefox
  - Brave Browser
- List all cookies for a specific domain
- Modify cookie values
- Export cookies to JSON format
- Cross-platform support (Linux, Windows, macOS)
- Automatic cookie database backup before modifications

## Installation

1. Clone the repository:
```bash
git clone https://github.com/phantom-kali/browser-hacking.git
cd browser-hacking
```

2. Install required dependencies:
```bash
pip install browser-cookie3 keyring cryptography
# For Windows users, also install:
pip install pywin32  # Windows only
```

## Usage

### Basic Cookie Listing
```bash
python cookie_dumper.py example.com
```

### Specify Browser
```bash
python cookie_dumper.py example.com --browser chrome
python cookie_dumper.py example.com --browser firefox
python cookie_dumper.py example.com --browser brave
```

### Export Cookies to JSON
```bash
python cookie_dumper.py example.com -o cookies.json
```

### Modify Cookie Value
```bash
python cookie_dumper.py example.com --browser chrome --modify "cookieName" "newValue"
```

## Command Line Options

- `domain`: Target domain to work with (required)
- `-b, --browser`: Browser to use (chrome/firefox/brave)
- `-o, --output`: Save output to JSON file
- `-m, --modify`: Modify cookie value (requires cookie name and new value)
- `-l, --list`: List all cookies for the domain

## Security Note

This tool creates backup files before modifying cookies. Backup files are stored in the same directory as the original cookie database with the format: `Cookies.backup_YYYYMMDD_HHMMSS`

## Requirements

- Python 3.6+
- browser_cookie3
- keyring
- cryptography
- pywin32 (Windows only)

## Supported Platforms

- Linux
- Windows
- macOS

## License

MIT License

## Disclaimer

This tool is for educational and testing purposes only. Use it responsibly and only on systems you own or have permission to test.
