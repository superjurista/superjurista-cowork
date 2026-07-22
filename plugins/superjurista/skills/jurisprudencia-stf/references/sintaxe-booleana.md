# Sintaxe de busca do STF

O portal do STF usa Elasticsearch (`query_string`) com um analisador jurídico. Sinônimos e
plural vêm ligados por padrão. O motor (`engine.js`) passa a `busca` direto — os operadores
abaixo funcionam como digitados.

## Operadores

| Operador | Sintaxe | Exemplo |
|----------|---------|---------|
| E (AND)  | `E` (padrão — pode omitir) | `pensao E morte` |
| OU (OR)  | `OU` | `droga OU entorpecente` |
| NÃO (NOT)| `NAO` | `prisao NAO preventiva` |
| Frase exata | `"..."` (anula operadores internos) | `"presuncao de inocencia"` |
| Proximidade | `"..."~N` (máx. N palavras entre os termos) | `"concurso nomeacao"~5` |
| Fuzzy | `termo~` | `indenizacao~` |
| Curinga (0+) | `$` | `indeniz$`, `$constitucional` |
| Curinga (1) | `?` | `RE 56394?` |
| Agrupamento | `( )` | `direito E (privacidade OU intimidade)` |

**Dicas:** evite algarismos romanos e hífens (digite `9`, não `IX`). Dentro de aspas, os
operadores são anulados. `E` é o padrão — não precisa digitar entre termos.

## Bases (parâmetro `base`)

| Base | Conteúdo | Cobertura |
|------|----------|-----------|
| `acordaos` | Decisões colegiadas (Turmas/Plenário) | desde 06/07/1950 |
| `repercussao-geral` | Acórdãos paradigmáticos de RG | — |
| `sumulas` | Enunciados de súmula (inclui vinculantes) | — |
| `decisoes` | Decisões monocráticas selecionadas | — |
| `informativos` | Informativos do STF (sem valor oficial) | — |

## Filtros (opts)

- `ministro` — relator (ex.: `GILMAR MENDES`, `BARROSO`).
- `dataInicio` / `dataFim` — DDMMAAAA (faixa de data de julgamento).
- `pagina` / `tamanho` — paginação (tamanho padrão 10, máx. 50).
