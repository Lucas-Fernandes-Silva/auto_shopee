# Análise automática do projeto

**Local:** `/mnt/data/projeto_unzipped`

**Total de arquivos:** 1181

**Tamanho total (bytes):** 33130553


## Top-level directories

- src
- cache
- logs
- notas
- planilhas dados

## Extensões de arquivo (contagem)

- `.xml`: 1142
- `.py`: 21
- `.xlsx`: 8
- `.csv`: 3
- `.txt`: 2
- `[no-ext]`: 1
- `.json`: 1
- `.ipynb`: 1
- `.log`: 1
- `.identifier`: 1

## Maiores arquivos (por tamanho)

- `planilhas dados/colunas_upseller.xlsx` — 2961689 bytes
- `planilhas dados/base_nome.xlsx` — 584622 bytes
- `cache/produtos.json` — 581015 bytes
- `final.xlsx` — 546161 bytes
- `planilhas dados/pai_filho_variantes.xlsx` — 509713 bytes
- `planilhas dados/upseller_template.xlsx` — 476777 bytes
- `planilhas dados/produtos_categorias.xlsx` — 458270 bytes
- `planilhas dados/produtos_com_marcas.xlsx` — 454258 bytes
- `planilhas dados/produtos.xlsx` — 438224 bytes
- `notas/NFe35220804648461000207550020024869481171119118.xml` — 64959 bytes
- `notas/nfes/NFe35220804648461000207550020024869481171119118.xml` — 64959 bytes
- `notas/NFe35250804648461000207550020032778231142130220.xml` — 63400 bytes
- `notas/nfes/NFe35250804648461000207550020032778231142130220.xml` — 63400 bytes
- `notas/NFe35251004648461000207550020033060421254151236.xml` — 61861 bytes
- `notas/nfes/NFe35251004648461000207550020033060421254151236.xml` — 61861 bytes

## Git info

{
  "found": false
}

## Arquivos Python — resumo (amostra)

### src/base_nome.py
- linhas: 113, blanks: 27
- funções (até 10): normalizar, similaridade_media, parte_comum, eh_medida
- classes (até 10): —
- imports (amostra): pandas, rapidfuzz.fuzz, unicodedata, re, tqdm.tqdm, itertools, collections.Counter, numpy
- long lines (>88): 1 (first examples: [(80, 94)])

### src/dados.py
- linhas: 30, blanks: 1
- funções (até 10): —
- classes (até 10): —
- imports (amostra): —
- long lines (>88): 12 (first examples: [(2, 129), (3, 126), (4, 125), (5, 129), (6, 122)])

### src/email_handler.py
- linhas: 25, blanks: 3
- funções (até 10): __init__, baixar_anexos
- classes (até 10): EmailHandler
- imports (amostra): os, imap_tools.MailBox, imap_tools.AND, datetime.timedelta, src.logger.logger
- long lines (>88): 2 (first examples: [(15, 113), (16, 90)])
- trailing whitespace occurrences: 1

### src/fornecedores.py
- linhas: 96, blanks: 22
- funções (até 10): extrair_fornecedores, normalizar_cnpj, formatar_cnpj, criar_linha
- classes (até 10): —
- imports (amostra): os, xml.etree.ElementTree, csv, re, pandas
- ⚠️ uses_print: True, uses_pdb: False
- long lines (>88): 11 (first examples: [(22, 89), (23, 97), (24, 98), (25, 109), (26, 104)])

### src/group.py
- linhas: 65, blanks: 13
- funções (até 10): normalizar
- classes (até 10): —
- imports (amostra): pandas, rapidfuzz.fuzz, rapidfuzz.process, unicodedata
- ⚠️ uses_print: True, uses_pdb: False
- long lines (>88): 1 (first examples: [(9, 102)])

### src/logger.py
- linhas: 33, blanks: 7
- funções (até 10): —
- classes (até 10): —
- imports (amostra): logging, logging.handlers.RotatingFileHandler, os
- long lines (>88): 1 (first examples: [(21, 91)])

### src/marcas.py
- linhas: 119, blanks: 25
- funções (até 10): limpar_texto, detectar_marca
- classes (até 10): —
- imports (amostra): pandas, numpy, re, unicodedata, env.fornecedores_noweb_scraping
- ⚠️ uses_print: True, uses_pdb: False
- long lines (>88): 14 (first examples: [(29, 129), (30, 126), (31, 125), (32, 129), (33, 122)])

### src/notas_manager.py
- linhas: 37, blanks: 15
- funções (até 10): __init__, cria_dataframe, copiar_xmls, salvar_excel
- classes (até 10): NotasManager
- imports (amostra): pandas, shutil, os, src.logger.logger
- trailing whitespace occurrences: 2

### src/transform.py
- linhas: 144, blanks: 36
- funções (até 10): normalizar, limpar_texto, gtin, escolher_prioritario, detectar_marca, preencher_categoria, similaridade_media, parte_comum
- classes (até 10): —
- imports (amostra): pandas, numpy, re, unicodedata, rapidfuzz.fuzz, rapidfuzz.process, tqdm.tqdm, collections.Counter, itertools, src.dados.marcas_adicionais
- ⚠️ uses_print: True, uses_pdb: False
- long lines (>88): 14 (first examples: [(19, 102), (40, 95), (43, 98), (67, 90), (76, 99)])

