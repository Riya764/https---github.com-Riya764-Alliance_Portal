from paramiko import Transport, SFTPClient, RSAKey
import paramiko
# from psycopg2 import connect
# paramiko.util.log_to_file("paramiko.log")
# # Open a transport
# host, port = "sftp.javis.co", 22
# # transport = paramiko.Transport((host, port))

# # # Auth
username = "hul-admin"
key = paramiko.RSAKey.from_private_key_file(
    'D:\Work\csscorp\HUL\pepsico\ddh1', password="g6rBY~5$mu")

sftp = paramiko.SSHClient()
sftp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sftp.connect(host, username=username, password="123455", pkey=key)
a = sftp.open_sftp()
a.put(put())
print(a.listdir())
sftp.close()

# # Go!

# # Download
# filepath = "/etc/passwd"
# localpath = "/home/remotepasswd"
# sftp.get(filepath, localpath)

# # Upload
# filepath = "/home/foo.jpg"
# localpath = "/home/pony.jpg"
# sftp.put(localpath, filepath)

# # Close
# if sftp:
#     sftp.close()
# if transport:
#     transport.close()


class SFTPConnection:

    ssh = None
    sftp = None

    def connect(self, host, username, password=None, pkey=None, passpharse=None, port=22,):
        key = None
        if pkey and passpharse:
            key = paramiko.RSAKey.from_private_key_file(
                pkey, password=passpharse)
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=username,
                         pkey=key)
        self.sftp = self.ssh.open_sftp()

    def upload_file(self, source, target):
        pass

    def download_file(self):
        print(self.sftp.listdir())

    def archive_file(self, path):
        pass

    def close(self):
        self.ssh.close()


sftp = SFTPConnection()
sftp.connect("sftp.javis.co", "hul-admin",
             pkey="D:\Work\csscorp\HUL\pepsico\ddh1", passpharse="g6rBY~5$mu")

sftp.get()
sftp.close()
