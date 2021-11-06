import unittest
import subprocess
import time
class TestClientServer(unittest.TestCase):
    def test(self):
        server_process = subprocess.Popen(['python', 'server.py'],
                     stdout=subprocess.PIPE, 
                    #  stderr=subprocess.PIPE,
                     stdin=subprocess.PIPE,)
        server_process.stdin.write(b'lan\n')
        server_process.stdin.flush()
        time.sleep(0.5)
        # server_process.stdin.close()

        client_process_1 = subprocess.Popen(['python', 'client.py'],
                    # stdout=subprocess.PIPE, 
                    # stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,)
        client_process_1.stdin.write(b'login\n')
        client_process_1.stdin.flush()
        client_process_1.stdin.write(b'Player1\n')
        client_process_1.stdin.flush()

        client_process_2 = subprocess.Popen(['python', 'client.py'],
                    # stdout=subprocess.PIPE, 
                    # stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,)
        client_process_2.stdin.write(b'login\n')
        client_process_2.stdin.write(b'Player2\n')

        client_process_1.stdin.write(b'start\n')
        client_process_1.stdin.flush()
        time.sleep(0.5)
        # client_process_1.stdin.close()

        client_process_2.stdin.write(b'join\n')
        client_process_2.stdin.flush()
        client_process_2.stdin.write(b'0\n')
        client_process_2.stdin.flush()
        time.sleep(0.5)
        # client_process_2.stdin.close()
        time.sleep(1.5)
        
        client_process_1.kill()
        client_process_2.kill()
        server_process.kill()
        time.sleep(1)



if __name__ == '__main__':
    unittest.main()