import unittest
import subprocess
import time


class TestCompetition(unittest.TestCase):
    def test(self):
        server_process = subprocess.Popen(['python', 'server.py'],
                    #  stdout=subprocess.PIPE, 
                    #  stderr=subprocess.PIPE,
                     stdin=subprocess.PIPE,)
        server_process.stdin.write(b'lan\n')
        server_process.stdin.flush()
        time.sleep(0.5)
        # server_process.stdin.close()

        client_process_1 = self.client("A")
        client_process_2 = self.client("B")
        client_process_3 = self.client("C")
        client_process_4 = self.client("D")

    
    def client(self, name):
        client_process = subprocess.Popen(['python', 'client.py'],
                    stdout=subprocess.DEVNULL, 
                    # stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE)
        client_process.stdin.write(b'login\n')
        client_process.stdin.flush()
        client_process.stdin.write(name.encode())
        client_process.stdin.flush()



if __name__ == '__main__':
    unittest.main()
