import socket
import threading

def conectar(host, porta):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0) # Timeout super agressivo para nao travar
        s.connect((host, porta))
        s.close()
    except Exception:
        pass

# Salada mista com muito mais alvos
alvos = [
    # Ultra-Baixa (Localhost - Pinta o extremo esquerdo)
    ("127.0.0.1", 22), ("127.0.0.1", 80), ("127.0.0.1", 443), ("127.0.0.1", 53),

    # Brasil (Latencia Baixa)
    ("www.ufes.br", 80), ("www.ufes.br", 443),
    ("www.uol.com.br", 80), ("www.uol.com.br", 443),
    ("www.pudim.com.br", 80), ("www.globo.com", 443),

    # EUA (Latencia Media)
    ("github.com", 22), ("github.com", 443),
    ("smtp.gmail.com", 587), ("smtp.gmail.com", 465),
    ("8.8.8.8", 53), ("1.1.1.1", 53), ("9.9.9.9", 53),

    # Europa (Latencia Alta)
    ("www.ox.ac.uk", 443), ("www.lemonde.fr", 80),
    ("ftp.gnu.org", 21), ("ftp.debian.org", 21),

    # Asia / Oceania (Latencia Muito Alta - Extremo direito)
    ("www.u-tokyo.ac.jp", 443), ("www.sydney.edu.au", 443),
    ("www.baidu.com", 80), ("www.tsinghua.edu.cn", 443)
]

print("[INFO] Iniciando o bombardeio extremo de rede (aguarde)...")

threads = []
# Disparando 50 vezes para cada alvo!
for _ in range(50):
    for host, porta in alvos:
        t = threading.Thread(target=conectar, args=(host, porta))
        threads.append(t)
        t.start()

for t in threads:
    t.join()

print("[INFO] Bombardeio de rede massivo concluido! Pode dar Ctrl+C no script do eBPF.")
