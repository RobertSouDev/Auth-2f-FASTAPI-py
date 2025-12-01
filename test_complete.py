"""Script completo para testar o sistema de registro após correções"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def verificar_servidor(max_tentativas=5, intervalo=2):
    """Verifica se o servidor está rodando, com múltiplas tentativas"""
    print("[*] Verificando se o servidor está rodando...")
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=3)
            if response.status_code == 200:
                print(f"[OK] Servidor está rodando! (tentativa {tentativa}/{max_tentativas})")
                return True
        except requests.exceptions.ConnectionError:
            if tentativa < max_tentativas:
                print(f"[*] Servidor não respondeu. Tentando novamente em {intervalo} segundos... ({tentativa}/{max_tentativas})")
                time.sleep(intervalo)
            else:
                print(f"[ERRO] Servidor não está rodando após {max_tentativas} tentativas")
                return False
        except Exception as e:
            print(f"[ERRO] Erro ao verificar servidor: {str(e)}")
            return False
    
    return False

def testar_registro(usuario):
    """Testa o registro de um usuário"""
    print("\n" + "=" * 60)
    print("TESTE DE REGISTRO DE USUÁRIO")
    print("=" * 60)
    print()
    print(f"[*] Dados do teste:")
    print(f"    Email: {usuario['email']}")
    print(f"    Username: {usuario['username']}")
    print(f"    Full Name: {usuario['full_name']}")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json=usuario,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"[*] Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            resultado = response.json()
            print("[SUCESSO] Usuário cadastrado com sucesso!")
            print(f"    Mensagem: {resultado.get('message', 'N/A')}")
            print(f"    Email: {resultado.get('email', 'N/A')}")
            print(f"    Username: {resultado.get('username', 'N/A')}")
            return True
        else:
            print("[ERRO] Falha ao cadastrar usuário")
            try:
                error_detail = response.json()
                detail = error_detail.get('detail', '')
                print(f"    Detalhes do erro:")
                print(f"    {json.dumps(error_detail, indent=4, ensure_ascii=False)}")
                
                # Análise do erro
                print()
                print("[ANÁLISE DO ERRO]")
                if 'SECRET_KEY' in detail or 'secret' in detail.lower():
                    print("    [AVISO] Erro relacionado ao SECRET_KEY")
                    print("    [SOLUCAO] Verifique se o arquivo .env contém SECRET_KEY")
                elif 'database' in detail.lower() or 'connection' in detail.lower():
                    print("    [AVISO] Erro relacionado ao banco de dados")
                    print("    [SOLUCAO] Verifique se o PostgreSQL está rodando")
                    print("    [SOLUCAO] Verifique se o banco 'auth_db' existe")
                elif 'An error occurred while registering the user' in detail:
                    print("    [AVISO] Erro genérico - servidor pode estar com código antigo")
                    print("    [SOLUCAO] REINICIE o servidor FastAPI")
                    print("    [SOLUCAO] Pare o servidor (Ctrl+C) e inicie novamente")
                else:
                    print(f"    [AVISO] Erro: {detail}")
                    
            except:
                print(f"    Resposta texto: {response.text[:500]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Erro de conexão: {str(e)}")
        return False
    except Exception as e:
        print(f"[ERRO] Exceção inesperada: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verificar_configuracao():
    """Verifica se as configurações básicas estão corretas"""
    print("=" * 60)
    print("VERIFICAÇÃO DE CONFIGURAÇÃO")
    print("=" * 60)
    print()
    
    import os
    from dotenv import load_dotenv
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_path):
        print("[ERRO] Arquivo .env não encontrado!")
        return False
    
    print("[OK] Arquivo .env encontrado")
    load_dotenv(env_path)
    
    # Verificar variáveis essenciais
    variaveis = {
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'SECRET_KEY': os.getenv('SECRET_KEY'),
    }
    
    todas_ok = True
    for var, valor in variaveis.items():
        if valor:
            # Mascarar valores sensíveis
            if 'SECRET_KEY' in var:
                display = valor[:20] + "..." if len(valor) > 20 else valor
            elif 'DATABASE_URL' in var:
                # Mascarar senha na URL
                if '@' in valor:
                    parts = valor.split('@')
                    if ':' in parts[0]:
                        user_pass = parts[0].split(':')
                        display = f"{user_pass[0]}:****@{parts[1]}"
                    else:
                        display = valor
                else:
                    display = valor
            else:
                display = valor
            print(f"[OK] {var}: {display}")
        else:
            print(f"[ERRO] {var}: NÃO DEFINIDO")
            todas_ok = False
    
    print()
    return todas_ok

def main():
    print("=" * 60)
    print("TESTE COMPLETO DO SISTEMA DE REGISTRO")
    print("=" * 60)
    print()
    
    # Verificar configuração
    if not verificar_configuracao():
        print("[AVISO] Algumas configurações estão faltando, mas continuando o teste...")
        print()
    
    # Verificar se o servidor está rodando
    if not verificar_servidor():
        print()
        print("=" * 60)
        print("INSTRUÇÕES PARA INICIAR O SERVIDOR")
        print("=" * 60)
        print()
        print("1. Navegue até o diretório do projeto:")
        print("   cd Auth-2f-FASTAPI-py")
        print()
        print("2. Inicie o servidor:")
        print("   uvicorn app.main:app --reload")
        print()
        print("   OU se estiver usando PDM:")
        print("   pdm run uvicorn app.main:app --reload")
        print()
        print("3. Aguarde até ver a mensagem:")
        print("   'Application startup complete'")
        print()
        print("4. Execute este script novamente para testar")
        print()
        return
    
    # Dados do teste (os mesmos que estavam falhando)
    usuario_teste = {
        "email": "robertdev988@gmail.com",
        "username": "Robert",
        "full_name": "Roger",
        "password": "ab123456"
    }
    
    # Testar registro
    sucesso = testar_registro(usuario_teste)
    
    # Resumo final
    print()
    print("=" * 60)
    print("RESUMO")
    print("=" * 60)
    print()
    
    if sucesso:
        print("[SUCESSO] O sistema está funcionando corretamente!")
        print()
        print("Próximos passos:")
        print("1. Verifique o email para o link de verificação")
        print("2. Use o endpoint /verify-email para ativar a conta")
        print("3. Teste o login após verificar o email")
    else:
        print("[FALHA] O teste falhou")
        print()
        print("Possíveis soluções:")
        print("1. REINICIE o servidor FastAPI (pare e inicie novamente)")
        print("2. Verifique se o PostgreSQL está rodando")
        print("3. Verifique os logs do servidor para mais detalhes")
        print("4. Verifique se o arquivo .env está configurado corretamente")
        print()
        print("Para ver os logs do servidor, verifique o terminal onde")
        print("o servidor está rodando para mensagens de erro detalhadas.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Teste interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERRO] Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

