import requests
import json
from typing import Dict, List, Optional

BASE_URL = "http://localhost:8000"

# Dados dos 5 usuários para teste
USUARIOS_TESTE = [
    {
        "email": "user1@test.com",
        "username": "user1",
        "full_name": "Usuário Um",
        "password": "senha123"
    },
    {
        "email": "user2@test.com",
        "username": "user2",
        "full_name": "Usuário Dois",
        "password": "senha456"
    },
    {
        "email": "user3@test.com",
        "username": "user3",
        "full_name": "Usuário Três",
        "password": "senha789"
    },
    {
        "email": "user4@test.com",
        "username": "user4",
        "full_name": "Usuário Quatro",
        "password": "senha012"
    },
    {
        "email": "user5@test.com",
        "username": "user5",
        "full_name": "Usuário Cinco",
        "password": "senha345"
    }
]


def verificar_servidor() -> bool:
    """Verifica se o servidor está rodando"""
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def cadastrar_usuario(usuario: Dict) -> Optional[Dict]:
    """Cadastra um usuário via POST /register"""
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json=usuario,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERRO] Erro ao cadastrar {usuario['username']}: {response.status_code}")
            print(f"       URL: {BASE_URL}/register")
            print(f"       Dados enviados: {json.dumps(usuario, indent=2, ensure_ascii=False)}")
            try:
                error_detail = response.json()
                print(f"       Detalhes JSON: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"       Resposta texto: {response.text[:500]}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Erro de conexao ao cadastrar {usuario['username']}: {str(e)}")
        return None
    except Exception as e:
        print(f"[ERRO] Excecao ao cadastrar {usuario['username']}: {str(e)}")
        import traceback
        print(f"       Traceback: {traceback.format_exc()}")
        return None


def testar_login(username: str, password: str) -> Optional[Dict]:
    """Testa o login via POST /login"""
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            data={
                "username": username,
                "password": password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERRO] Erro ao fazer login com {username}: {response.status_code}")
            print(f"       Detalhes: {response.text}")
            return None
    except Exception as e:
        print(f"[ERRO] Excecao ao fazer login com {username}: {str(e)}")
        return None


def main():
    print("=" * 60)
    print("TESTE DE ROTAS - CADASTRO E LOGIN")
    print("=" * 60)
    print()
    
    # Verificar se o servidor está rodando
    print("[*] Verificando se o servidor esta rodando...")
    if not verificar_servidor():
        print("[ERRO] Servidor nao esta rodando em http://localhost:8000")
        print("       Por favor, inicie o servidor antes de executar os testes.")
        return
    print("[OK] Servidor esta rodando!\n")
    
    # Cadastrar 5 usuários
    print("=" * 60)
    print("CADASTRO DE USUÁRIOS")
    print("=" * 60)
    usuarios_cadastrados = []
    
    for i, usuario in enumerate(USUARIOS_TESTE, 1):
        print(f"\n[*] Cadastrando usuario {i}/5: {usuario['username']}")
        resultado = cadastrar_usuario(usuario)
        
        if resultado:
            print(f"[OK] Usuario {usuario['username']} cadastrado com sucesso!")
            print(f"     ID: {resultado.get('id')}")
            print(f"     Email: {resultado.get('email')}")
            print(f"     Nome: {resultado.get('full_name')}")
            usuarios_cadastrados.append({
                "username": usuario['username'],
                "password": usuario['password'],
                "dados": resultado
            })
        else:
            print(f"[ERRO] Falha ao cadastrar usuario {usuario['username']}")
    
    print(f"\n[*] Resumo: {len(usuarios_cadastrados)}/{len(USUARIOS_TESTE)} usuarios cadastrados com sucesso")
    
    # Testar login
    print("\n" + "=" * 60)
    print("TESTE DE LOGIN")
    print("=" * 60)
    
    logins_sucesso = 0
    for usuario in usuarios_cadastrados:
        print(f"\n[*] Testando login para: {usuario['username']}")
        resultado = testar_login(usuario['username'], usuario['password'])
        
        if resultado:
            print(f"[OK] Login bem-sucedido para {usuario['username']}!")
            print(f"     Token: {resultado.get('access_token', '')[:50]}...")
            print(f"     Tipo: {resultado.get('token_type')}")
            logins_sucesso += 1
        else:
            print(f"[ERRO] Falha no login para {usuario['username']}")
    
    print(f"\n[*] Resumo: {logins_sucesso}/{len(usuarios_cadastrados)} logins bem-sucedidos")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)
    print(f"[OK] Usuarios cadastrados: {len(usuarios_cadastrados)}/{len(USUARIOS_TESTE)}")
    print(f"[OK] Logins bem-sucedidos: {logins_sucesso}/{len(usuarios_cadastrados)}")
    
    if len(usuarios_cadastrados) == len(USUARIOS_TESTE) and logins_sucesso == len(usuarios_cadastrados):
        print("\n[SUCESSO] Todos os testes passaram com sucesso!")
    else:
        print("\n[AVISO] Alguns testes falharam. Verifique os erros acima.")


if __name__ == "__main__":
    main()

