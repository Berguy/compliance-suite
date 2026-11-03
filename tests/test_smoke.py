"""Teste de fumaça: garante que o app sobe e as rotas existem."""
 
 
def test_app_importa(app_module):
    assert app_module.app is not None
 
 
def test_rotas_registradas(app_module):
    rotas = {regra.rule for regra in app_module.app.url_map.iter_rules()}
    esperadas = {
        "/",
        "/nova-auditoria",
        "/api/executar-auditoria",
        "/auditorias",
        "/clientes",
        "/clientes/novo",
        "/api/configuracoes",
    }
    assert esperadas.issubset(rotas)
