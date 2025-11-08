import paramiko
import time

class SSHClient:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.ssh = None

    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.ip, username=self.username, password=self.password, timeout=10)
        self.shell = self.ssh.invoke_shell()
        time.sleep(1)
        self.shell.recv(1024)  # 清空欢迎信息

    def execute_cmds(self, cmds):
        self.connect()
        result = {}
        for cmd in cmds:
            self.shell.send(cmd + "\n")
            time.sleep(2)
            output = self._read_output()
            result[cmd] = output
        self.ssh.close()
        return result

    def _read_output(self):
        output = ""
        while True:
            chunk = self.shell.recv(4096).decode(errors="ignore")
            output += chunk
            if "--- More ---" in chunk:
                self.shell.send(" ")  # 翻页
                time.sleep(1)
            elif chunk.endswith(">") or chunk.endswith("#"):
                break
        return output.replace("--- More ---", "").strip()
