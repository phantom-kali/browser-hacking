#!/usr/bin/env python3
import browser_cookie3
import argparse
import json
from datetime import datetime
import sys
import os
import sqlite3
import tempfile
import shutil
import keyring
import base64
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from configparser import ConfigParser

class CookieManager:
    def __init__(self, browser):
        if not browser:
            raise ValueError("Browser must be specified")
        self.browser = browser.lower()
        self.cookie_paths = {
            'chrome': self._get_chrome_path(),
            'firefox': self._get_firefox_path(),
            'brave': self._get_brave_path()
        }
        
        if self.browser not in self.cookie_paths:
            raise ValueError(f"Unsupported browser: {self.browser}. Supported browsers: {', '.join(self.cookie_paths.keys())}")
        
    def _get_chrome_path(self):
        if sys.platform == 'linux':
            return os.path.expanduser('~/.config/google-chrome/Default/Cookies')
        elif sys.platform == 'darwin':
            return os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies')
        elif sys.platform == 'win32':
            return os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cookies')
        
    def _get_firefox_path(self):
        if sys.platform == 'linux':
            firefox_path = os.path.expanduser('~/.mozilla/firefox')
        elif sys.platform == 'darwin':
            firefox_path = os.path.expanduser('~/Library/Application Support/Firefox/Profiles')
        elif sys.platform == 'win32':
            firefox_path = os.path.expanduser('~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles')
            
        # Find default profile
        if os.path.exists(firefox_path):
            profiles = [d for d in os.listdir(firefox_path) if d.endswith('.default-release')]
            if profiles:
                return os.path.join(firefox_path, profiles[0], 'cookies.sqlite')
        return None

    def _get_brave_path(self):
        if sys.platform == 'linux':
            return os.path.expanduser('~/.config/BraveSoftware/Brave-Browser/Default/Cookies')
        elif sys.platform == 'darwin':
            return os.path.expanduser('~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Cookies')
        elif sys.platform == 'win32':
            return os.path.expanduser('~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Cookies')

    def _get_chrome_encryption_key(self):
        """Get the encryption key for Chrome/Brave cookies"""
        if sys.platform == 'linux':
            return keyring.get_password('chrome_cookies', 'chrome_cookies')
        elif sys.platform == 'win32':
            import win32crypt
            path = os.path.join(os.environ['LOCALAPPDATA'], 
                              'Google', 'Chrome', 'User Data', 'Local State')
            if self.browser == 'brave':
                path = os.path.join(os.environ['LOCALAPPDATA'],
                                  'BraveSoftware', 'Brave-Browser', 'User Data', 'Local State')
            
            with open(path, 'r', encoding='utf-8') as f:
                local_state = json.loads(f.read())
            encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
            return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            
        elif sys.platform == 'darwin':
            if self.browser == 'chrome':
                key_label = 'Chrome Safe Storage'
            else:  # brave
                key_label = 'Brave Safe Storage'
            
            cmd = ['security', 'find-generic-password',
                   '-w', '-a', 'Chrome', '-s', key_label]
            import subprocess
            try:
                key = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                return key.strip()
            except:
                return None
        return None

    def get_cookies(self, domain):
        """Get cookies for the specified domain"""
        try:
            if self.browser == 'chrome':
                cookies = browser_cookie3.chrome(domain_name=domain)
            elif self.browser == 'firefox':
                cookies = browser_cookie3.firefox(domain_name=domain)
            elif self.browser == 'brave':
                cookies = browser_cookie3.brave(domain_name=domain)
            else:
                raise ValueError(f"Unsupported browser: {self.browser}")
            
            return list(cookies)
        except Exception as e:
            print(f"Error accessing {self.browser} cookies: {str(e)}")
            return None

    def modify_cookie(self, domain, cookie_name, new_value):
        """Modify a cookie value for the specified domain"""
        cookie_path = self.cookie_paths.get(self.browser)
        if not cookie_path or not os.path.exists(cookie_path):
            print(f"Cookie database not found for {self.browser} at {cookie_path}")
            return False

        # Create a temporary copy of the database
        temp_db = tempfile.NamedTemporaryFile(delete=False).name
        shutil.copy2(cookie_path, temp_db)

        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            if self.browser in ['chrome', 'brave']:
                cursor.execute("""
                    UPDATE cookies 
                    SET value = ?, encrypted_value = ''
                    WHERE host_key LIKE ? AND name = ?
                """, (new_value, f'%{domain}%', cookie_name))
                rows_affected = cursor.rowcount
            elif self.browser == 'firefox':
                cursor.execute("""
                    UPDATE moz_cookies 
                    SET value = ?
                    WHERE host LIKE ? AND name = ?
                """, (new_value, f'%{domain}%', cookie_name))
                rows_affected = cursor.rowcount

            conn.commit()
            conn.close()

            if rows_affected == 0:
                print(f"No cookie found with name '{cookie_name}' for domain '{domain}'")
                return False

            # Backup original and replace with modified version
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{cookie_path}.backup_{timestamp}"
            shutil.copy2(cookie_path, backup_path)
            shutil.copy2(temp_db, cookie_path)
            
            print(f"Successfully modified cookie '{cookie_name}' for domain '{domain}'")
            print(f"Original database backed up to: {backup_path}")
            return True

        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            return False
        except Exception as e:
            print(f"Error modifying cookie: {str(e)}")
            return False
        finally:
            try:
                os.unlink(temp_db)
            except:
                pass

