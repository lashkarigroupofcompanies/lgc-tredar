import os
import win32com.client

user_home = os.path.expanduser('~')
desktop_dirs = [
    os.path.join(user_home, 'Desktop'),
    os.path.join(user_home, 'OneDrive', 'Desktop'),
    r'C:\Users\Public\Desktop'
]

repo_root = os.path.dirname(os.path.abspath(__file__))
target_exe = os.path.join(repo_root, 'dist', 'LGCTrader.exe')
work_dir = repo_root
icon_path = os.path.join(repo_root, 'ui', 'src-tauri', 'icons', 'icon.ico')

shell = win32com.client.Dispatch('WScript.Shell')

updated = False
for d in desktop_dirs:
    lnk_file = os.path.join(d, 'LGC Trader.lnk')
    try:
        sc = shell.CreateShortcut(lnk_file)
        sc.TargetPath = target_exe
        sc.WorkingDirectory = work_dir
        if os.path.exists(icon_path):
            sc.IconLocation = f"{icon_path},0"
        sc.Description = "LGC Trader Autonomous Multi-Agent Trading System"
        sc.Save()
        print(f"Successfully created/updated shortcut at: {lnk_file} -> {target_exe}")
        updated = True
    except Exception as e:
        print(f"Could not write to {lnk_file}: {e}")

if updated:
    print("Desktop shortcut update complete.")
