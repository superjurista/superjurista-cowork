# Glossário leigo, perguntas frequentes e solução de problemas

> Material de apoio do concierge. Usar estas respostas como base, sempre
> adaptando ao caso concreto do usuário — e sem jargão.

## Glossário (como explicar cada termo)

| Termo técnico | Como dizer ao jurista |
|---|---|
| Pipeline / fluxo | "Linha de produção da peça: o trabalho é dividido em etapas, cada uma feita por um assistente especializado e conferida automaticamente antes da próxima" |
| Gate | "Conferência automática de qualidade: o sistema verifica formato, seções obrigatórias e integridade de cada etapa antes de seguir" |
| Subagente | "Assistente especializado que faz UMA etapa (ex.: só a linha do tempo, só a análise) — por isso cada etapa sai focada" |
| Workspace / pasta do caso | "A pasta no seu computador onde ficam os autos e tudo o que o sistema produzir sobre este caso" |
| Conector / gateway | "O serviço SuperJurista na nuvem, que fornece os modelos de trabalho e as buscas de jurisprudência — exige assinatura ativa" |
| Pronto / prompt curado | "Modelo de tarefa pronto: um roteiro profissional para uma tarefa pontual (um parecer, uma análise, uma peça)" |
| Missão | "A instrução detalhada que cada assistente especializado recebe para a sua etapa" |
| Regime verbatim | "Regra de ouro das citações: só entra entre aspas o que foi copiado exatamente da fonte (dos autos ou de uma busca real de jurisprudência feita na hora)" |
| OCR | "Leitura de páginas escaneadas: transforma a imagem do PDF em texto pesquisável, no seu próprio computador" |
| Retomada | "Se o trabalho for interrompido, o sistema reconhece o que já está pronto e continua de onde parou, sem refazer" |

## Perguntas frequentes

**"Meus autos vão para a internet?"**
Os autos e todos os documentos produzidos ficam gravados na pasta do caso, no
computador do usuário — nenhum arquivo é publicado nem enviado a terceiros.
Vão à internet: as consultas de jurisprudência (que buscam nos sites dos
tribunais) e a conversa normal com o Claude — o que inclui os trechos dos
autos que o modelo lê para trabalhar, sob as regras de privacidade da conta
Claude em uso. A conferência de citações dos autos roda localmente. Em caso
de segredo de justiça, a decisão sobre usar o sistema é do jurista, informado
por este quadro.

**"Posso confiar no que o sistema escreve?"**
O sistema foi desenhado contra os dois maiores riscos de IA jurídica:
(1) julgado inventado — proibido citar jurisprudência "de memória"; toda
citação vem de busca real, verbatim, com processo, relator e data conferíveis;
(2) afirmação sem fonte — o que o sistema diz dos autos aponta documento e
página. Ainda assim, a decisão é SEMPRE do jurista: o sistema é inteligência
aumentada, produz minutas e análises para revisão humana — não substitui o
juízo profissional. Recomendar sempre a leitura crítica do resultado.

**"Quanto tempo demora?"**
Tarefa pontual (pronto): a resposta sai na conversa, em minutos. Fluxo
completo: vários minutos — o sistema anuncia cada etapa em uma linha, e o
usuário pode acompanhar sem abrir arquivo nenhum.

**"Onde foi parar o que o sistema produziu?"**
Na pasta do caso, um arquivo por etapa, nomeados pelo número do processo
(ex.: `<numero>-analise.md`, `<numero>-sentenca.md`). O resumo final lista
cada arquivo com o caminho.

**"Por que o sistema me fez uma pergunta no meio do trabalho?"**
Algumas etapas têm escolhas que pertencem ao usuário (escopo da pesquisa,
qual decisão embargar, ênfase estratégica). O sistema pergunta UMA vez, com
as opções e o padrão declarados; sem resposta, segue no padrão e registra.

**"O sistema se recusou a fazer o que pedi. Por quê?"**
As recusas são proteções deliberadas: não cita julgado que a busca não
confirmou, não redige embargos que a própria análise reprovou, não inventa
dado que não está nos autos. A recusa vem sempre com a explicação e, quando
existe, com a alternativa.

**"Preciso saber programar?"**
Não. Basta descrever a necessidade em português ("minute esta sentença",
"cabem embargos aqui?", "como os TRFs decidem sobre X?"). O concierge existe
exatamente para traduzir a necessidade em rota.

## Solução de problemas

**O serviço não responde / "conector não encontrado".**
Verificar: Configurações → Conectores → "SuperJurista" habilitado para a
sessão. Se estiver habilitado e mesmo assim as ferramentas não aparecerem,
é uma falha conhecida de plataforma — sugerir testar no claude.ai e avisar
o suporte. Não improvisar a tarefa sem o serviço.

**"Assinatura inativa".**
O corpo do sistema é gratuito; a inteligência (modelos, fluxos, buscas) exige
assinatura ativa no serviço SuperJurista. Orientar a regularizar pelo canal de
assinatura e retomar depois — nada é executado sem ela.

**O PDF é escaneado e o texto saiu incompleto.**
A skill `preparar-autos` detecta páginas escaneadas e as trata (OCR local ou
transcrição assistida, com cada página marcada). Se alguma página constar como
"TRANSCREVER" pendente, o preparo não terminou — concluir antes de rodar
qualquer fluxo, ou a análise enxergará um processo pela metade.

**Uma etapa foi reprovada duas vezes na conferência.**
O sistema para por honestidade em vez de entregar peça defeituosa. O aviso
diz qual arquivo e qual o motivo. Caminhos: dar a instrução que faltava
(muitas reprovações vêm de informação ausente nos autos) e pedir para rodar
de novo — a retomada preserva as etapas válidas.

**Fechei tudo no meio do trabalho.**
Nada se perde: reabrir a conversa (ou uma nova) na mesma pasta do caso e
pedir para continuar — o sistema confere o que já está válido e segue da
etapa pendente.