def format_cookie(cookie):
    """Convert cookie object to dictionary with relevant information"""
    return {
        'name': cookie.name,
        'value': cookie.value,
        'domain': cookie.domain,
        'path': cookie.path,
        'secure': cookie.secure,
        'expires': datetime.fromtimestamp(cookie.expires).isoformat() if cookie.expires else None,
        'http_only': cookie.has_nonstandard_attr('HttpOnly')
    }

def main():
    parser = argparse.ArgumentParser(description='Browser Cookie Manager')
    parser.add_argument('domain', help='Domain to work with (e.g., example.com)')
    parser.add_argument('--browser', '-b',
                        choices=['chrome', 'firefox', 'brave'],
                        help='Browser to work with (REQUIRED for --modify)',
                        required='--modify' in sys.argv)
    parser.add_argument('--output', '-o', help='Output file path (JSON format)')
    parser.add_argument('--modify', '-m', nargs=2, metavar=('COOKIE_NAME', 'NEW_VALUE'),
                        help='Modify a cookie value (specify cookie name and new value)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all cookies for the domain')
    
    args = parser.parse_args()
    
    try:
        if args.modify and not args.browser:
            parser.error("--browser is required when using --modify")
            
        cookie_manager = CookieManager(args.browser if args.browser else 'chrome')

        if args.modify:
            cookie_name, new_value = args.modify
            print(f"\nModifying cookie in {args.browser.upper()} browser")
            print(f"Domain: {args.domain}")
            print(f"Cookie name: {cookie_name}")
            print(f"New value: {new_value}")
            
            if not cookie_manager.modify_cookie(args.domain, cookie_name, new_value):
                sys.exit(1)
                
            print("\nCurrent cookies after modification:")
            
        cookies = cookie_manager.get_cookies(args.domain)
        
        if not cookies:
            print(f"No cookies found for domain: {args.domain}")
            sys.exit(0)
            
        formatted_cookies = [format_cookie(cookie) for cookie in cookies]
        print(f"\nFound {len(formatted_cookies)} cookies for {args.domain}")
        
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    json.dump(formatted_cookies, f, indent=2)
                print(f"Successfully saved cookies to: {args.output}")
            except Exception as e:
                print(f"Error saving to file: {str(e)}")
                print("Displaying cookies in console instead:\n")
                print(json.dumps(formatted_cookies, indent=2))
        else:
            print("\nCookie contents:")
            print(json.dumps(formatted_cookies, indent=2))

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
