import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
import sys

PASTA_DESTINO = Path(r"C:\XML")
CERTIFICADO = "meu_certificado.pem" 
CHAVE = "minha_chave.pem"          

URL_LOGIN = "https://www.nfse.gov.br/EmissorNacional"
URL_BASE = "https://www.nfse.gov.br"

print("="*40)
print("   ROBÔ XML - ASSISTENTE PARA XML - SP")
print("="*40)

DATA_INICIO = input("Data Inicial (ex: 01/01/2026): ")
DATA_FIM = input("Data Final (ex: 31/01/2026): ")

def baixar_tudo():
    PASTA_DESTINO.mkdir(parents=True, exist_ok=True)
    
    sessao = requests.Session()
    sessao.cert = (CERTIFICADO, CHAVE)
    sessao.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        print("\n1. Realizando login...")
        resposta_login = sessao.get(URL_LOGIN)
        resposta_login.raise_for_status()
        soup_login = BeautifulSoup(resposta_login.text, 'html.parser')
        
        link_autenticacao = None
        for a in soup_login.find_all('a', href=True):
            if "certificado digital" in a.text.lower() or "acesso via certificado" in a.text.lower():
                link_autenticacao = a['href']
                break
        
        if not link_autenticacao:
             for img in soup_login.find_all('img', alt=True):
                if "certificado" in img['alt'].lower():
                    pai = img.find_parent('a')
                    if pai and pai.get('href'):
                        link_autenticacao = pai['href']
                        break

        if link_autenticacao:
            if not link_autenticacao.startswith("http"):
                link_autenticacao = URL_BASE + link_autenticacao
            sessao.get(link_autenticacao)
            print("-> Login efetuado com sucesso.")
        else:
            print("AVISO: Login automático falhou ou já está logado. Tentando continuar...")

    except Exception as e:
        print(f"ERRO NO LOGIN: {e}")
        input("\nPressione ENTER para fechar...")

        return

    print(f"\n2. Iniciando busca de {DATA_INICIO} a {DATA_FIM}...")
    
    url_atual = f"{URL_BASE}/EmissorNacional/Notas/Emitidas"
    parametros_iniciais = {
        'busca': '',
        'datainicio': DATA_INICIO,
        'datafim': DATA_FIM
    }
    
    pagina_numero = 1
    total_baixados = 0

    while url_atual:
        try:
            print(f"\n--- Processando Página {pagina_numero} ---")
            
            if pagina_numero == 1:
                resposta = sessao.get(url_atual, params=parametros_iniciais)
            else:
                resposta = sessao.get(url_atual)
            
            resposta.raise_for_status()
            soup = BeautifulSoup(resposta.text, 'html.parser')
            
            links_download = [link['href'] for link in soup.find_all('a', href=True) if "Download/NFSe" in link['href']]
            
            if not links_download:
                print("Nenhum XML nesta página.")
            else:
                for link_parcial in links_download:
                    try:
                        if link_parcial.startswith("http"):
                            link_completo = link_parcial
                        else:
                            link_completo = URL_BASE + link_parcial
                        
                        nome_arquivo = link_parcial.split("/")[-1] + ".xml"
                        caminho_final = PASTA_DESTINO / nome_arquivo
                        
                        if not caminho_final.exists():
                            print(f"Baixando: {nome_arquivo}...")
                            resp_xml = sessao.get(link_completo)
                            with open(caminho_final, 'wb') as arquivo:
                                arquivo.write(resp_xml.content)
                            total_baixados += 1
                        else:
                            print(f"Arquivo já existe: {nome_arquivo}")
                    except Exception as e:
                        print(f"Erro ao baixar arquivo: {e}")
                        input("\nPressione ENTER para fechar...")


            proxima_url = None
            todos_links = soup.find_all('a', href=True)
            
            for a in todos_links:
                title = a.get('title', '')
                orig_title = a.get('data-original-title', '')
                
                tem_icone = a.find('i', class_='fa-angle-right')
                
                eh_botao_proximo = "Próxima" in title or "Próxima" in orig_title or tem_icone
                
                if eh_botao_proximo:
                    pai_li = a.find_parent('li')
                    esta_desabilitado = pai_li and 'disabled' in pai_li.get('class', [])
                    
                    if esta_desabilitado:
                        print("-> Botão 'Próximo' está desabilitado. Fim da paginação.")
                        proxima_url = None 
                        break
                    
                    link_bruto = a['href']
                    if "javascript" not in link_bruto and link_bruto.strip() != "#":
                        if link_bruto.startswith("http"):
                            proxima_url = link_bruto
                        else:
                            proxima_url = URL_BASE + link_bruto
                        break 

            if proxima_url:
                print(f"-> Indo para pág {pagina_numero + 1}...")
                url_atual = proxima_url
                pagina_numero += 1
                time.sleep(1) 
            else:
                print("\nNenhuma próxima página encontrada. Encerrando.")
                break

        except Exception as e:
            print(f"ERRO CRÍTICO NA PÁGINA: {e}")
            input("\nPressione ENTER para fechar...")

            break

    print(f"\nRESUMO FINAL: {total_baixados} arquivos baixados com sucesso.")

    input("\nPressione ENTER para fechar...")

if __name__ == "__main__":
    baixar_tudo()