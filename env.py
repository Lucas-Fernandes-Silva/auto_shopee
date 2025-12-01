user = "raimundovirginio8@gmail.com"
pwd = "iwld satm jadn yhbu"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


fornecedores_bloqueados = [
    "EDP SAO PAULO DISTRIBUICAO DE ENERGIA SA" "IND E COM DE TUBOS E CONEXOES FORT.COM",
    "VOTORANTIM CIMENTOS SA",
    "CABOQUINHO MATERIAIS PARA CONSTRUCAO",
    "Saint-Gobain do Brasil Produtos Ind ustriais e para Construc",
    "CARREFOUR COMERCIO E INDUSTRIA LTDA",
    "MAGAZINE LUIZA SA",
]

fornecedores_web_scraping = [
    "CONSTRUDIGI DISTRIBUIDORA DE MATERIAIS PARA CONSTRUCAO LTDA",
    "CONSTRUJA DISTR. DE MATERIAIS P/ CONSTRU",
    "M.S.B. COMERCIO DE MATERIAIS PARA CONSTRUCAO",
]


fornecedores_noweb_scraping = [
    "MJLESTE DISTRIBUIDORA DE MATERIAIS PARA CONSTRUCAO LTDA",
    "MJR CUNHA DISTRIBUIDORA DE MAT.CONSTR LTDA",
    "SOOPER HOLDING LTDA",
    "SOPREMA LTDA",
    "DENVER IMPERMEABILIZANTES, INDUSTRIA E C",
    "KADESH EQUIPAMENTOS PROFISSIONAIS LTDA",
    "Global Center Com.Ferragens Ltda",
    "MJR CUNHA DISTRIBUIDORA DE MATERIAIS PARA CONSTRUCAO LTDA",
]

fornecedores = [
    fornecedores_bloqueados,
    fornecedores_web_scraping,
    fornecedores_noweb_scraping,
]