### src/upseller_template.py
- linhas: 52, blanks: 11
- funções (até 10): criar_linha
- classes (até 10): —
- imports (amostra): pandas, os

### src/variantes.py
- linhas: 67, blanks: 14
- funções (até 10): normalizar
- classes (até 10): —
- imports (amostra): pandas, rapidfuzz.fuzz, unicodedata, tqdm.tqdm
- ⚠️ uses_print: True, uses_pdb: False
- long lines (>88): 3 (first examples: [(11, 102), (38, 109), (58, 94)])

### src/web_scraper.py
- linhas: 231, blanks: 33
- funções (até 10): __init__, _carregar_cache, _salvar_cache, _processar_com_requests, _montar_url, _get_nested, _extrair_dados, _processar_produto, enriquecer_dataframe, processar_linha
- classes (até 10): WebScraper
- imports (amostra): requests, bs4.BeautifulSoup, json, os, concurrent.futures.ThreadPoolExecutor, asyncio, playwright.async_api.async_playwright, src.logger.logger, pandas
- long lines (>88): 8 (first examples: [(155, 104), (160, 114), (168, 99), (179, 95), (182, 99)])
- trailing whitespace occurrences: 7

### src/xml_processor.py
- linhas: 85, blanks: 23
- funções (até 10): __init__, processar_todos, _listar_arquivos_xml, _processar_arquivo, _extrair_dados
- classes (até 10): XMLProcessor
- imports (amostra): concurrent.futures.ProcessPoolExecutor, xml.etree.ElementTree, datetime.datetime, os, src.logger.logger
- ⚠️ uses_print: True, uses_pdb: False
- long lines (>88): 1 (first examples: [(62, 95)])
- trailing whitespace occurrences: 4

### baseVariatoinExtract.py
- linhas: 39, blanks: 3
- funções (até 10): similaridade_media, parte_comum, aplicar
- classes (até 10): BaseVariantExtractor
- imports (amostra): numpy, rapidfuzz.fuzz, itertools, normalizer.Normalizer, collections.Counter, re, tqdm.tqdm
- long lines (>88): 6 (first examples: [(22, 98), (23, 115), (27, 114), (32, 98), (36, 102)])

### brandDetector.py
- linhas: 34, blanks: 5
- funções (até 10): __init__, _compilar_marcas, detectar, aplicar
- classes (até 10): BrandDetector
- imports (amostra): normalizer.Normalizer, numpy
- long lines (>88): 2 (first examples: [(13, 98), (33, 110)])

### categoryFilter.py
- linhas: 26, blanks: 3
- funções (até 10): __init__, _buscar_categoria, aplicar
- classes (até 10): CategoryFiller
- imports (amostra): normalizer.Normalizer, pandas, rapidfuzz.process, rapidfuzz.fuzz
- long lines (>88): 2 (first examples: [(20, 102), (25, 101)])

### env.py
- linhas: 41, blanks: 9
- funções (até 10): —
- classes (até 10): —
- imports (amostra): —
- long lines (>88): 3 (first examples: [(5, 89), (7, 110), (40, 96)])

### gtinValidator.py
- linhas: 24, blanks: 6
- funções (até 10): __init__, is_valid_gtin, filter_priority, escolher_prioritario
- classes (até 10): GTINValidator
- imports (amostra): pandas
- long lines (>88): 3 (first examples: [(18, 89), (19, 103), (22, 106)])
- trailing whitespace occurrences: 1

### main.py
- linhas: 26, blanks: 7
- funções (até 10): —
- classes (até 10): —
- imports (amostra): src.email_handler.EmailHandler, src.xml_processor.XMLProcessor, src.web_scraper.WebScraper, src.notas_manager.NotasManager, datetime.date, env, pandas, src.logger.logger
- long lines (>88): 1 (first examples: [(23, 91)])

### normalizer.py
- linhas: 13, blanks: 1
- funções (até 10): normalize
- classes (até 10): Normalizer
- imports (amostra): pandas, re, unicodedata
- long lines (>88): 1 (first examples: [(11, 106)])

### variationGrouper.py
- linhas: 30, blanks: 5
- funções (até 10): __init__, aplicar
- classes (até 10): VariationGrouper
- imports (amostra): normalizer.Normalizer, tqdm.tqdm, rapidfuzz.fuzz
- long lines (>88): 3 (first examples: [(11, 127), (19, 120), (26, 121)])


## Sugestões rápidas de reorganização

- Colocar código principal em `src/` (se houver scripts espalhados).
- Mover testes para `tests/` com estrutura pytest.
- Adicionar `requirements.txt` ou `pyproject.toml` se não existirem.
- Criar `README.md` e `CONTRIBUTING.md` com instruções de como executar/testar.
- Se houver um package, adicionar `setup.cfg`/`pyproject.toml`.
- Usar `src/packagename` para evitar problemas de imports locais em desenvolvimento.
