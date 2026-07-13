from bcc import BPF
from time import sleep
import json

# O Programa eBPF em C (Heatmap Multidimensional TCP)
ebpf_code = """
#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <bcc/proto.h>

BPF_HASH(inicio_conexao, struct sock *, u64);

struct heatmap_key {
    u32 dport;
    u64 slot;
};
BPF_HISTOGRAM(heatmap_latencia, struct heatmap_key);

int kprobe__tcp_v4_connect(struct pt_regs *ctx, struct sock *sk) {
    u64 ts = bpf_ktime_get_ns();
    inicio_conexao.update(&sk, &ts);
    return 0;
}

int kprobe__tcp_rcv_state_process(struct pt_regs *ctx, struct sock *sk) {
    u64 *tsp, latencia_ns;
    tsp = inicio_conexao.lookup(&sk);
    if (tsp == 0) return 0;

    latencia_ns = bpf_ktime_get_ns() - *tsp;
    u64 latencia_us = latencia_ns / 1000;
    
    u16 dport = sk->__sk_common.skc_dport;
    dport = ntohs(dport);

    struct heatmap_key key = {};
    key.dport = dport;
    key.slot = bpf_log2l(latencia_us);
    
    heatmap_latencia.increment(key);
    inicio_conexao.delete(&sk);
    return 0;
}
"""

print("1. Compilando Kprobes Multidimensionais...")
b = BPF(text=ebpf_code)

print("\n[INFO] Heatmap 2D de I/O (Camada 4) Ativo!")
print("Gerando trafego no terminal... Pressione Ctrl+C para exportar o relatorio.\n")

try:
    while True:
        sleep(2)
        b["heatmap_latencia"].print_log2_hist("Latencia (us)", "Porta Destino")
        
except KeyboardInterrupt:
    print("\n\nEncerrando captura... Extraindo matriz de dados do Kernel!")
    
    dados_brutos = b["heatmap_latencia"].items()
    matriz_heatmap = {}
    
    for k, v in dados_brutos:
        porta = k.dport
        slot = k.slot
        contagem = v.value
        
        if porta not in matriz_heatmap:
            matriz_heatmap[porta] = {}
        matriz_heatmap[porta][slot] = contagem

    if not matriz_heatmap:
        print("Nenhum dado capturado. Gere trafego de rede antes de encerrar.")
        exit()

    portas = sorted(list(matriz_heatmap.keys()))
    eixo_y = [f"Porta {p}" for p in portas]
    
    max_slot = max(max(slots.keys()) for slots in matriz_heatmap.values())
    eixo_x = [f"2^{i} us" for i in range(max_slot + 1)]
    
    eixo_z = []
    for p in portas:
        linha = [matriz_heatmap[p].get(i, 0) for i in range(max_slot + 1)]
        eixo_z.append(linha)

    html_content = f"""
    <html>
    <head>
        <title>Relatorio Heatmap TCP</title>
        <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
        <style>body {{ font-family: Arial; padding: 20px; background: #f4f4f9; }}</style>
    </head>
    <body>
        <h2 style="text-align: center; color: #333;">Observabilidade de I/O: Heatmap de Latencia TCP</h2>
        <div id="graficoHeatmap" style="width: 90%; height: 600px; margin: auto; background: white; padding: 10px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"></div>
        
        <script>
            var data = [{{
                z: {json.dumps(eixo_z)},
                x: {json.dumps(eixo_x)},
                y: {json.dumps(eixo_y)},
                type: 'heatmap',
                colorscale: 'YlOrRd',
                hoverongaps: false
            }}];
            
            var layout = {{
                title: 'Concentracao de Trafego por Porta (L4) e Custo de I/O',
                xaxis: {{ title: 'Latencia do Handshake TCP (Microssegundos em Log2)' }},
                yaxis: {{ title: 'Portas de Destino' }}
            }};

            Plotly.newPlot('graficoHeatmap', data, layout);
        </script>
    </body>
    </html>
    """
    
    with open('relatorio_heatmap.html', 'w') as f:
        f.write(html_content)
        
    print("[INFO] Sucesso! Relatorio visual gerado: 'relatorio_heatmap.html'")
