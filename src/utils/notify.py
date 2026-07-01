import platform
import subprocess


def notify(title: str, message: str):
    """Show a native OS notification. Fails silently if unsupported."""
    system = platform.system()
    try:
        if system == "Darwin":
            safe_title = title.replace('"', '\\"')
            safe_message = message.replace('"', '\\"')
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{safe_message}" with title "{safe_title}" sound name "Glass"'],
                check=False,
            )
        elif system == "Linux":
            subprocess.run(["notify-send", title, message], check=False)
        elif system == "Windows":
            safe_title = title.replace("'", "''")
            safe_message = message.replace("'", "''")
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Add-Type -AssemblyName System.Windows.Forms; "
                 "$n = New-Object System.Windows.Forms.NotifyIcon; "
                 "$n.Icon = [System.Drawing.SystemIcons]::Information; "
                 "$n.Visible = $true; "
                 f"$n.ShowBalloonTip(5000, '{safe_title}', '{safe_message}', "
                 "[System.Windows.Forms.ToolTipIcon]::Info)"],
                check=False,
            )
    except Exception:
        pass
